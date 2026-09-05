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

--apply 只处理 A 和 B，且遵循本仓库既有约定：**注释停用而非删除**，
前缀 `# [已停用-冗余]`，随时可恢复。C 类永远需要人工判断。

用法：
    python3 scripts/dedupe.py                    # 只出报告
    python3 scripts/dedupe.py --apply            # 停用 A/B 两类
    python3 scripts/dedupe.py --ini <路径或URL>  # 指定规则链来源
"""
import os, re, sys, argparse, urllib.request
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
    """返回 [(行号, 类型, 值, 原始行)]，只含生效规则行"""
    p = os.path.join(LIST, name + '.list')
    if not os.path.exists(p):
        return None
    out = []
    for i, raw in enumerate(open(p, encoding='utf-8', errors='replace')):
        s = raw.rstrip('\n')
        t = s.strip()
        if not t or t.startswith('#'):
            continue
        parts = t.split(',')
        if len(parts) < 2:
            continue
        out.append((i, parts[0].strip(), parts[1].strip().lower(), s))
    return out


def analyse(chain):
    suffix, exact, keyword = {}, {}, []
    redundant = defaultdict(list)   # name -> [(lineno, raw, 原因)]
    conflict = []
    missing = []
    for grp, name in chain:
        rows = read_list(name)
        if rows is None:
            missing.append(name)
            continue
        for lineno, typ, val, raw in rows:
            hit = None
            if typ in ('DOMAIN', 'DOMAIN-SUFFIX'):
                if val in exact:
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
                if val in suffix:
                    hit = suffix[val]
                if not hit:
                    for kw, g, f in keyword:
                        if kw in val:
                            hit = (g, f, kw)
                            break
            if hit:
                hg, hf = hit[0], hit[1]
                if hf == name:
                    redundant[name].append((lineno, raw, '文件内被 %s 包含' % hf))
                elif hg == grp:
                    redundant[name].append((lineno, raw, '已被 %s 以同一分组命中' % hf))
                else:
                    conflict.append((name, grp, val, hf, hg))
            if typ == 'DOMAIN-SUFFIX':
                suffix.setdefault(val, (grp, name))
            elif typ == 'DOMAIN':
                exact.setdefault(val, (grp, name))
            else:
                keyword.append((val, grp, name))
    return redundant, conflict, missing


def apply_changes(redundant):
    changed = 0
    for name, items in redundant.items():
        p = os.path.join(LIST, name + '.list')
        lines = open(p, encoding='utf-8').read().split('\n')
        for lineno, raw, why in items:
            if lines[lineno].startswith('#'):
                continue
            lines[lineno] = MARK + lines[lineno].strip() + '  ← ' + why
        open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ini', default=DEFAULT_INI, help='规则链来源：本地路径或 URL')
    ap.add_argument('--apply', action='store_true', help='把 A/B 两类注释停用（C 类不动）')
    a = ap.parse_args()

    chain = load_ini(a.ini)
    print('规则链来源 : %s' % a.ini)
    print('引用规则集 : %d 个\n' % len(chain))

    redundant, conflict, missing = analyse(chain)
    if missing:
        print('⚠ ini 引用但 rules/list 里不存在：%s\n' % ', '.join(missing))

    total = sum(len(v) for v in redundant.values())
    print('【A+B 可安全停用】共 %d 条，分布在 %d 个文件' % (total, len(redundant)))
    for name, items in sorted(redundant.items(), key=lambda x: -len(x[1]))[:15]:
        print('   %5d  %s' % (len(items), name))
    if len(redundant) > 15:
        print('   ...（其余 %d 个文件）' % (len(redundant) - 15))

    print('\n【C 异组冲突】共 %d 条，需人工判断，本脚本不处理' % len(conflict))
    c = Counter((x[0], x[3]) for x in conflict)
    for (later, earlier), n in c.most_common(10):
        print('   %5d  %-30s 被 %s 提前命中' % (n, later, earlier))

    if a.apply:
        n = apply_changes(redundant)
        print('\n已在 %d 个文件里注释停用 %d 条。' % (n, total))
        print('接下来跑 scripts/build.py 重新生成 yaml，再跑 scripts/validate.py 校验。')
    else:
        print('\n（只读模式。加 --apply 执行停用）')


if __name__ == '__main__':
    main()
