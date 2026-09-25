#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验构建产物。

检查项：
  * yaml 能被 YAML 解析器正确读出 payload（避免线上表现为
    「provider 加载了但规则数为 0」这类静默失效）
  * payload 每条符合规则语法，规则类型在 mihomo 支持的范围内（拼错的类型
    如 DOMAIN-SUFIX 会被 classical provider 记一条警告后跳过，规则静默失效）
  * IP 规则：CIDR 可解析、ASN 为数字、带 no-resolve（缺了会触发 DNS 解析）。
    主机位与地址族不符不算错误——内核按掩码截断，IP-CIDR / IP-CIDR6 两种写法
    都能解析任一地址族，规则仍然生效——由 build.py 告警
  * yaml 与 list 源文件逐条一致（内容与顺序）
  * list 的 header 完整：NAME 与文件名一致、UPDATED 为合法日期、
    TOTAL 与各类型统计均与实际相符
"""
import os, re, sys, datetime, collections, ipaddress

try:
    import yaml
except ImportError:
    sys.exit('缺少 PyYAML，请先 pip install pyyaml')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML = os.path.join(ROOT, 'rules', 'yaml')
LIST = os.path.join(ROOT, 'rules', 'list')
RULE_RE = re.compile(r'^([A-Z][A-Z0-9-]*),(.+)$')
# mihomo 规则集里可用的类型。本库实际只用 DOMAIN / DOMAIN-SUFFIX / DOMAIN-KEYWORD /
# IP-CIDR / IP-CIDR6 / IP-ASN，其余列出是为了不误报合法写法，只拦拼写错误
TYPES = {
    'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'DOMAIN-REGEX', 'DOMAIN-WILDCARD',
    'GEOSITE', 'GEOIP', 'IP-CIDR', 'IP-CIDR6', 'IP-SUFFIX', 'IP-ASN',
    'SRC-GEOIP', 'SRC-IP-ASN', 'SRC-IP-CIDR', 'SRC-IP-SUFFIX',
    'DST-PORT', 'SRC-PORT', 'IN-PORT', 'IN-TYPE', 'IN-USER', 'IN-NAME',
    'PROCESS-NAME', 'PROCESS-PATH', 'PROCESS-NAME-REGEX', 'PROCESS-PATH-REGEX',
    'NETWORK', 'UID', 'DSCP',
}


def check_rule(r):
    """返回规则的问题描述，没有问题返回 None。"""
    m = RULE_RE.match(r)
    if not m:
        return '规则格式异常'
    t, v = m.groups()
    if t not in TYPES:
        return '未知规则类型 %s' % t
    if t in ('IP-CIDR', 'IP-CIDR6', 'IP-ASN'):
        parts = v.split(',')
        if 'no-resolve' not in parts[1:]:
            return 'IP 规则缺少 no-resolve'
        if t == 'IP-ASN':
            if not parts[0].isdigit():
                return 'ASN 不是数字'
        else:
            try:
                ipaddress.ip_network(parts[0], strict=False)
            except ValueError:
                return 'CIDR 无法解析'
    return None

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
        err = check_rule(str(r))
        if err:
            bad.append('%s: %s —— %s' % (name, err, r))

    # 与 list 源文件条数比对
    lp = os.path.join(LIST, name + '.list')
    if not os.path.exists(lp):
        bad.append('%s: 没有对应的 list 源文件' % name)
        continue

    src = open(lp, encoding='utf-8').read()
    rules = [l.strip() for l in src.split('\n') if RULE_RE.match(l.strip())]
    # 逐条比对而非只比条数：两边各错一条时条数相同，只比条数会漏掉
    got = [str(r) for r in payload]
    if len(rules) != len(got):
        bad.append('%s: 条数不符 —— yaml %d 条，list %d 条' % (name, len(got), len(rules)))
    elif rules != got:
        i = next(k for k, (a, b) in enumerate(zip(rules, got)) if a != b)
        n = sum(a != b for a, b in zip(rules, got))
        bad.append('%s: 内容不符 %d 条，首处第 %d 条 —— list「%s」 yaml「%s」'
                   % (name, n, i + 1, rules[i], got[i]))

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
