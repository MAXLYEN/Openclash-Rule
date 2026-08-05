<h1 align="center">Clash (Mihomo 内核) 分流规则</h1>

<p align="center">
  <a href="https://github.com/MAXLYEN/Openclash-Rule/stargazers"><img src="https://img.shields.io/github/stars/MAXLYEN/Openclash-Rule?style=flat-square&logo=github" alt="stars"></a>
  <a href="https://github.com/MAXLYEN/Openclash-Rule/commits/main"><img src="https://img.shields.io/github/last-commit/MAXLYEN/Openclash-Rule?style=flat-square" alt="last commit"></a>
  <img src="https://img.shields.io/badge/rules-26452-blue?style=flat-square" alt="rules">
  <img src="https://img.shields.io/badge/platforms-81-blue?style=flat-square" alt="platforms">
</p>

面向 OpenClash / Mihomo 的分流规则集，覆盖金融机构、科技平台、虚拟货币交易所、流媒体与游戏平台等常用场景。

规则以**平台**为单位组织，每个平台的域名规则与 IP 规则分别存放于独立文件，结构统一、可直接引用。

配套的订阅转换模板见 [Custom_OpenClash_Rules](https://github.com/MAXLYEN/Custom_OpenClash_Rules)。

---

## 目录结构

```
rules/
├── Netflix_Domain.list      域名规则
├── Netflix_IP.list          IP 规则
├── China_Domain.list
├── China_IP_1.list          超过 2500 条按序号分片
├── China_IP_2.list
└── China_IP_3.list
```

### 命名规范

格式为 `平台名_类型[_序号].list`

| 部分 | 说明 |
|---|---|
| 平台名 | PascalCase，缩写全大写（`ChinaCompany`、`GoogleCNProxyIP`） |
| 类型 | `_Domain` 或 `_IP`，**所有文件必带其一** |
| 序号 | 单文件超过 2500 条时分片，紧随类型之后（`China_IP_1`） |

**每个平台一律成对存在**。某一侧暂无规则时保留占位空文件，因此引用方无需判断文件是否存在，新增规则时也不必新建文件。

### 文件格式

采用 Clash `classical` 格式，域名与 IP 规则类型均可使用：

```
# NAME: Netflix
# UPDATED: 2026-08-04
# DOMAIN: 4
# DOMAIN-SUFFIX: 39
# DOMAIN-KEYWORD: 2
# TOTAL: 45
DOMAIN-SUFFIX,netflix.com
DOMAIN-KEYWORD,nflxvideo
```

- header 中的统计与 `TOTAL` 按实际内容生成
- 所有 IP 规则均带 `no-resolve`，避免触发 DNS 解析
- 换行符统一为 LF
- 停用的规则保留为 `# [已停用] 原规则  ← 原因`，可随时恢复

---

## 使用方法

### OpenClash 订阅转换

在订阅转换配置（ini）中引用，**必须带 `clash-classic:` 前缀**：

```
ruleset=Netflix,clash-classic:https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/Netflix_Domain.list,28800
ruleset=Netflix,clash-classic:https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/Netflix_IP.list,28800
```

> **前缀不可省略。** 省略时订阅转换会按 `domain` 格式解析，导致所有带 `DOMAIN-SUFFIX,` 等类型前缀的规则被整体丢弃，只有 `DOMAIN-KEYWORD` 侥幸生效 —— 规则看似加载成功，实则大部分失效。

### Mihomo 配置文件直接引用

```yaml
rule-providers:
  netflix-domain:
    type: http
    behavior: classical
    url: "https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/Netflix_Domain.list"
    path: ./ruleset/netflix-domain.list
    interval: 28800

rules:
  - RULE-SET,netflix-domain,Netflix
```

`behavior` 必须为 `classical`。

### 加速地址

国内环境建议使用 jsdelivr 镜像替代 `raw.githubusercontent.com`：

```
https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/文件名.list
```

jsdelivr 对 `@main` 分支引用存在 CDN 缓存，规则更新后生效可能延迟数小时。需要立即生效时可手动刷新：

```
https://purge.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/文件名.list
```

对更新时效要求高的规则（如金融、AI 平台），建议直接使用 raw 地址并将更新间隔设为 3600。

---

## 规则编写约定

提交或自行修改时请遵循以下几点，多数是踩过坑的：

**换行符必须为 LF。** CRLF 的 `\r` 会被并入域名字符串，形成 `example.com\r`，匹配不到任何流量。建议在仓库根目录放置 `.gitattributes`：

```
*.list text eol=lf
```

**逗号后不加空格。** `DOMAIN-SUFFIX, example.com` 中的空格会进入匹配串导致规则失效。

**IP 规则必须带 `no-resolve`。** 否则内核会先做 DNS 解析再比对 IP，拖慢匹配并带来解析泄漏风险。

**`DOMAIN-KEYWORD` 只匹配域名。** 含 `?` `=` `/` 或空格的内容（如 `announce.php?passkey=`、`peer_id=`）永远不会命中 —— 这类通常是从 Surge 的 `URL-REGEX` 误迁移而来，Clash 无 URL 层匹配能力。关键词也需为小写，大写永不命中。

**避免通用 CDN 与第三方服务。** `cloudfront`、`amazonaws`、`akamaihd`、`akamaized.net`、`gvt1.com`、`digicert.com`、`app-measurement` 这类会把海量无关站点拖入该分组，属于典型的规则污染。需要时应精确到具体子域。

**关键词长度与常见度。** 4 字符以内的词根（`moco`）、常见英文单词（`split`、`tracker`、`coins`）、常见人名（`claude`）误匹配面很大，优先使用 `DOMAIN-SUFFIX` 精确匹配。

**不使用 `PROCESS-NAME`。** 它匹配本机进程名，而 OpenClash 作为网关转发其他设备流量时取不到发起进程，此类规则在网关场景恒不生效。

---

## 收录范围

| 类别 | 平台 |
|---|---|
| 虚拟货币 | OKX、Binance、Bybit 等交易所与钱包 |
| 金融支付 | PayPal 及各地区支付、KYC 相关域名 |
| AI 平台 | OpenAI、Claude、Gemini、Copilot、Nvidia |
| 流媒体 | Netflix、Disney+、HBO、Prime Video、Hulu、Apple TV+、Emby、Spotify、Bahamut |
| 社交通讯 | Telegram、Twitter(X)、Snapchat、Talkatone |
| 游戏平台 | Steam、Epic、EA、暴雪、育碧、索尼、任天堂、Supercell |
| 电商 | Amazon、Shopee、Shopify、Ozon |
| 科技服务 | Google、Apple、Microsoft、GitHub、YouTube、TikTok |
| 地区分流 | 香港、日本、美国、英国、欧洲、土耳其 |
| 国内直连 | 中国大陆域名与 IP、国内媒体、小米、网易云音乐 |
| PT / BT | 私有 tracker 站点 |
| 广告拦截 | 通用广告、Talkatone 广告、HDO Box 广告 |

---

## 更新

持续更新中。规则变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

部分规则碎片来自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。
