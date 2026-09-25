#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则冗余分析：找出在实际规则链上永远不会被命中的条目。

原理：单个 .list 文件内部无法判断一条规则是否冗余 —— 冗余是由**整条规则链的
顺序**决定的。所以本脚本读取 Openclash-Config 的产物 ini 还原规则顺序，
再按内核「从上到下、命中即止」的语义做首命中模拟。

三类结果：
  A 同组冗余   被更早的规则命中，且目标分组相同 -> 删了行为完全不变，可安全停用
  B 文件内重复 同一文件里被自己更宽的规则包含   -> 同上
  C 异组冲突   被更早的规则命中，但目标分组不同 -> 行为会变，**只报告不处理**
  D IP 覆盖    IP-CIDR 被链上更早的段完整包含（分异组 / 同组）-> **只报告不处理**

局限：GEOSITE / GEOIP 行不展开（路由器实际使用的 geodata 版本不确定，
按 v2fly 展开的结论可能与真实行为不符），模拟时视为不存在。

--apply 只处理 A 和 B，且遵循本仓库既有约定：**注释停用而非删除**，
前缀 `# [已停用-冗余]`，随时可恢复。C 类永远需要人工判断。

用法：
    python3 scripts/dedupe.py                    # 只出报告
    python3 scripts/dedupe.py --apply            # 停用 A/B 两类
    python3 scripts/dedupe.py --ini <路径或URL>  # 指定规则链来源
