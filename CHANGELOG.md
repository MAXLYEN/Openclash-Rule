# 规则库整理说明

适用项目：`MAXLYEN/Openclash-Rule`
整理日期：2026-08-05
规模：166 个规则集 / 81 个平台 / 26452 条规则

> 订阅转换模板（ini）的改动记录见模板项目的 CHANGELOG。

---

## 一、双格式目录结构

```
rules/
├── list/     166 个 .list —— 手动维护，唯一数据源
└── yaml/     166 个 .yaml —— 自动生成，供配置引用
```

### 为什么需要 yaml 版本

**这是本次整理中最关键的一处修复。**

配置中的 ruleset 只要带了更新间隔（`,3600` / `,28800`），订阅转换就会生成 **rule-provider** 而非内联展开规则。而 Clash 的 `classical` behavior provider 要求 payload 是 **YAML 数组结构**：

```yaml
payload:
  - DOMAIN-SUFFIX,claude.ai
  - DOMAIN-KEYWORD,anthropic
```

纯文本的 `.list` 格式（每行一条、无 `payload:` 键）解析不出任何内容。表现为 provider 加载成功但**规则数为 0**，内核直接跳过，流量继续往下走到兜底规则。

实测现象：访问 `claude.ai` 时日志显示

```
match GeoSite(category-ai-!cn) using Optional
```

而非预期的 `RuleSet(Claude_Domain)`。核对后确认 **166 个 provider 全部未生效**，一直是 GeoSite 在兜底——因为兜底大多也能把流量导向正确的组，问题被长期掩盖。

`list/` 保留纯文本格式便于阅读与手动编辑，`yaml/` 由脚本自动转换，两者内容始终一致。

### mrs 格式已评估但未采用

`mrs` 是 mihomo 的二进制规则集，体积优势显著（`China_IP_1` 由 96 KB 降至 5.3 KB），但存在两处限制：

1. **只支持 `domain` 与 `ipcidr` 两种 behavior**，无法表达 `DOMAIN-KEYWORD`。而本库 45 个文件含 keyword，且集中在关键位置——`EUNet_Domain` 163/179 条是 keyword、`SG_Domain` 27/28、`Game_Domain` 24/24，转换会丢失绝大部分规则。
2. ipcidr 类规则集默认触发 DNS 解析，配置语法能否传递 `no-resolve` 未经验证，存在解析泄漏风险。

综合判断收益不足以覆盖风险，暂不生成。

---

## 二、自动化构建

```
你修改 rules/list/  →  push  →  Actions 自动运行
                                    ↓
                    规范化 list 源文件 + 生成 yaml + 校验 + 提交
```

| 文件 | 作用 |
|---|---|
| `scripts/build.py` | 规范化 list、生成 yaml、补齐配对、清理孤儿产物 |
| `scripts/validate.py` | 用 YAML 解析器校验产物，条数与源文件比对 |
| `.github/workflows/build.yml` | 监听 `rules/list/**` 变化，自动构建并提交 |

### 自动修复项

以下问题在每次构建时就地修正，无需手动注意：

| 问题 | 处理 | 后果（若不修） |
|---|---|---|
| CRLF 换行 | 转为 LF | `\r` 并入域名，整个文件的规则永不命中 |
| 逗号后多余空格 | 去除 | 空格进入匹配串，规则失效 |
| IP 规则缺 `no-resolve` | 补齐 | 触发 DNS 解析，拖慢匹配并有泄漏风险 |
| `DOMAIN-KEYWORD` 含大写 | 转小写 | 域名匹配为小写，大写永不命中 |
| 文件内重复规则 | 去重 | — |
| header 统计与实际不符 | 重算 | — |
| 规则有变动 | 刷新 `UPDATED` | — |

### 告警项

以下问题无法自动修复，构建时输出到 Actions Summary，不阻断流程：

- `DOMAIN-KEYWORD` 含 `?` `=` `/` 或空格（URL 片段，恒不命中）
- `PROCESS-NAME`（网关转发场景取不到进程名，恒不生效）
- `_Domain` 混入 IP 规则 / `_IP` 混入域名规则
- 文件名不符合命名规范

### 其他行为

- 平台缺少 `_Domain` 或 `_IP` 一侧时，自动创建占位空文件
- `list/` 中删除的文件，其 `yaml/` 产物自动清理
- 内容无变化的文件不重写，不产生空提交
- 校验不通过时**不提交任何内容**，`yaml/` 保持上一个正确版本

---

## 三、修复的实际故障

### CRLF 换行（11 个文件）

`EUNet` `EUNetIP` `HK` `HKIP` `JP` `US` `UKNet` `UKNetIP` `Others` `Reject` `HDOBOXAds`

Windows 换行符 `\r` 会被并入域名字符串，形成 `bybit.com\r`，匹配不到任何流量。这些文件的规则从未生效过。

