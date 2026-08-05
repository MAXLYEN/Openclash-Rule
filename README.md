<h1 align="center">Clash (Mihomo 内核) 分流规则</h1>

<p align="center">
  <a href="https://github.com/MAXLYEN/Openclash-Rule/stargazers"><img src="https://img.shields.io/github/stars/MAXLYEN/Openclash-Rule?style=flat-square&logo=github" alt="stars"></a>
  <a href="https://github.com/MAXLYEN/Openclash-Rule/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/MAXLYEN/Openclash-Rule/build.yml?style=flat-square&label=build" alt="build"></a>
  <a href="https://github.com/MAXLYEN/Openclash-Rule/commits/main"><img src="https://img.shields.io/github/last-commit/MAXLYEN/Openclash-Rule?style=flat-square" alt="last commit"></a>
</p>

面向 OpenClash / Mihomo 的分流规则集，覆盖金融机构、科技平台、虚拟货币交易所、流媒体与游戏平台等常用场景。

规则以**平台**为单位组织，每个平台的域名规则与 IP 规则分别存放于独立文件。仓库提供 `.list` 与 `.yaml` 两套格式，后者由 GitHub Actions 自动生成。

配套的订阅转换模板见 [Custom_OpenClash_Rules](https://github.com/MAXLYEN/Custom_OpenClash_Rules)。

---

## 目录结构

```
rules/
├── list/                    手动维护，唯一数据源
│   ├── Netflix_Domain.list
│   ├── Netflix_IP.list
│   └── China_IP_1.list      超过 2500 条按序号分片
└── yaml/                    自动生成，请勿手动编辑
    ├── Netflix_Domain.yaml
    ├── Netflix_IP.yaml
    └── China_IP_1.yaml
```

**引用配置时请使用 `yaml/` 目录。** 原因见下方「为什么需要两套格式」。

### 命名规范

格式为 `平台名_类型[_序号]`

| 部分 | 说明 |
|---|---|
| 平台名 | PascalCase，缩写全大写（`ChinaCompany`、`GoogleCNProxyIP`） |
| 类型 | `_Domain` 或 `_IP`，**所有文件必带其一** |
| 序号 | 单文件超过 2500 条时分片，紧随类型之后（`China_IP_1`） |

**每个平台一律成对存在**。某一侧暂无规则时保留占位空文件，因此引用方无需判断文件是否存在。新建单侧文件时，构建流程会自动补齐另一侧。

---

## 使用方法

### OpenClash 订阅转换

引用 `rules/yaml/` 下的文件，**必须带 `clash-classic:` 前缀**：

```
ruleset=Netflix,clash-classic:https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/Netflix_Domain.yaml,28800
ruleset=Netflix,clash-classic:https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/Netflix_IP.yaml,28800
```

### Mihomo 配置文件直接引用

```yaml
rule-providers:
  netflix-domain:
    type: http
    behavior: classical
    url: "https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/Netflix_Domain.yaml"
    path: ./ruleset/netflix-domain.yaml
    interval: 28800

rules:
  - RULE-SET,netflix-domain,Netflix
```

`behavior` 必须为 `classical`。

### 加速地址

国内环境建议使用 jsdelivr 镜像替代 `raw.githubusercontent.com`：

```
https://testingcf.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/文件名.yaml
```

jsdelivr 对 `@main` 分支引用存在 CDN 缓存，更新后生效可能延迟数小时。需要立即生效时手动刷新：

```
https://purge.jsdelivr.net/gh/MAXLYEN/Openclash-Rule@main/rules/yaml/文件名.yaml
```

对时效要求高的规则（金融、AI 平台），建议直接使用 raw 地址并将更新间隔设为 3600。

---

## 为什么需要两套格式

配置中的 ruleset 只要带了更新间隔（`,3600` / `,28800`），生成的就是 **rule-provider**。而 Clash 的 `classical` behavior provider 要求 payload 为 **YAML 数组结构**：

```yaml
payload:
  - DOMAIN-SUFFIX,netflix.com
  - DOMAIN-KEYWORD,nflxvideo
```

纯文本 `.list`（每行一条，无 `payload:` 键）**解析不出任何内容** —— provider 会加载成功但规则数为 0，内核直接跳过，流量落到后续的兜底规则。这个问题很隐蔽：兜底通常也能把流量导向正确的策略组，表面看不出异常。

因此：

- `list/` 保留纯文本格式，便于阅读和手动编辑
- `yaml/` 由脚本自动转换，是实际供配置引用的格式

两者内容始终一致，由 CI 校验保证。

---

## 自动化构建

修改 `rules/list/` 下任意文件并提交后，GitHub Actions 会自动完成：

```
规范化 list 源文件 → 生成 yaml → 校验 → 提交回仓库
```

**你只需要维护 `rules/list/`。**

### 自动修复

以下问题在每次构建时就地修正：

| 问题 | 处理 | 若不修的后果 |
|---|---|---|
| CRLF 换行 | 转为 LF | `\r` 并入域名，整个文件的规则永不命中 |
| 逗号后多余空格 | 去除 | 空格进入匹配串，规则失效 |
| IP 规则缺 `no-resolve` | 补齐 | 触发 DNS 解析，拖慢匹配并有泄漏风险 |
| `DOMAIN-KEYWORD` 含大写 | 转小写 | 域名匹配为小写，大写永不命中 |
| 文件内重复规则 | 去重 | — |
| header 统计与实际不符 | 重算 | — |
| 规则有变动 | 刷新 `UPDATED` | — |
| 平台缺少配对文件 | 自动创建占位 | — |
| `list/` 中已删除的文件 | 清理对应 yaml 产物 | — |

### 告警

无法自动修复的问题会输出到 Actions Summary，不阻断构建：

- `DOMAIN-KEYWORD` 含 `?` `=` `/` 或空格（URL 片段，恒不命中）
- `PROCESS-NAME`（网关转发场景取不到进程名，恒不生效）
- `_Domain` 混入 IP 规则 / `_IP` 混入域名规则
- 文件名不符合命名规范

### 校验

构建后用 YAML 解析器逐个验证产物，并与 list 源文件比对条数。**校验不通过时不提交任何内容**，`yaml/` 保持上一个正确版本，不会把损坏的产物推到线上。

---

## 规则编写约定

多数是踩过坑总结的，构建脚本能自动修前四条，但从源头避免更好：

**换行符用 LF。** 建议在仓库根目录放置 `.gitattributes`：

```
*.list text eol=lf
```

**逗号后不加空格。** `DOMAIN-SUFFIX, example.com` 中的空格会进入匹配串。

**IP 规则带 `no-resolve`。** 否则内核会先做 DNS 解析再比对 IP。

**`DOMAIN-KEYWORD` 用小写，且只匹配域名。** 含 `?` `=` `/` 或空格的内容（如 `announce.php?passkey=`、`peer_id=`）永远不会命中 —— 这类通常是从 Surge 的 `URL-REGEX` 误迁移而来，Clash 无 URL 层匹配能力。

**避免通用 CDN 与第三方服务。** `cloudfront`、`amazonaws`、`akamaihd`、`akamaized.net`、`gvt1.com`、`digicert.com`、`app-measurement` 这类会把海量无关站点拖入该分组。需要时应精确到具体子域。

**注意关键词长度与常见度。** 4 字符以内的词根（`moco`）、常见英文单词（`split`、`tracker`、`coins`）、常见人名（`claude`）误匹配面很大，优先用 `DOMAIN-SUFFIX` 精确匹配。

**不使用 `PROCESS-NAME`。** 它匹配本机进程名，而 OpenClash 作为网关转发其他设备流量时取不到发起进程。

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

持续更新中。整理与变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

部分规则碎片来自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。
