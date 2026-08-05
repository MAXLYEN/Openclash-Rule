# 规则库整理说明

适用项目：`MAXLYEN/Openclash-Rule`（规则文件仓库）
整理日期：2026-08-04
规模：166 个规则文件 / 81 个平台 / 26452 条规则

> 订阅转换模板（ini）的改动记录不在本文档，见模板项目的 CHANGELOG。

---

## 一、修复的实际故障

以下问题导致规则**完全或部分失效**，不是风格调整。

### 1. CRLF 换行（11 个文件）

`EUNet` `EUNetIP` `HK` `HKIP` `JP` `US` `UKNet` `UKNetIP` `Others` `Reject` `HDOBOXAds`

Windows 换行符 `\r` 会被并入域名字符串，形成 `bybit.com\r`，**匹配不到任何流量**。这些文件的规则从未生效过。全部转为 LF。

> 规律：手写文件基本都是 CRLF，从 blackmatrix7 同步的都是 LF。
> 建议在仓库根目录加 `.gitattributes` 防止复发：
>
> ```
> *.list text eol=lf
> ```

### 2. 逗号后多余空格（7 个文件）

`Apple` `Bybit` `Emby_2` `HK-wifi-call` `UK-wifi-call` `US-wifi-call` `User`

`DOMAIN-SUFFIX, example.com` 中的空格会进入匹配串。其中 `Bybit.list`（24 条）与 `User.list`（23 条）为全文命中，即整个文件失效。

### 3. IP 规则缺 `no-resolve`

`Binance` 7 条、`EUNetIP` 20 条、`Game` 67 条。缺失会触发 DNS 解析后再比对 IP，既拖慢匹配也带来解析泄漏风险。已统一补齐。

### 4. GoogleVoice.list 内容与文件名不符

原文件唯一一条规则是 `DOMAIN,lens.l.google.com` —— 这是 Google Lens（图像识别），与 Google Voice 无关。已重写为 `voice.google.com` / `voice.telephony.goog` / `googlevoice.com` / `grandcentral.com`。

### 5. 统计与日期

多个文件的 header 统计与实际条数不符，已按实际内容重算。`Steam_CDN.list` 注释中的 `204/8/9` 为笔误，与其余文件内残留日期一并更新。

---

## 二、停用的规则（124 条，均保留为注释可恢复）

统一标记为 `# [已停用] 原规则  ← 原因`。

### PROCESS-NAME：81 条

匹配的是本机进程名。OpenClash 作为网关转发其他设备流量时，内核只能看到 IP 包和连接四元组，取不到发起进程 —— 该进程在手机或电脑上，不在路由器上。此类规则在网关场景恒不生效。

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

这些是 tracker 请求的 URL 参数名或 UDP 报文字段，**不会出现在域名中**。含 `?` `=` 的两条尤其明显 —— 域名不可能包含这两个字符。原始来源应为 Surge 的 `URL-REGEX` 规则，迁移时类型标错。Clash 无 URL 层匹配能力，只能依靠 tracker 的实际域名。

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

- `JP.list` 的 `coins`（coins.ph）、`maya`（Maya 菲律宾电子钱包）、`split` —— 经确认为实际使用中的规则，已就地加注用途与收窄建议（可改为 `DOMAIN-SUFFIX,coins.ph` / `maya.ph`）
- `SG.list` 全部规则未作改动。其中 `jumio`、`cloudauth-device` 虽属通用第三方服务，但为 KYC 流程必经环节，停用可能导致验证失败

### 自动检查规则

以下两项已内置到处理流程，后续新增规则同样生效：

- `DOMAIN-KEYWORD` 含 `?` `=` `/` 或空格 → 自动停用（域名不含这些字符，属 URL 片段）
- `DOMAIN-KEYWORD` 含大写字母 → 自动转小写（域名匹配为小写，大写永不命中）

---

## 三、文件组织

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

### 域名与 IP 彻底分离（强制成对）

**每个平台一律产出 `平台_Domain.list` 与 `平台_IP.list` 两个文件，某一侧无规则时也建立占位空文件**，共 81 个平台、166 个文件，其中 49 个为占位空文件。

结构完全可预测：任意平台的域名规则必在 `平台_Domain.list`，IP 规则必在 `平台_IP.list`，新增规则时无需判断文件是否存在。

拆分时注释归属其下方的第一条规则，不产生孤儿注释。占位空文件的 header 中注明用途。

分离后每个文件均为单一 behavior 类型，后续可直接切换为 `clash-domain:` / `clash-ipcidr:`，或编译为 mrs 二进制格式。

> 注：切换到 `clash-domain` 需要额外做格式转换 —— 去掉 `DOMAIN-SUFFIX,` 前缀并改写为 `+.example.com`。当前 classical 格式无需转换即可使用。

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
# UPDATED: 2026-08-04
# DOMAIN: n
# DOMAIN-SUFFIX: n
# DOMAIN-KEYWORD: n
# IP-CIDR: n
# TOTAL: n
```

移除 `AUTHOR` / `REPO` / `SOURCE`，统计数字按实际内容重算。

---

## 四、遗留事项

1. **`AU_Domain` / `AU_IP` / `BR_Domain` / `BR_IP`** 为占位文件（0 条规则），待补充。
2. **`Others.list` 的 `DOMAIN-KEYWORD,ipinfo` 与 `Custom_Direct` 的 `ipinfo.io` 冲突** —— 模板中 Custom_Direct 位置靠前，ipinfo.io 走直连。若用于检测节点出口 IP，看到的将是真实出口而非节点 IP。
3. **`Download.list`** 停用 PROCESS-NAME 后仅剩 6 条域名关键词，可考虑补充下载站域名或停止引用。
4. **IP 合并未执行** —— `Amazon_IP`（1802）、`China_IP`（6894）为官方发布的精确段，做 /24→/16 合并会吞掉大量不属于它们的地址（AWS 的段尤其碎）。该合并策略适用于零散收集的 IP，不适用于官方段。

---

## 五、自检结果

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