> 规律：手写文件基本都是 CRLF，从 blackmatrix7 同步的都是 LF。
> 建议在仓库根目录放置 `.gitattributes`：
>
> ```
> *.list text eol=lf
> ```
>
> 构建脚本也会自动修正，但源头防住更好。

### 逗号后多余空格（7 个文件）

`Apple` `Bybit` `Emby_2` `HK-wifi-call` `UK-wifi-call` `US-wifi-call` `User`

其中 `Bybit.list`（24 条）与 `User.list`（23 条）为全文命中，即整个文件失效。

### IP 规则缺 `no-resolve`

`Binance` 7 条、`EUNetIP` 20 条、`Game` 67 条，已统一补齐。

### GoogleVoice.list 内容与文件名不符

原文件唯一一条规则是 `DOMAIN,lens.l.google.com`——这是 Google Lens（图像识别），与 Google Voice 无关。已重写为 `voice.google.com` / `voice.telephony.goog` / `googlevoice.com` / `grandcentral.com`。

### 统计与日期

多个文件的 header 统计与实际条数不符，已重算。`Steam_CDN.list` 注释中的 `204/8/9` 笔误与其余文件内残留日期一并更新。

---

## 四、停用的规则（124 条，均保留为注释可恢复）

统一标记为 `# [已停用] 原规则  ← 原因`。

### PROCESS-NAME：81 条

匹配的是本机进程名。OpenClash 作为网关转发其他设备流量时，内核只能看到 IP 包和连接四元组，取不到发起进程——该进程在手机或电脑上，不在路由器上。

受影响最大的是 `Download.list`（34 条中 28 条为 PROCESS-NAME，停用后仅剩 6 条）与 `Direct.list`（36 条）。

### 恒不生效的规则：8 条

`PT.list` 中的 BT/DHT 协议字段：

```
DOMAIN-KEYWORD,announce.php?passkey=
DOMAIN-KEYWORD,peer_id=
DOMAIN-KEYWORD,info_hash
DOMAIN-KEYWORD,get_peers
DOMAIN-KEYWORD,find_node
DOMAIN-KEYWORD,announce_peer
```

这些是 tracker 请求的 URL 参数名或 UDP 报文字段，不会出现在域名中。含 `?` `=` 的两条尤其明显——域名不可能包含这两个字符。原始来源应为 Surge 的 `URL-REGEX` 规则，迁移时类型标错；Clash 无 URL 层匹配能力。

### 范围过宽的规则：35 条

按污染面排序：

| 文件 | 规则 | 说明 |
|---|---|---|
| GlobalMedia | `amazonaws.com` `amazonaws.co.uk` `cloudfront.net` `akamaized.net` | 整个 AWS 与两大 CDN，覆盖互联网极大比例流量 |
| GlobalMedia | `challenges.cloudflare.com` | Cloudflare 人机验证；验证节点与主站节点不一致会导致验证反复失败 |
| GlobalMedia | `gvt1.com` | Google 通用 CDN |
| Binance | `cloudfront` `amazonaws` `myqcloud` `amazontrust` | 通用 CDN；`myqcloud` 为腾讯云 COS，会把国内站点推向代理 |
| Binance | `appsflayer` | 拼写有误（应为 appsflyer），且本身是通用归因平台 |
| Binance | `forter` | 通用风控服务商 |
| EA / EUNet_1 | `akamaihd` `akamaihd.net` `cloudfront` | 通用 CDN；`akamaihd.net` 还与 `Custom_Direct` 的同名直连规则冲突 |
| Bahamut | `digicert.com` | 全球证书颁发机构，所有 HTTPS 站点都会访问 |
| Bahamut | `gvt1.com` | Google 通用 CDN |
| Disney / HBO | `execute-api.*.amazonaws.com` | AWS API Gateway 区域公共端点，任何人可用 |
| Game | `moco` | 4 字符常见词根 |
| Game | `app-analyics-services` | 拼写有误（analyics），恒不生效 |
| Game | `app-measurement` | Firebase Analytics，全网 App 通用，且与 GoogleCN 重复 |
| Claude | `DOMAIN-KEYWORD,claude` | claude 为常见法语人名；已由精确 SUFFIX 覆盖 |
| Claude | `cdn.usefathom.com` | Fathom Analytics，通用统计服务 |
| Copilot | `chat.openai.com.cdn.cloudflare.net` | 属于 OpenAI，位置放错 |
| Copilot | `api.statsig.com` `in.appcenter.ms` `browser-intake-datadoghq.com` | 通用第三方服务 |
| Gemini | `apis.google.com` | Google 全部 API 的公共入口，会截走 Drive/日历/YouTube 等 API 流量 |
| Gemini | `DOMAIN-KEYWORD,gemini` | 会撞 Gemini 交易所（gemini.com）；已改为精确域名 |
| Gemini | `DOMAIN-KEYWORD,colab` | 会匹配 colaborador 等西/葡语站点；已改为精确域名 |
| HK | `go-mpulse` | Akamai mPulse 性能监测，全网通用 |
| PT | `tracker` `audiences` | 通用词，文件内已有精确域名覆盖 |
| Amazon | `DOMAIN-SUFFIX,aws` | 非合法域名后缀，恒不生效 |
| Direct | `alt1-mtalk.google.com` `alt2-mtalk.google.com` | FCM 推送域名被提前直连，导致 GoogleFCM 分组失效 |

