#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验构建产物。

检查项：
  * yaml 能被 YAML 解析器正确读出 payload（避免线上表现为
    「provider 加载了但规则数为 0」这类静默失效）
  * payload 每条符合规则语法
  * yaml 与 list 源文件条数一致
  * list 的 header 完整：NAME 与文件名一致、UPDATED 为合法日期、
    TOTAL 与各类型统计均与实际相符
"""
import os, re, sys, datetime, collections

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
    if not os.path.exists(lp):
        bad.append('%s: 没有对应的 list 源文件' % name)
        continue

    src = open(lp, encoding='utf-8').read()
    rules = [l.strip() for l in src.split('\n') if RULE_RE.match(l.strip())]
    if len(rules) != len(payload):
        bad.append('%s: 条数不符 —— yaml %d 条，list %d 条' % (name, len(payload), len(rules)))

    # header 三项完整性：NAME 与文件名一致、UPDATED 为合法日期、统计与实际相符
    m = re.search(r'^#\s*NAME:\s*(\S+)', src, re.M)
    if not m:
        bad.append('%s: 缺少 # NAME' % name)
    elif m.group(1) != name:
        bad.append('%s: NAME 与文件名不符 —— %s' % (name, m.group(1)))

    m = re.search(r'^#\s*UPDATED:\s*(\S+)', src, re.M)
    if not m:
        bad.append('%s: 缺少 # UPDATED' % name)
    else:
        try:
            datetime.date.fromisoformat(m.group(1))
        except ValueError:
            bad.append('%s: UPDATED 不是合法日期 —— %s' % (name, m.group(1)))

    m = re.search(r'^#\s*TOTAL:\s*(\d+)', src, re.M)
    if not m:
        bad.append('%s: 缺少 # TOTAL' % name)
    elif int(m.group(1)) != len(rules):
        bad.append('%s: TOTAL 与实际不符 —— 标注 %s，实际 %d'
                   % (name, m.group(1), len(rules)))

    cnt = collections.Counter(RULE_RE.match(r).group(1) for r in rules)
    for t, n in cnt.items():
        hm = re.search(r'^#\s*%s:\s*(\d+)' % re.escape(t), src, re.M)
        if not hm:
            bad.append('%s: header 缺少 %s 统计' % (name, t))
        elif int(hm.group(1)) != n:
            bad.append('%s: %s 统计不符 —— 标注 %s，实际 %d' % (name, t, hm.group(1), n))

print('yaml 文件 : %d 个（其中空规则集 %d 个）'
      % (len([f for f in os.listdir(YAML) if f.endswith('.yaml')]), empty))
print('规则总数  : %d 条' % total)

if bad:
    print('\n发现 %d 个问题：' % len(bad))
    for b in bad:
        print('  ' + b)
    sys.exit(1)
print('校验通过')
