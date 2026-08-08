#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则构建：rules/list/  ->  rules/yaml/

  rules/list/   手动维护，唯一数据源（classical 格式，每行一条）
  rules/yaml/   自动生成，供 ini 以 clash-classic: 引用

除生成 yaml 外，本脚本还会就地规范化 list 源文件，自动修复：

  * CRLF 换行             -> LF        （\\r 会并入域名，导致规则永不命中）
  * 逗号后多余空格         -> 去除      （空格会进入匹配串）
  * IP 规则缺 no-resolve   -> 补齐      （否则触发 DNS 解析，拖慢并有泄漏风险）
  * DOMAIN-KEYWORD 含大写  -> 转小写    （域名匹配为小写，大写永不命中）
  * 文件内重复规则         -> 去重
  * header 统计与实际不符   -> 重算
  * 规则有变动的文件        -> 更新 UPDATED 日期

并检查以下问题，仅告警不阻断构建：

  * DOMAIN-KEYWORD 含 ? = / 或空格（URL 片段，恒不命中）
  * PROCESS-NAME（网关转发场景取不到进程名，恒不生效）
  * _Domain 混入 IP 规则 / _IP 混入域名规则
  * 文件名不符合 平台_Domain / 平台_IP 规范
  * 平台缺少配对（自动创建占位文件）