### 保留启用的例外

- `JP.list` 的 `coins`（coins.ph）、`maya`（Maya 菲律宾电子钱包）、`split`——经确认为实际使用中的规则，已就地加注用途与收窄建议（可改为 `DOMAIN-SUFFIX,coins.ph` / `maya.ph`）
- `SG.list` 全部规则未作改动。其中 `jumio`、`cloudauth-device` 虽属通用第三方服务，但为 KYC 流程必经环节，停用可能导致验证失败

---

## 五、文件组织

### 合并同源

| 结果 | 来源 |
|---|---|
| `EUNet_Domain` / `EUNet_IP` | EUNet + EUNet_1 + EUNetIP |
| `Emby_Domain` / `Emby_IP` | Emby + Emby_2 |
| `HBO_Domain` / `HBO_IP` | HBO + HBO_fix |
| `HK_Domain` / `HK_IP` | HK + HKIP |
| `UKNet_Domain` / `UKNet_IP` | UKNet + UKNetIP |
| `Amazon_Domain` / `Amazon_IP` | Amazon + AmazonIP |
| `China_Domain` / `China_IP_1/2/3` | ChinaDomain + ChinaIp（本就是同一平台的域名段与 IP 段） |

合并时保持各源文件内部原始行序，插入 `# === 以下合并自 xxx.list ===` 分界线，跨文件重复规则去重。分节中文注释与其下方规则的对应关系完整保留。

**未合并**：`GoogleCN` 与 `GoogleCNProxyIP` 名称相近但用途相反（前者直连、后者代理）；`HK-wifi-call` 与 `UK-wifi-call`、`US-wifi-call` 成体系，保持独立。

### 域名与 IP 强制成对

**每个平台一律产出 `平台_Domain` 与 `平台_IP` 两个文件，某一侧无规则时也建立占位空文件**，共 81 个平台、166 个文件，其中 49 个为占位空文件。

结构完全可预测：任意平台的域名规则必在 `_Domain`，IP 规则必在 `_IP`，新增规则时无需判断文件是否存在。构建脚本会自动补齐缺失的一侧。

### 超长文件分片（每片 2500 条）

- `China_IP_1` / `China_IP_2` / `China_IP_3`（6894 条）
- `ProxyGFWlist_Domain_1` / `_2` / `_3`（6131 条）

### 命名规范

- 统一格式：`平台名_类型[_序号].list`
- PascalCase，缩写全大写：`ChinaIp` → `China`，`ChinaCompanyIp` → `ChinaCompany`
- 类型后缀：`_Domain` / `_IP`，**所有文件必带其一**
- 分片序号紧随类型之后：`China_IP_1`，而非 `ChinaIP_1`
- 去除无语义序号：`EUNet_1`、`Emby_2`

### header 统一格式

```
# NAME: <与文件名一致>
# UPDATED: <规则有变动时自动刷新>
# DOMAIN: n
# DOMAIN-SUFFIX: n
# DOMAIN-KEYWORD: n
# IP-CIDR: n
# TOTAL: n
```

移除 `AUTHOR` / `REPO` / `SOURCE`，统计数字由脚本按实际内容生成。

---

## 六、遗留事项

1. **`AU_Domain` / `AU_IP` / `BR_Domain` / `BR_IP`** 为占位文件（0 条规则），待补充。
2. **`Others.list` 的 `DOMAIN-KEYWORD,ipinfo` 与 `Custom_Direct` 的 `ipinfo.io` 冲突**——模板中 Custom_Direct 位置靠前，ipinfo.io 走直连。若用于检测节点出口 IP，看到的将是真实出口而非节点 IP。
3. **`Download.list`** 停用 PROCESS-NAME 后仅剩 6 条域名关键词，可考虑补充下载站域名或停止引用。
4. **IP 合并未执行**——`Amazon_IP`（1802）、`China_IP`（6894）为官方发布的精确段，做 /24→/16 合并会吞掉大量不属于它们的地址（AWS 的段尤其碎）。该策略适用于零散收集的 IP，不适用于官方段。

---

## 七、自检结果

- CRLF 残留：0
- 逗号后空格：0
- IP 规则缺 `no-resolve`：0
- 未停用的 PROCESS-NAME：0
- 文件内重复规则：0
- header `NAME` 与文件名不符：0
- header 统计与实际条数不符：0
- 平台缺 `_Domain` 或 `_IP` 配对：0
- `_Domain` 文件混入 IP 规则：0
- `_IP` 文件混入域名规则：0
- 文件命名不符 `平台_类型[_序号]`：0
- yaml 产物可被 YAML 解析器正确读出 payload：166 / 166
- yaml 与 list 条数一致：166 / 166