"""
import os, re, sys, argparse, ipaddress, urllib.request
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, 'rules', 'list')
YAML = os.path.join(ROOT, 'rules', 'yaml')
DEFAULT_INI = ('https://raw.githubusercontent.com/MAXLYEN/Openclash-Config/'
               'main/dist/Custom_Clash_V2.ini')
MARK = '# [已停用-冗余] '


def load_ini(src):
    if src.startswith('http'):
        req = urllib.request.Request(src, headers={'User-Agent': 'dedupe/1.0'})
        text = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    else:
        text = open(src, encoding='utf-8').read()
    chain = []
    for line in text.split('\n'):
        line = line.strip()
        if not line.startswith('ruleset=') or 'clash-classic:' not in line:
            continue
        grp, rest = line[len('ruleset='):].split(',', 1)
        fn = rest.split('clash-classic:', 1)[1].rsplit(',', 1)[0].rsplit('/', 1)[-1]
        chain.append((grp.strip(), fn[:-5] if fn.endswith('.yaml') else fn))
    return chain


def read_list(name):
    """返回 [(行号, 类型, 值, 原始行, 是否已被本脚本停用)]

    关键：被本脚本停用的行（MARK 前缀）也要读回来重新判定。
    冗余与否取决于 ini 的规则顺序，而 ini 会独立演进 —— 某条规则今天冗余，
    改了顺序之后可能就不冗余了。只停用不恢复会变成单向棘轮，
    时间一长就会有规则被错误地长期禁用。
    其他 # 开头的行（人工注释、header）一律不碰。
    因此人工停用必须用 `# [已停用]` 等其他标记，不能借用 MARK，否则会被自动恢复。"""
    p = os.path.join(LIST, name + '.list')
    if not os.path.exists(p):
        return None
    out = []
    for i, raw in enumerate(open(p, encoding='utf-8', errors='replace')):
        line = raw.rstrip('\n')
        t = line.strip()
        was_off = False
        if t.startswith(MARK):
            # 原因分隔符按「←」切，不依赖前面的空格数；否则恢复时会把原因一起写回规则行
            t = t[len(MARK):].split('←')[0].strip()
            was_off = True
        elif t.startswith('#') or not t:
            continue
        parts = t.split(',')
        if len(parts) < 2:
            continue
        out.append((i, parts[0].strip(), parts[1].strip().lower(), t, was_off))
    return out


def analyse(chain):
    suffix, exact, keyword = {}, {}, []
    redundant = defaultdict(list)   # 需停用：当前生效但冗余
    restore = defaultdict(list)     # 需恢复：已停用但不再冗余
    keep_off = 0                    # 已停用且仍冗余，无需改动
    conflict = []
    missing = []
    for grp, name in chain:
        rows = read_list(name)
        if rows is None:
            missing.append(name)
            continue
        for lineno, typ, val, raw, was_off in rows:
            hit = None
            # 覆盖关系只能由「更宽」的规则成立：
            #   DOMAIN        <- 同名 DOMAIN / 祖先 SUFFIX / 子串 KEYWORD
            #   DOMAIN-SUFFIX <- 祖先 SUFFIX / 子串 KEYWORD（同名 DOMAIN 盖不住子域）
            #   DOMAIN-KEYWORD <- 子串 KEYWORD（任何 SUFFIX 都盖不住「包含即命中」）
            if typ in ('DOMAIN', 'DOMAIN-SUFFIX'):
                if typ == 'DOMAIN' and val in exact:
                    hit = exact[val]
                if not hit:
                    parts = val.split('.')
                    for i in range(len(parts)):
                        s = '.'.join(parts[i:])
                        if s in suffix:
                            hit = suffix[s]
                            break
                if not hit:
                    for kw, g, f in keyword:
                        if kw in val:
                            hit = (g, f, kw)
                            break
            elif typ == 'DOMAIN-KEYWORD':
                for kw, g, f in keyword:
                    if kw in val:
                        hit = (g, f, kw)
                        break
            is_red = False
            why = ''
            if hit:
                hg, hf = hit[0], hit[1]
                if hf == name:
                    is_red, why = True, '文件内被 %s 包含' % hf
                elif hg == grp:
                    is_red, why = True, '已被 %s 以同一分组命中' % hf
                else:
                    conflict.append((name, grp, val, hf, hg))
            if is_red and not was_off:
                redundant[name].append((lineno, raw, why))
            elif is_red and was_off:
                keep_off += 1
            elif not is_red and was_off:
                restore[name].append((lineno, raw, ''))
            # 已停用的行不进索引：它在内核眼里不存在，不能用来遮蔽后面的规则
            if was_off:
                continue
            if typ == 'DOMAIN-SUFFIX':
                suffix.setdefault(val, (grp, name))
            elif typ == 'DOMAIN':
                exact.setdefault(val, (grp, name))
            else:
                keyword.append((val, grp, name))
    return redundant, restore, keep_off, conflict, missing


def analyse_ip(chain):
    """IP 规则的首命中模拟，**只报告**。

    一条 IP-CIDR 被链上更早的某个段完整包含时，它永远不会被命中。
    与域名部分不同，这里不做 --apply：链上夹着 GEOIP 行（本脚本看不到），
    且大量重叠来自官方段之间（Netflix_IP 与 GlobalMedia_IP 互为副本、
    Apple 17.0.0.0/8 覆盖 China_IP 里的 Apple 中国机房等），是否处理需要人工判断。

    首命中取「链上位置最早」的包含段，而不是最宽的那个 —— 内核按顺序匹配。
    查找按前缀长度逐级取上级网段查表，每条最多 32（v6 为已出现的前缀种类数）次，
    避免两两比较。只处理完整包含；部分重叠（后者更宽）不算遮蔽。

    返回 (cross, same)，元素为 (后者文件, 后者分组, 后者段, 前者文件, 前者分组, 前者段)。"""
    seen = {}                     # (版本, 前缀长度, 网络号) -> (链上序号, 分组, 文件, 段)
    lens = {4: set(), 6: set()}
    cross, same = [], []
    pos = 0
    for grp, name in chain:
        for lineno, typ, val, raw, was_off in (read_list(name) or []):
            if was_off or typ not in ('IP-CIDR', 'IP-CIDR6'):
                continue
            try:
                net = ipaddress.ip_network(val, strict=False)
            except ValueError:
                continue
            pos += 1
            hit = None
            for p in lens[net.version]:
                if p > net.prefixlen:
                    continue
                sup = net.supernet(new_prefix=p)
                h = seen.get((net.version, p, int(sup.network_address)))
                if h and (hit is None or h[0] < hit[0]):
                    hit = h
            if hit:
                (same if hit[1] == grp else cross).append(
                    (name, grp, str(net), hit[2], hit[1], hit[3]))
            seen.setdefault((net.version, net.prefixlen, int(net.network_address)),
                            (pos, grp, name, str(net)))
            lens[net.version].add(net.prefixlen)
    return cross, same


def apply_changes(redundant, restore):
    files = set(redundant) | set(restore)
    for name in files:
        p = os.path.join(LIST, name + '.list')
        lines = open(p, encoding='utf-8').read().split('\n')
        for lineno, raw, why in redundant.get(name, []):
            lines[lineno] = MARK + raw + '  ← ' + why
        for lineno, raw, _ in restore.get(name, []):
            lines[lineno] = raw          # 去掉 MARK 与原因，恢复原样
        open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    return len(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ini', default=DEFAULT_INI, help='规则链来源：本地路径或 URL')
    ap.add_argument('--apply', action='store_true', help='把 A/B 两类注释停用（C 类不动）')
    a = ap.parse_args()

    chain = load_ini(a.ini)
    print('规则链来源 : %s' % a.ini)
    print('引用规则集 : %d 个\n' % len(chain))

    redundant, restore, keep_off, conflict, missing = analyse(chain)
    if missing:
        print('⚠ ini 引用但 rules/list 里不存在：%s\n' % ', '.join(missing))

    total = sum(len(v) for v in redundant.values())
    n_res = sum(len(v) for v in restore.values())
    print('【已停用且仍冗余】%d 条，无需改动' % keep_off)
    if n_res:
        print('【需恢复】%d 条：之前被停用，但按当前规则顺序已不再冗余' % n_res)
        for name, items in sorted(restore.items(), key=lambda x: -len(x[1])):
            print('   %5d  %s' % (len(items), name))
    print('【A+B 可安全停用】共 %d 条，分布在 %d 个文件' % (total, len(redundant)))
    for name, items in sorted(redundant.items(), key=lambda x: -len(x[1]))[:15]:
        print('   %5d  %s' % (len(items), name))
    if len(redundant) > 15:
        print('   ...（其余 %d 个文件）' % (len(redundant) - 15))

    print('\n【C 异组冲突】共 %d 条，需人工判断，本脚本不处理' % len(conflict))
    c = Counter((x[0], x[3]) for x in conflict)
    for (later, earlier), n in c.most_common(10):
        print('   %5d  %-30s 被 %s 提前命中' % (n, later, earlier))

    # IP 部分只报告；IP 规则均为 no-resolve，只影响按 IP 直连的流量（游戏对战、语音、P2P 等）
    ip_cross, ip_same = analyse_ip(chain)
    print('\n【D IP 异组覆盖】共 %d 条：被链上更早的其他分组 IP 段完整包含，需人工判断'
          % len(ip_cross))
    c = Counter((x[0], x[3]) for x in ip_cross)
    for (later, earlier), n in c.most_common(10):
        ex = next(x for x in ip_cross if x[0] == later and x[3] == earlier)
        print('   %5d  %-24s 被 %-18s 覆盖  例 %s ⊂ %s' % (n, later, earlier, ex[2], ex[5]))
    wide = Counter('%s %s' % (x[3], x[5]) for x in ip_cross)
    if wide:
        print('   遮蔽最多的段：%s' % '、'.join('%s（%d 条）' % kv for kv in wide.most_common(5)))
    print('【D IP 同组覆盖】共 %d 条：后者永不命中、删了行为不变；IP 规则不自动停用'
          % len(ip_same))
    for (later, earlier), n in Counter((x[0], x[3]) for x in ip_same).most_common(5):
        print('   %5d  %-24s 被 %s 覆盖' % (n, later, earlier))

    if a.apply:
        if not total and not n_res:
            print('\n无需改动。')
            return
        # 一轮改动会改变后续判定：恢复一条规则后，它会重新遮蔽链上更靠后的同名规则。
        # 反复分析直到不动点，保证单次 --apply 之后再跑只读模式结果为零。
        files, rounds = set(), 0
        while (total or n_res) and rounds < 10:
            files |= set(redundant) | set(restore)
            apply_changes(redundant, restore)
            rounds += 1
            redundant, restore = analyse(chain)[:2]
            total = sum(len(v) for v in redundant.values())
            n_res = sum(len(v) for v in restore.values())
        if total or n_res:
            print('\n⚠ %d 轮后仍未收敛，剩余停用 %d 条、恢复 %d 条' % (rounds, total, n_res))
        print('\n改动 %d 个文件（%d 轮收敛）。' % (len(files), rounds))
        print('接下来跑 scripts/build.py 重新生成 yaml，再跑 scripts/validate.py 校验。')
    else:
        print('\n（只读模式。加 --apply 执行停用/恢复）')


if __name__ == '__main__':
    main()
