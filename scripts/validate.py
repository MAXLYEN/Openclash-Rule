#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 rules/yaml/ 下的产物能被 YAML 解析器正确读出 payload。

构建后运行，用真正的 YAML 解析器验证一遍，避免格式问题被推到线上后
才在内核里表现为「provider 加载了但规则数为 0」。
"""
import os, re, sys

try:
    import yaml
except ImportError:
    sys.exit('缺少 PyYAML，请先 pip install pyyaml')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML = os.path.join(ROOT, 'rules', 'yaml')
LIST = os.path.join(ROOT, 'rules', 'list')
RULE_RE = re.compile(r'^([A-Z][A-Z0-9-]*),(.+)$')

bad, total, empty = [], 0, 0

for f in sorted(os.listdir(YAML)):
    if not f.endswith('.yaml'):
        continue
    name = f[:-5]
    path = os.path.join(YAML, f)
    try:
        doc = yaml.safe_load(open(path, encoding='utf-8'))
    except Exception as e:
        bad.append('%s: YAML 解析失败 —— %s' % (name, e))
        continue
    if not isinstance(doc, dict) or 'payload' not in doc:
        bad.append('%s: 缺少 payload 键' % name)
        continue
    payload = doc['payload'] or []
    if not isinstance(payload, list):
        bad.append('%s: payload 不是数组' % name)
        continue
    if not payload:
        empty += 1
    total += len(payload)

    for r in payload:
        if not RULE_RE.match(str(r)):
            bad.append('%s: 规则格式异常 —— %s' % (name, r))

    # 与 list 源文件条数比对
    lp = os.path.join(LIST, name + '.list')
    if os.path.exists(lp):
        n = len([l for l in open(lp, encoding='utf-8') if RULE_RE.match(l.strip())])
        if n != len(payload):
            bad.append('%s: 条数不符 —— yaml %d 条，list %d 条' % (name, len(payload), n))
    else:
        bad.append('%s: 没有对应的 list 源文件' % name)

print('yaml 文件 : %d 个（其中空规则集 %d 个）'
      % (len([f for f in os.listdir(YAML) if f.endswith('.yaml')]), empty))
print('规则总数  : %d 条' % total)

if bad:
    print('\n发现 %d 个问题：' % len(bad))
    for b in bad:
        print('  ' + b)
    sys.exit(1)
print('校验通过')
