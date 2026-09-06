#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置校验：检查 cfg/*.ini 的结构完整性。

构建脚本只负责剥注释，真正防事故的是这一步。检查项分两级：
  ERROR   会让配置生成失败或整块规则静默失效 -> 阻断构建
  WARN    可疑但不一定错 -> 只提示

不认识任何具体分组名，纯结构检查，v2/v3/vN 通用。
带 --online 时额外做网络检查（拉取每个 ruleset 产物，验证 payload 结构）。
"""
import os, re, sys, time, argparse, urllib.request, concurrent.futures

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, 'cfg')

BUILTIN = {'DIRECT', 'REJECT', 'REJECT-TINYGIF'}
# Go RE2 不支持的语法；正则编译失败会让分组变空，且没有任何报错
RE2_UNSUPPORTED = (r'(?!', r'(?<!', r'(?<=', r'(?=', r'\1', r'\2')
# 规则源与更新间隔的约定
# 两个端点都是 jsdelivr，只是 CDN 厂商不同（Fastly / Cloudflare），
# 靠端点区分两档更新间隔。注意匹配顺序：fastly 必须先判，
# 否则 'jsdelivr.net' 会把 fastly 地址也一起匹配上。
INTERVAL_CONVENTION = {'fastly.jsdelivr.net': 3600, 'testingcf.jsdelivr.net': 28800}

# 刻意留空的规则集：--online 检查到 payload: [] 时不告警。
#   SelfHosted_Domain —— 自建域名写在路由器本地的 openclash_custom_overwrite.sh，
#                        本文件只为 Self-Hosted 策略组提供挂载点
#   Custom-Made_Domain —— 临时性分流需求的定制区，平时为空
INTENTIONALLY_EMPTY = {'SelfHosted_Domain.yaml', 'Custom-Made_Domain.yaml'}

errors, warns = [], []
# 头部注释里带这个标记的文件，其 ERROR 降级为 WARN，不阻断构建。
# 用途：为兼容旧订阅链接保留、但已不再维护的历史版本配置。
DEPRECATED_MARK = '已停止维护'
deprecated = set()


def err(f, msg):
    if f in deprecated:
        warns.append('%s: %s（该文件已停止维护，降级为告警）' % (f, msg))
    else:
        errors.append('%s: %s' % (f, msg))


def warn(f, msg): warns.append('%s: %s' % (f, msg))


def parse(path):
    groups, order = {}, []          # name -> [candidate, ...]
    rulesets = []                   # (group, payload, lineno)
    settings = {}
    section = None
    for i, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.strip()
        if not line or line.startswith((';', '#', '//')):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        if '=' not in line:
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        if key == 'ruleset':
            g, _, payload = val.partition(',')
            rulesets.append((g.strip(), payload.strip(), i))
        elif key == 'custom_proxy_group':
            parts = val.split('`')
            name = parts[0].strip()
            if name in groups:
                err(os.path.basename(path), '第 %d 行 策略组重名：%s' % (i, name))
            groups[name] = parts[1:]
            order.append(name)
        else:
            settings[key] = val.strip()
    return groups, order, rulesets, settings, section


def check(path):
    f = os.path.basename(path)
    head = ''.join(open(path, encoding='utf-8').readlines()[:10])
    if DEPRECATED_MARK in head:
        deprecated.add(f)
    groups, order, rulesets, settings, last_section = parse(path)
    defined = set(groups)

    # 1. 必备开关
    for k, want in (('enable_rule_generator', 'true'), ('overwrite_original_rules', 'true')):
        if settings.get(k) != want:
            warn(f, '%s 不是 %s（当前 %r）' % (k, want, settings.get(k)))

    # 2. ruleset 指向的分组必须已定义
    for g, payload, i in rulesets:
        if g not in defined and g not in BUILTIN:
            err(f, '第 %d 行 ruleset 指向未定义的分组：%s' % (i, g))

    # 3. 候选引用必须已定义
    for name, cands in groups.items():
        for c in cands:
            if not c.startswith('[]'):
                continue                       # 正则筛选，不校验
            ref = c[2:].strip()
            if ref not in defined and ref not in BUILTIN:
                err(f, '分组 %s 的候选引用了未定义的目标：%s' % (name, ref))

    # 4. 循环引用 —— Clash 加载时会直接失败
    graph = {n: [c[2:].strip() for c in cs if c.startswith('[]')] for n, cs in groups.items()}
    state = {}
    def dfs(n, stack):
        if state.get(n) == 2: return
        if state.get(n) == 1:
            err(f, '策略组循环引用：%s' % ' -> '.join(stack[stack.index(n):] + [n]))
            return
        state[n] = 1
        for m in graph.get(n, []):
            if m in graph: dfs(m, stack + [n])
        state[n] = 2
    for n in graph: dfs(n, [])

    # 5. 定义了却没有任何规则指向的分组（节点池与 Auto-Test 类除外：它们靠候选引用）
    used_by_rule = {g for g, _, _ in rulesets}
    used_by_cand = {c[2:].strip() for cs in groups.values() for c in cs if c.startswith('[]')}
    for n in order:
        if n not in used_by_rule and n not in used_by_cand:
            warn(f, '分组 %s 既无规则指向也无人引用，是死分组' % n)

    # 6. FINAL 兜底
    finals = [i for g, p, i in rulesets if p.upper() in ('[]FINAL', '[]MATCH')]
    if len(finals) != 1:
        err(f, '[]FINAL 兜底应恰好一条，实际 %d 条' % len(finals))
    elif finals[0] != max(i for _, _, i in rulesets):
        err(f, '[]FINAL 不在 ruleset 段最后（第 %d 行）' % finals[0])

    # 7. url-test 组的正则
    for name, cands in groups.items():
        if not cands or cands[0] not in ('url-test', 'fallback', 'load-balance'):
            continue
        pat = cands[1] if len(cands) > 1 else ''
        for bad in RE2_UNSUPPORTED:
            if bad in pat:
                err(f, '分组 %s 的正则含 Go RE2 不支持的语法 %s，会导致分组为空且无报错' % (name, bad))
        try:
            re.compile(pat)
        except re.error as e:
            err(f, '分组 %s 的正则无法编译：%s' % (name, e))

    # 8. 规则源与更新间隔的约定
    for g, payload, i in rulesets:
        if not payload.startswith('clash-classic:'):
            continue
        m = re.search(r',(\d+)\s*$', payload)
        if not m:
            warn(f, '第 %d 行 ruleset 未带更新间隔，会被内联展开而非生成 provider' % i)
            continue
        interval = int(m.group(1))
        for host, want in INTERVAL_CONVENTION.items():
            if host in payload and interval != want:
                warn(f, '第 %d 行 %s 源的间隔是 %d，约定为 %d' % (i, host, interval, want))

    # 8b. 禁止 raw.githubusercontent.com
    # OpenClash 的「Github 加速地址」会把它改写成
    # fastly.jsdelivr.net/gh/...@refs/heads/main，与 CI purge 用的 @main
    # 不是同一个缓存键，purge 会长期失效（源码 yml_rules_change.sh:295）
    for g, payload, i in rulesets:
        if 'raw.githubusercontent.com' in payload:
            err(f, '第 %d 行使用了 raw.githubusercontent.com，会被 OpenClash 改写成 '
                   '@refs/heads/main 而使 CI 的 purge 失效。请改写为 '
                   'https://fastly.jsdelivr.net/gh/<用户>/<仓库>@main/...' % i)

    # 9. 单候选分组：可行但会静默降级（子转换器在节点池为空时插入 DIRECT）
    for name, cands in groups.items():
        if cands and cands[0] == 'select' and len(cands) == 2 \
           and cands[1].lstrip('[]').strip() not in BUILTIN:
            warn(f, '分组 %s 只有一个候选：节点匹配不到时会静默降级为直连，且面板上无法手动救急' % name)

    return len(rulesets), len(groups)


def check_online(path):
    """拉取每个 provider 产物，确认是 payload: 结构。
    历史事故：166 个 provider 引用的是纯文本 .list，加载成功但规则数为 0，
    流量全部落到 GeoSite 兜底，因为兜底大多也能导向正确分组，问题被长期掩盖。"""
    f = os.path.basename(path)
    urls = []
    for raw in open(path, encoding='utf-8'):
        line = raw.strip()
        if not line.startswith('ruleset=') or 'clash-classic:' not in line:
            continue
        u = line.split('clash-classic:', 1)[1].rsplit(',', 1)[0]
        urls.append(u)

    def fetch(u):
        # 用浏览器 UA：部分 CDN（jsdelivr 走 Cloudflare）对陌生 UA 会返回
        # 挑战页而不是文件，状态码仍是 200，正文里自然没有 payload:
        req = urllib.request.Request(u, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; openclash-config-validator/1.1)',
            'Accept': 'text/plain,*/*',
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read(8192).decode('utf-8', 'replace')

    def probe(u):
        last = None
        for attempt in range(3):          # CDN 偶发抖动重试两次，避免误报
            try:
                status, ctype, head = fetch(u)
            except Exception as e:
                last = '拉取失败：%s' % e
                time.sleep(1.5 * (attempt + 1))
                continue
            if 'payload:' in head:
                if re.search(r'payload:\s*\[\s*\]', head):
                    # 2026-09-06 起 rules/yaml 改为零注释产物，无法再从内容里读出
                    # "占位"标记，改用显式白名单。新增刻意留空的规则集时在此登记，
                    # 并在对应 .list 的 header 里写清原因。
                    if u.rsplit('/', 1)[-1] in INTENTIONALLY_EMPTY:
                        return u, None, None
                    return u, 'WARN', 'payload 为空，且不在 INTENTIONALLY_EMPTY 白名单中'
                return u, None, None
            # 拿到了内容但没有 payload:，把实到的东西一并报出来，否则无法判断
            # 是文件真错了，还是 CDN 返回了别的东西
            snippet = head[:80].replace('\n', ' ⏎ ').strip()
            last = ('不是 classical provider 结构（缺 payload:），provider 会加载为 0 条规则。'
                    'HTTP %s / Content-Type: %s / 正文开头: %r' % (status, ctype or '(无)', snippet))
            time.sleep(1.5 * (attempt + 1))
        return u, 'ERROR', last

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for u, level, msg in ex.map(probe, sorted(set(urls))):
            if level == 'ERROR': err(f, '%s -> %s' % (u.rsplit('/', 1)[-1], msg))
            elif level == 'WARN': warn(f, '%s -> %s' % (u.rsplit('/', 1)[-1], msg))


def check_dist_sync():
    """检查 dist/ 是否与 cfg/ 同步。用与 build_ini.py 相同的剥离规则重算后比对。

    仅在 --check-dist 时运行，**不进 CI 默认流程**。
    原因：workflow 的步骤顺序是「校验 → 构建」。改了 cfg/ 之后 dist/ 本来就是旧的，
    等着被构建重新生成；若默认执行本检查，校验会在构建之前把 job 掐断，
    dist/ 永远没机会更新 —— 任何一次正常的 cfg 修改都会让 CI 红掉。

    它的用途是本地预提交自查：手改过 dist/、或改完 cfg/ 忘了跑构建就想提交时，
    先跑 `validate_ini.py --check-dist` 能立刻发现。"""
    DIST = os.path.join(ROOT, 'dist')
    if not os.path.isdir(DIST):
        warn('dist', 'dist/ 目录不存在，尚未构建')
        return
    for n in sorted(f for f in os.listdir(SRC) if f.endswith('.ini')):
        dist_path = os.path.join(DIST, n)
        if not os.path.exists(dist_path):
            err('dist/' + n, '产物缺失，需要运行 scripts/build_ini.py')
            continue
        raw = open(os.path.join(SRC, n), 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
        expect = [l.rstrip() for l in text.split('\n')]
        expect = [l for l in expect if l and not l.strip().startswith((';', '#', '//'))]
        actual = open(dist_path, encoding='utf-8').read().split('\n')
        actual = [l for l in actual if l]
        if expect != actual:
            d = next((i for i, (a, b) in enumerate(zip(expect, actual)) if a != b), min(len(expect), len(actual)))
            err('dist/' + n, '与 cfg/%s 不同步（第 %d 行起有差异）。'
                             '不要手改 dist/，运行 scripts/build_ini.py 重新生成' % (n, d + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true', help='额外拉取所有 provider 校验 payload 结构')
    ap.add_argument('--check-dist', action='store_true',
                    help='检查 dist/ 是否与 cfg/ 同步。本地提交前自查用；'
                         'CI 里不要开，因为构建步骤排在校验之后')
    a = ap.parse_args()

    names = sorted(f for f in os.listdir(SRC) if f.endswith('.ini'))
    for n in names:
        p = os.path.join(SRC, n)
        nr, ng = check(p)
        if a.online:
            check_online(p)
        print('%-32s %3d ruleset / %3d group' % (n, nr, ng))

    if a.check_dist:
        check_dist_sync()

    if warns:
        print('\n告警 %d 条：' % len(warns))
        for w in warns: print('  ⚠ ' + w)
    if errors:
        print('\n错误 %d 条：' % len(errors))
        for e in errors: print('  ✗ ' + e)
        sys.exit(1)
    print('\n校验通过')


if __name__ == '__main__':
    main()