"""
import os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, 'rules', 'list')
YAML = os.path.join(ROOT, 'rules', 'yaml')
TODAY = datetime.date.today().isoformat()

RULE_RE = re.compile(r'^([A-Z][A-Z0-9-]*)\s*,\s*(.+)$')
NAME_RE = re.compile(r'^(.+?)_(Domain|IP)(?:_(\d+))?$')
HDR_RE  = re.compile(r'^#\s*(NAME|UPDATED|TOTAL|DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|'
                     r'DOMAIN-REGEX|IP-CIDR|IP-CIDR6|IP-ASN|PROCESS-NAME|DST-PORT|SRC-PORT)\s*:')
DOMAIN_T = ('DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'DOMAIN-REGEX')
IP_T     = ('IP-CIDR', 'IP-CIDR6', 'IP-ASN')
ORDER    = DOMAIN_T + IP_T + ('PROCESS-NAME', 'DST-PORT', 'SRC-PORT')

warnings = []


def warn(name, msg):
    warnings.append((name, msg))


def parse(path, name):
    """读取并规范化。返回保序序列 [('c', 注释) | ('r', 类型, 值)]，
    注释与其下方规则的相邻关系必须保持不变 —— 分节注释一旦被挪走，
    文件就再也说不清哪条规则属于哪一节。"""
    raw = open(path, 'rb').read()
    if b'\r' in raw:
        warn(name, 'CRLF 换行已转为 LF')

    seq, seen = [], set()
    text = raw.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            if not HDR_RE.match(line):        # 旧 header 丢弃，说明性注释原位保留
                seq.append(('c', line))
            continue
        m = RULE_RE.match(line)
        if not m:
            warn(name, '无法解析，已转为注释：%s' % line[:60])
            seq.append(('c', '# ' + line))
            continue
        t, v = m.group(1).upper(), m.group(2).strip()

        if t in ('IP-CIDR', 'IP-CIDR6') and 'no-resolve' not in v:
            v += ',no-resolve'
            warn(name, '已补 no-resolve：%s' % v)
        if t == 'DOMAIN-KEYWORD':
            if re.search(r'[?=/\s]', v):
                warn(name, 'DOMAIN-KEYWORD 含 URL 片段字符，恒不命中：%s' % v)
            if v != v.lower():
                v = v.lower()
                warn(name, 'DOMAIN-KEYWORD 已转小写：%s' % v)
        if t == 'PROCESS-NAME':
            warn(name, 'PROCESS-NAME 在网关转发场景下不生效：%s' % v)

        key = '%s,%s' % (t, v.split(',no-resolve')[0])
        if key in seen:
            warn(name, '重复规则已去除：%s,%s' % (t, v))
            continue
        seen.add(key)
        seq.append(('r', t, v))
    return seq


def build_head(name, seq, updated):
    cnt = {}
    for it in seq:
        if it[0] == 'r':
            cnt[it[1]] = cnt.get(it[1], 0) + 1
    head = ['# NAME: %s' % name, '# UPDATED: %s' % updated]
    head += ['# %s: %d' % (t, cnt[t]) for t in ORDER if cnt.get(t)]
    head.append('# TOTAL: %d' % sum(cnt.values()))
    return head


def write_if_changed(path, content):
    if os.path.exists(path) and open(path, encoding='utf-8').read() == content:
        return False
    open(path, 'w', encoding='utf-8').write(content)
    return True


def main():
    if not os.path.isdir(LIST):
        sys.exit('未找到目录：%s' % LIST)
    os.makedirs(YAML, exist_ok=True)          # 已存在则复用，不覆盖

    files = sorted(f for f in os.listdir(LIST) if f.endswith('.list'))
    if not files:
        sys.exit('rules/list/ 下没有 .list 文件')

    # ---------- 成对检查：缺失的一侧自动补占位 ----------
    platforms = {}
    for f in files:
        m = NAME_RE.match(f[:-5])
        if not m:
            warn(f[:-5], '文件名不符合 平台_Domain / 平台_IP 规范')
            continue
        platforms.setdefault(m.group(1), set()).add(m.group(2))
    created = []
    for plat, kinds in sorted(platforms.items()):
        for k in ('Domain', 'IP'):
            if k in kinds:
                continue
            if any(f[:-5].startswith('%s_%s_' % (plat, k)) for f in files):
                continue                      # 分片文件视为已有该类型
            open(os.path.join(LIST, '%s_%s.list' % (plat, k)), 'w', encoding='utf-8').write(
                '# NAME: %s_%s\n# UPDATED: %s\n# TOTAL: 0\n'
                '# 占位文件：本平台暂无%s规则，保留成对结构以便后续补充\n'
                % (plat, k, TODAY, '域名' if k == 'Domain' else ' IP '))
            created.append('%s_%s' % (plat, k))
    if created:
        files = sorted(f for f in os.listdir(LIST) if f.endswith('.list'))

    # ---------- 规范化并生成 yaml ----------
    names, fixed_n, yaml_n, total = [], 0, 0, 0
    rule_changed = []
    for f in files:
        name = f[:-5]
        names.append(name)
        path = os.path.join(LIST, f)

        origin = open(path, encoding='utf-8', errors='replace').read()
        seq = parse(path, name)
        rule_types = [it[1] for it in seq if it[0] == 'r']
        total += len(rule_types)

        m = NAME_RE.match(name)
        if m:
            kind = m.group(2)
            if kind == 'Domain' and any(t in IP_T for t in rule_types):
                warn(name, '_Domain 文件中混入了 IP 规则')
            if kind == 'IP' and any(t in DOMAIN_T for t in rule_types):
                warn(name, '_IP 文件中混入了域名规则')

        # 规则内容有变动才刷新 UPDATED。
        # 基准取上一次的构建产物 yaml/，而非 list 规范化前的状态 —— 后者是本次提交
        # 后的内容，你新增一条格式正确的规则时前后一致，日期就永远不会更新。
        new_rules = ['%s,%s' % (it[1], it[2]) for it in seq if it[0] == 'r']
        prev_yaml = os.path.join(YAML, name + '.yaml')
        last_rules = []
        if os.path.exists(prev_yaml):
            for pl in open(prev_yaml, encoding='utf-8'):
                pm = re.match(r'^\s{2}-\s+(.+?)\s*$', pl)
                if pm:
                    last_rules.append(pm.group(1))
        prev = re.search(r'^#\s*UPDATED:\s*(\S+)', origin, re.M)
        changed = new_rules != last_rules
        updated = TODAY if changed or not prev else prev.group(1)
        if changed:
            rule_changed.append(name)

        head = build_head(name, seq, updated)
        # 保序输出：注释与规则维持原有相邻关系
        body = [it[1] if it[0] == 'c' else '%s,%s' % (it[1], it[2]) for it in seq]
        if write_if_changed(path, '\n'.join(head + body) + '\n'):
            fixed_n += 1

        payload = ('payload:\n' + '\n'.join('  - ' + r for r in new_rules)) if new_rules else 'payload: []'
        notes_only = [it[1] for it in seq if it[0] == 'c']
        if write_if_changed(os.path.join(YAML, name + '.yaml'),
                            '\n'.join(head + notes_only) + '\n' + payload + '\n'):
            yaml_n += 1

    # ---------- 清理 list 中已删除文件的 yaml 产物 ----------
    keep = set(names)
    removed = 0
    for f in os.listdir(YAML):
        if f.endswith('.yaml') and f[:-5] not in keep:
            os.remove(os.path.join(YAML, f))
            removed += 1

    print('规则集      : %d 个' % len(names))
    print('规则总数    : %d 条' % total)
    print('规则有变动  : %d 个' % len(rule_changed))
    print('list 修正   : %d 个' % fixed_n)
    print('yaml 更新   : %d 个' % yaml_n)
    print('新建占位    : %d 个' % len(created))
    print('清理产物    : %d 个' % removed)
    if warnings:
        print('\n告警 %d 条：' % len(warnings))
        for n, msg in warnings[:50]:
            print('  %-26s %s' % (n, msg))
        if len(warnings) > 50:
            print('  ... 另有 %d 条' % (len(warnings) - 50))

    # ---------- GitHub Actions 摘要 ----------
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as fh:
            fh.write('## 规则构建结果\n\n| 项目 | 数量 |\n|---|---|\n')
            fh.write('| 规则集 | %d |\n| 规则总数 | %d |\n' % (len(names), total))
            fh.write('| list 修正 | %d |\n| yaml 更新 | %d |\n' % (fixed_n, yaml_n))
            fh.write('| 新建占位 | %d |\n| 清理产物 | %d |\n' % (len(created), removed))
            if rule_changed:
                fh.write('\n**规则有变动（已刷新 UPDATED）**：%s\n'
                         % '、'.join('`%s`' % c for c in rule_changed))
            if created:
                fh.write('\n**新建占位文件**：%s\n' % '、'.join('`%s`' % c for c in created))
            if warnings:
                fh.write('\n<details><summary>告警 %d 条</summary>\n\n' % len(warnings))
                fh.write('| 规则集 | 说明 |\n|---|---|\n')
                for n, msg in warnings:
                    fh.write('| `%s` | %s |\n' % (n, msg.replace('|', '\\|')))
                fh.write('\n</details>\n')


if __name__ == '__main__':
    main()
