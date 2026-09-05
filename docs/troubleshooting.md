# 排查记录

规则库这边踩过的坑。约定见 [design-notes.md](design-notes.md)。

配置侧的排查记录（provider 静默失效、策略组选择丢失、正则误匹配等）在
[Openclash-Config/docs/troubleshooting.md](https://github.com/MAXLYEN/Openclash-Config/blob/main/docs/troubleshooting.md)。

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

---

## 冗余规则的判定与停用

单个 `.list` 文件内部**无法**判断一条规则是否冗余 —— 冗余由整条规则链的顺序决定。
`scripts/dedupe.py` 读取 `Openclash-Config` 的产物 ini 还原顺序后做首命中模拟，
把结果分成三类：

| 类别 | 含义 | 处理 |
|---|---|---|
| A 同组冗余 | 被更早的规则命中，且目标分组相同 | 删了行为完全不变，可安全停用 |
| B 文件内重复 | 同一文件里被自己更宽的规则包含 | 同上 |
| C 异组冲突 | 被更早的规则命中，但目标分组不同 | **行为会变，只报告不处理** |

`--apply` 只处理 A 和 B，且遵循本仓库约定：注释停用而非删除，前缀 `# [已停用-冗余]`。

C 类占比最大（约 1790 条）但大多是设计如此 —— 例如 `GlobalMedia_Domain` 被
`YouTube_Domain` / `Disney_Domain` 提前命中，那正是「专属规则优先、泛媒体兜底」
的预期行为，不该动。
