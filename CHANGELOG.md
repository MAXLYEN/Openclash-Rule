# 更新记录

规则内容的更新与 [Openclash-Config](https://github.com/MAXLYEN/Openclash-Config) 模板的更新相互独立。

设计约定见 [docs/design-notes.md](docs/design-notes.md)，排查记录见 [docs/troubleshooting.md](docs/troubleshooting.md)。

---

## 2026-09-26（AI 编程模型与 Meta 分流）

- 按最终路由要求，撤销 `meta.ai` / `meta.com` 的 UKNet 例外，将两者及其子域改回 USNet；Meta 一方域名在本规则库目标策略组统一为 USNet。实际出口仍需核对路由器上 USNet 当前所选节点。
- `meta.com` 及其子域跟随 `meta.ai` 改走 UKNet，覆盖 Meta 英国官网与 `ai.meta.com`；Muse 继续保持 USNet。
- `meta.ai` 及其子域从 USNet 改为 UKNet：用户在原美国出口看到地区不可用提示；英国已在 Meta 公布的支持地区中。Muse 保持 USNet。
- 补齐 Meta Muse 的独立入口 `muse.ai`，连同 `auth.muse.ai` 等子域走 USNet；`meta.ai` 原已在 USNet 规则中。
- 补齐阶跃星辰 StepFun / Step Code：中国站 `stepfun.com`（含 API 和安装资源）直连，国际站 `stepfun.ai`（含 API）走 USNet；以官方中国站 / 国际站说明区分。
- `US_Domain` 收录 Meta 官方社交、模型 API、开发者与 Oculus 一方域名，以及 Devin、Windsurf、Cursor、Z.ai 和 Kimi 国际平台的站点与 API；`Game_Domain` 停用先于 US 命中的 `fbsbx` 关键字。
- 补充 OpenAI、Claude、GitHub Copilot 的独立服务域名；DeepSeek、BigModel、Kimi 国内站与 Qwen 国内入口放入早于通用 AI geosite 的直连规则。
- 阿里云百炼按官方 API 接入地域分别进入北京直连、新加坡、美国、香港、东京、法兰克福对应策略组；完整主机名、地区依据与待配合的 Meta IP 分流见 [编程模型网站与 API 分流规格](docs/ai-coding-routing.md)。
- 手工维护和提交 `rules/list` 源文件；推送后由 GitHub Actions 构建、校验并提交 `rules/yaml` 产物，不在本地手工修改或上传 YAML。

---

## 2026-09-25（十二）

币安 App 被识别为国内 IP：日志里的连接全部走代理，排查出 App 内嵌 SDK 的上报端点被规则直连——服务端按来源 IP 记录地区。

- `Custom_Proxy_Domain` 新增统计 / 崩溃上报 / 归因 SDK：`app-measurement.com`、`google-analytics.com`、`googleanalytics.com`、`ssl-google-analytics.l.google.com`（Firebase Analytics）、`crashlytics.com`、`crashlyticsreports-pa.googleapis.com`（Crashlytics）、`appsflyer.com`、`adjust.com`。原先由 `GoogleCN_Domain`、`GEOSITE,google-cn`、`Direct_Domain` 直连；`Custom_Proxy_Domain` 排在它们之前才截得住。`Direct_Domain` / `GoogleCN_Domain` 的同名直连条目以 `[已停用-分组冲突]` 注明
- `Binance_Domain` 新增 `DOMAIN-KEYWORD,addfd325e6e3`：币安在反欺诈服务 Forter 上的商户编号（日志中的 `addfd325e6e3.cdn4.forter.com` 等），原先落到 `Amazon_IP` 走香港，与主站 SG 出口不一致
- `IPCheck_Domain` 明确收录境外 IP 查询服务（`ipify.org`、`ifconfig.me`、`icanhazip.com`、`ip.sb` 等），走代理；原先大多落到 FINAL，结果相同
- 保持直连（用户指定）：`Custom_Direct_Domain` 的 `ipinfo.io` 与路由器 DDNS 取公网 IP 用的 `checkip.dyndns.org`、`ifconfig.co`、`api.myip.com`、`ipapi.co`、`ip6.seeip.org`、`members.3322.org`；国内 IP 查询（IPIP.NET、PConline、`ip.cn` 等）由 `China_Domain` / `GEOSITE,cn` 直连

## 2026-09-25（十一）

按 MEXC App 的连接日志，把 MEXC 全部连接统一到 JPNet（用户要求必须走亚洲出口）：

- `EUNet_Domain` 停用 `mexc`、`greentreeone`、`mocortexh` 三个关键字（`[已停用-分组冲突]`），移入 `JP_Domain` 的 `#mexc` 段。日志中 `tracking.mexc.cg`、`www` / `otc` / `affiliates.greentreeone.com` 走的是 EUNet（德国），而同一 App 的 `mocortech.com`、`payapptoday.com`、`gotoda.co` 早已在 `JP_Domain`——`EUNet_Domain` 排在 `JP_Domain` 之前，关键字先命中。`mocortexh` 疑为 `mocortech` 的笔误，随同迁移，保证不会再有 MEXC 相关域名落到欧洲
- 未处理：App 内 Google 登录的 `oauth2.googleapis.com` 属于 Google 通用接口，仍走 Google 组；`EUNet_Domain` 的交易所通用 SDK 关键字（`pushsdk`、`mixpanel`、`onesignal` 等）被多家交易所共用，按域名无法区分 App，保持 EUNet

## 2026-09-25（十）

Openclash-Config v2.10 撤除内联内容规则（规则内容一律放本仓库）后，把归属在规则内容层面恢复，并处理同日覆盖复查的两项：

- 新增成对的 `CryptoCom_Domain` / `CryptoCom_IP`（IP 侧为占位）：`crypto.com` 原靠 Config 的内联 `[]DOMAIN-SUFFIX,crypto.com` 归 Cryptocurrency 组，撤除后首命中落到 `SG_Domain`（SGNet），切换 Cryptocurrency 组时不跟随。`SG_Domain` 的 `crypto.com` 以 `[已停用-分组冲突]` 停用。单独成集而不放进 `OKX_Domain` / `Binance_Domain`，避免串味。**需要 Config 在 `OKX_Domain` 之前引用、挂 Cryptocurrency 组**；引用前由 ⑨ 之后的 `GEOSITE,category-cryptocurrency` 兜底，同样落在 Cryptocurrency 组
- `Netflix_Domain` 停用 `DOMAIN-KEYWORD,netflix`（`[已停用-范围过宽]`）：它排在 `Emby_Domain` 之前，截走了 Emby 服 `notnetflix.cos.cat`。上游 v2fly、MetaCubeX geosite:netflix、blackmatrix7 Netflix 列表都没有这个关键字，其后缀本文件已全部收录，Netflix 实际域名不受影响。被它判为冗余的 `netflixdnstest` 关键字由 `dedupe.py` 恢复。`GlobalMedia_Domain` 的 `dashasiafox.akamaized.netflix` 随之由 Global TV 接管。不需要改 Config
- 新增成对的 `HuluJP_Domain` / `HuluJP_IP`（IP 侧为占位）：`hulu.jp`、`happyon.jp`、`hjholdings.jp`、`streaks.jp`、`yb.uncn.jp`（与 blackmatrix7 HuluJP 列表一致）和 HJ Holdings 的 `prod.hjholdings.tv`。日本 Hulu 需要日本 IP，原在 `Hulu_Domain` 跟着 Hulu 组走 USNet；按「仅共用地区节点的归锚点组」归 JPNet（先例 `AppleAI_Domain` → USNet）。`Hulu_Domain` 的这 6 条以 `[已停用-分组冲突]` 停用；`GlobalMedia_Domain` 的同名条目本就是异组冲突，不动。**需要 Config 在 `Hulu_Domain` 之前引用、挂 JPNet**——geosite:disney 含 `+.hulu.jp`，也必须排在 `GEOSITE,disney` 之前。引用前 `hulu.jp` 落到 Disney+、其余 5 个落到 `GlobalMedia_Domain`（Global TV），都不是日本出口
- `Direct_Domain` 补 14 个国内游戏站：`Game_Domain` 的 `pubg`、`roblox`、`supercell`、`brawlstars` 关键字把它们带进 Game Platform。其中 `brawlstars.cn`、`pubghelper.com`、`pubgno1.cn`、`pubgtool.com`、`roblox.cn`、`roblox.qq.com`、`robloxdev.cn`、`supercellcommunity.cn`、`supercellsupport.cn` 在 v2fly category-games-cn（但不在 Config ⑦ 引用的 `category-games@cn` 里），`cnpubg.com`、`pubg.plus`、`pubg8x.com`、`pubgkam.com`、`pubgzh-cn.vip` 在 geosite:cn。关键字不收窄：上游 pubg 列表只有 `pubg.com`、`playbattlegrounds.com`、`kraftonde.com`，收窄会断 `pubgmobile.com` 等
- 未处理：`igamecj`、`gpubgm`、`amsoveasea`、`onezapp`、`tdatamaster`、`vasdgame`、`wetest*`、`supercell.com`、`clashroyaleapp.com`、`proximabeta`、`anticheatexpert`、`hk/nagcloudcs` 虽在 geosite:cn，实为海外游戏基础设施或已列入有意保留

## 2026-09-25（九）

按连接日志修正 LINE 日本版与 Yahoo 的分流：

- `GlobalMedia_Domain` 停用 `line-cdn.net`、`line-scdn.net`（`[已停用-分组冲突]`）：LINE 全站通用的静态资源 CDN 排在 `JP_Domain` 之前，LINE 的图片、贴图、动态、新闻一直走 Global TV（HK），只有 `line.me` / `line-apps.com` 走 JPNet。现由 `JP_Domain` 接管；LINE TV 台湾版的 `linetv.tw` 仍留在 GlobalMedia
- `GlobalMedia_Domain` 停用 `s.yimg.jp`（原为已停服的 GYAO!），由 `JP_Domain` 的 `yimg.jp` 接管
- `JP_Domain` 补 `line-home.flvcdn.net`（LINE 首页视频，日志中落到 FINAL；`flvcdn.net` 用途不明，只收这个子域）和上游 geosite:line 的其余域名（`lin.ee`、`linegame.jp`、`linemobile.com` 等）
- Yahoo 全球主站与公共资源定到 JPNet（用户指定）：`JP_Domain` 补 `yahoo.com`、`yahoo.net`、`yimg.com`、`yahoodns.net`、`yahooinc.com`、`yusercontent.com`、`ymail.com`，原先走 GFW 列表（Proxy=HK）。各国分站（`yahoo.com.hk`、`yahoo.com.sg`、`yahoo.co.uk` 等）仍归各自地区

## 2026-09-25（八）

规则覆盖复查（首次把链上 GEOSITE 按 MetaCubeX 文本版展开做首命中模拟），并与另外两份独立分析交叉核对：

- `dedupe.py` 判定修正：首命中改取**链上最早**的覆盖项，而不是最具体的后缀；ini 里的内联域名规则（`[]DOMAIN-SUFFIX,crypto.com`）参与遮蔽判定。旧逻辑把 `User_Domain` 的 `u2.dmhy.org` 判成撞上 `PrivateTracker_Domain` 的同名条目（异组），实际先被同组 `Custom_Proxy_Domain` 的 `dmhy.org` 命中——现已停用；`ProxyGFWlist_Domain_1` 的 `google.eu` / `.hk` / `.us` 实际被 `Google_Domain` 先命中（异组），不属冗余，已恢复（出口不变）
- `ChinaMedia_IP` 的 29 条 `IP-CIDR6,::ffff:<IPv4>/128` 永远不会命中：内核把 IPv4 目标按 4 字节地址比较，IPv4 不匹配 IPv6 前缀。26 条转为 `IP-CIDR,<IPv4>/32`；3 条 `198.18.*` 是 fake-IP 虚拟地址（从连接日志误抄），停用而不转换。`build.py` 对这两类写法告警（`198.18.0.0/15` 整段作保留地址直连不告警）
- `tmall.hk`、`jd.hk`、`xiumi.us` 加入 `Direct_Domain`：`China_Domain` 里的同名直连规则排在 `ProxyGFWlist_Domain_1` 的 `.hk` / `.us` 顶级域后缀之后，从未命中，天猫国际、京东国际一直走代理
- 过宽关键字收窄（依据：上游 v2fly 列表或官方域名）：`JP_Domain` 的 `gcash` → `gcash.com` + `m-gcash-com.s3.ap-southeast-1.amazonaws.com`（原先截走 `BR_Domain` 的 `ngcash`）；`US_Domain` 的 `tubi` → `tubi.io` / `tubi.tv` / `tubi.video` / `tubitv.com`，`chime` → `chime.com` / `chimebank.com`（原先命中长隆 `chimelong.com`）；`BR_Domain` 的 `neon` 停用，`neon.com.br` 已由同文件的 `com.br` 覆盖
- `HK_Domain` 的 `mushroomtrack` 关键字停用，由 `AU_Domain` 的 `mushroomtrack.com` 接管（走 AUNet）
- `HK_Domain` 的 `biya`（BiyaPay）没有 App 实际域名依据，保留关键字；被它误伤的必要商城 `biyao.com` 加入 `Direct_Domain`
- 按上游 geosite 补漏：`Gemini_Domain` +30（Gemini CLI / Code Assist、NotebookLM、Antigravity、Jules、Flow、`ai.studio` 等，原先被 `Google_Domain` 截进 Google 组）；`Snap_Domain` +3（`sc-static.net`、`sc-gw.com`，原先落到 FINAL）；`Telegram_Domain` +3（Fragment、TON）；`Nvidia_Domain` +1
- 未处理：交易所类关键字（`htx`、`bwb`、`bingx`、`blockchain`、`okx`）误伤少量冷门国内站点，按「交易所出口一致」的约定保留；`SG_IP` 唯一的 `43.128.0.0/16` 被 `Game_IP` 的腾讯云段覆盖，是保留海外腾讯游戏大段的代价
- Openclash-Config 侧另行处理：Hulu 被前面的 `GEOSITE,disney`（含全部 Hulu 域名）截进 Disney+；`category-entertainment` 先于 `category-games`，游戏兜底大半落到 Global TV；`category-games` 把 4399 等国内游戏站带进代理；Emby 的 `notnetflix.cos.cat` 被 `netflix` 关键字截走

## 2026-09-25（七）

来自 Openclash-Config 会话的交叉检查，逐条核实后处理：

- `dedupe.yml`：`config-updated` 带来的提交号先校验格式（7–40 位十六进制）再拼进 URL；`--ini` 参数改用数组传递，不经分词；加 `pipefail`，拉取配置失败时运行变红，而不是带着空报告通过
- 新增 `check-token.yml`：每周一检查 `DISPATCH_TOKEN` 是否仍能访问 Openclash-Config、剩余有效期是否不足 14 天。通知步骤是 `continue-on-error`，token 过期后运行仍是绿的，对方也只是「收不到通知」，以前没有任何地方能发现。反方向由 Config 的 `build-ini.yml` 检查
- `validate.py` 增加规则类型白名单（`DOMAIN-SUFIX` 这类拼写错误会被 classical provider 跳过、静默失效）；IP 规则检查 CIDR 可解析、ASN 为数字、带 `no-resolve`。主机位与地址族不符仍只由 `build.py` 告警——规则照样生效，不值得阻断发布
- 收窄过宽关键字：`EUNet_Domain` 的 `n26` → `DOMAIN-SUFFIX,n26.com`（原写法命中 `cdn26`、`sn26` 等编号主机名，同段已有 `number26`、`tech26.de`）；`China_Domain` 的 `moke` 停用，恢复被它顶掉的 `DOMAIN-SUFFIX,moke.com`（原写法命中 `smoke`）
- `HBO_Domain` 停用 `braze`、`branch`：通用推送 / 归因 SDK，所有 App 的这类流量都会被带进 HBO 组；`branch` 还是常见词。与 `UK_Domain` 已停用 `braze.com`、`branch.io` 的处理一致
- `docs/design-notes.md`：合并同源表改为 `UK_Domain` / `UK_IP`，注明 `UKNet_*`、`Others_Domain` 是 v1 兼容文件；写明 dedupe 只按 V2 顺序判断、对冻结的 v1 可能误停
- 未处理：`BR_Domain` 的 `neon`（意图应是巴西 Neon 银行，会误中 `neon.tech`），需要该 App 实际连接的域名才能收窄；`UKNet_Domain` 的 `argent` 只被冻结的 v1 引用，不动

## 2026-09-25（六）

- `dedupe.py` 新增【D IP 覆盖】报告：按规则链做 IP-CIDR 的首命中模拟，列出被更早的段完整包含的条目（分异组 / 同组）与遮蔽最多的段。**只报告不处理**——链上夹着看不到的 GEOIP 行，且大量重叠来自官方段之间，是否处理需要人工判断。首命中取链上最早的包含段；与逐条两两比较的实现核对结果完全一致（当前异组 228 条、同组 119 条），耗时约 0.3 秒
- 当前报告中遮蔽最多的是 `Apple_IP` 的 `17.0.0.0/8`（覆盖 `China_IP_1` 里 56 段 Apple 中国机房）；同组覆盖主要是 `ChinaCompany_IP` 被 `China_IP` 完整包含（93 条）
- GEOSITE / GEOIP 仍不展开：路由器实际使用的 geodata（Loyalsoldier / MetaCubeX）与 v2fly 不完全一致，展开后的结论可能与真实行为不符

## 2026-09-25（五）

- `build.yml` / `dedupe.yml` 运行环境由 `ubuntu-latest` 固定为 `ubuntu-24.04`：GitHub 自 2026-10-19 起将 `ubuntu-latest` 迁移到 Ubuntu 26，固定版本避免运行环境在无改动的情况下变化。Openclash-Config 同步处理

## 2026-09-25（四）

与 Openclash-Config 联合复查：两个仓库的自动化衔接。

- `build.yml` 通知 Openclash-Config 时改传**含产物的 bot 提交号**（原为触发构建的源提交，其上 `rules/yaml` 还是旧的）；配合对方改为按提交号校验，推送后立即触发的校验不再读到自建镜像约 5 分钟前的旧内容
- `dedupe.yml` 接入反向通知：收到 `config-updated` 时按对方提交号读取 V2 规则链，只出报告；有待停用 / 恢复项或引用缺失时打 `::warning::`，不再只躺在 Summary 里。发送端在 Openclash-Config，需要其配置 `RULE_DISPATCH_TOKEN`
- `build.yml` / `dedupe.yml` 推送产物失败时 rebase 后重试（最多 3 次，冲突即中止），与 Openclash-Config 对齐——只改 README / docs 的推送不触发构建、不受 concurrency 保护，会与 bot 推送撞车
- README：配套仓库链接由已不存在的 `Custom_OpenClash_Rules` 改为 `Openclash-Config`；删除「时效敏感规则直接用 raw 地址」的建议（OpenClash 会改写 raw 地址致缓存刷新失效，Openclash-Config 的校验已将其判为错误）
- `docs/design-notes.md`「与 Openclash-Config 的边界」补充双向通知与密钥说明
- `build.yml` 刷新 jsdelivr 缓存改为按本次运行前后远端 main 上的 `rules/yaml` 变化决定：此前只看 bot 提交，本地生成 yaml 一起推送时 bot 无可提交，一个都不刷（如 `b57c37a` 改了 5 个 yaml，CI 打印「无 yaml 变动」）。与 Openclash-Config 的同类修复一致
- `dedupe.yml` 以 apply 模式推送后补做刷新 jsdelivr 缓存与通知 Openclash-Config（`rules-updated`，携带推送后的 HEAD）：它用 `GITHUB_TOKEN` 推送，不会触发 `build.yml`，此前这两步都不执行，规则集被清空只能等对方每周一的定时校验发现

## 2026-09-25（三）

构建校验补强与文档同步。

- `build.py` 新增告警：IP-CIDR 含主机位 / 无法解析 / 与地址族不符（本次修正的 `/16` 误写即此类，内核按掩码截断不会报错）；单文件超过 2500 条分片上限（`China_IP_1` / `_2` 已满，新增请加到 `_3`）
- `validate.py` 改为 list 与 yaml **逐条比对内容与顺序**，不再只比条数——两边各错一条时条数相同，原先会漏掉
- `docs/design-notes.md`：现状数字更新（172 个文件 / 84 个平台 / 55 个占位）；章节重新编号、去掉重复分隔线；新增「停用标记与有意保留」一节，写明 `[已停用-冗余]` 仅限 `dedupe.py` 使用，以及复查时不必再报的有意保留项
- `docs/troubleshooting.md` 章节重新编号；README 的告警与校验说明同步
- 下方 2026-08-05 的遗留事项逐条标注当前状态

## 2026-09-25（二）

全面复查的 IP 规则项（均为 `no-resolve`，只影响按 IP 直连的流量：游戏对战、语音、P2P 等）。依据 AWS 官方 `ip-ranges.json` 的区域字段。

- `Amazon_IP` 停用 44 段 AWS 中国区（cn-north-1 / cn-northwest-1）：排在 `China_IP` 之前，国内按 IP 访问 AWS 北京 / 宁夏的服务会走 Proxy；现由 `China_IP` 直连
- `Netflix_IP` / `GlobalMedia_IP` 各停用 29 段 ≤/16 的 AWS 整区大段（us-east-1 / us-west-2 / eu-west-1 等，每个文件约 520 万地址）：排在游戏与 Amazon 之前，截走了 `Supercell_IP` 与 `Game_IP` 的服务器段。Netflix 自有 CDN 段不受影响
- 修正 5 段带主机位的 CIDR：`ProxyGFWlist_IP` 的 `108.168.174.0` / `174.37.243.0` / `75.126.150.0` / `69.171.235.0` 由 `/16` 改为 `/24`（相邻条目均为 /27、/30 精确段，/16 为误写，实际生效范围是整个 /16）；`China_IP_1` 的 `185.188.32.1/28` 规范为 `185.188.32.0/28`（效果不变）
- 保留：`Game_IP` 的 68 个云厂商 /16（海外游戏服务器）、`EUNet_IP` 的 12 个 /16（交易所）

## 2026-09-25

全链路复查的低风险项。

- 停用 5 个宽泛 / 无效 keyword：`US_Domain` 的 `claude`（`Claude_Domain` 已同组完整收录）与 `backpack`（同文件已有 `backpack.app` / `backpack.exchange`）、`HK_Domain` 的 `backpack`、`UK_Domain` 的 `argent`（未在使用，命中 argentina）、`Direct_Domain` 的 `wb_ad`（含下划线恒不命中）
- B 站 / 爱奇艺国际版改走 Global TV：`ChinaMedia_Domain` 停用 7 条国际版条目（`bilibili.tv`、`biliintl.co/.com`、bstar 静态与 CDN），缺的补进 `GlobalMedia_Domain`；`GlobalMedia_Domain` 停用 `v.smtcdns.com/.net`（腾讯视频国内外共用）。**需配合 Openclash-Config 把 `ChinaMedia_Domain` 移到 `GlobalMedia_Domain` 之后**，否则 `ChinaMedia` 的 `bilibili` / `qiyi` keyword 与 `iqiyi.com` 后缀仍会先命中国际版；模拟确认调整后只有 9 个国际版域名改变去向
- **有意保留**（在用）：`JP_Domain` 的 `maya` / `globe` / `split`，`HK_Domain` 的 `chie` / `wechat`，`Game_Domain` 的 `telephony` / `fbsbx`
- 不改（设计取舍）：FINAL 走代理、官方来源的大 IP 段、`HDOBOXAds_Domain` 的 `doubleclick.net`、`Custom_Direct_Domain` 的 `jsdelivr.net`

## 2026-09-24（五）

- `Game_Domain`：`gcloudcs` 会同时命中国服腾讯游戏云 `gcloudcs.com`，收窄为海外端点 `hkgcloudcs.com` / `nagcloudcs.com`（依据 v2fly `tencent-games`）；国内端点交由 `GEOSITE,cn`（经 `geolocation-cn` → `tencent`）直连
- `Game_Domain`：`anticheatexpert` **有意保留** —— 国服与海外腾讯游戏共用该域名、无法区分，需要海外游戏可用。代价：国服游戏的反作弊流量也进 Game Platform 分组
- `PT_Domain` 停用 `sjtu.edu.cn` / `xauat6.edu.cn` 两条整域后缀：PT 分组切到代理时会把交大 jAccount / 邮箱 / VPN 等一并带走；PT 站本身已由 `pt.sjtu.edu.cn` / `pt.xauat6.edu.cn` 精确收录

## 2026-09-24（四）

全链路复查的中风险项，以及对（三）的部分回滚。

- 回滚（三）中的两处，恢复原状：`SG_Domain` 的 `cloudauth-device`（收窄依据是推测，没有抓包）；`EUNet_Domain` 的 `pushsdk` / `pushcloud` / `qq-os` / `we-api`。**约定：交易所 App 的推送、统计等 SDK 流量随 EUNet 走，保持出口一致，不按「跨平台共享服务」拆出**
- `EUNet_Domain` 停用 7 个常见词 keyword：`ether`（together / whether / netherlands）、`engage`、`coca`、`pave`、`tuyo`（途游 tuyoo.com）、`ramp`、`exactly`；后两个收窄为 `ramp.network`、`exact.ly`
- `Microsoft_Domain` 停用 `edgesuite.net`：Akamai 通用 CDN，非微软专属，截走了 `netflix.com.edgesuite.net`。Azure 系（`azureedge.net` 等）保留 —— 上游 `GEOSITE,microsoft` 已收录且同组，停用不改变行为
- `YouTube_Domain` 停用 `gvt1.com` / `gvt2.com`：Google 通用下载 / 更新 CDN，由 `GEOSITE,google` 交还 Google 分组

## 2026-09-24（三）

全链路复查的高风险项：排在 `China_Domain` / `GEOSITE,cn` 之前的列表把国内流量送去了海外节点。

- `TikTok_Domain` / `GlobalMedia_Domain` 停用 `snssdk.com`：字节国内域名（抖音 / 头条 / 西瓜），v2fly 上游归在 bytedance 而非 tiktok；TikTok 分组没有直连选项，国内 App 全走美国节点。现由 `ChinaMedia_Domain` 接管，国际版仍由 `isnssdk.com` 命中
- `EUNet_Domain` 停用 4 条国内基础设施：`volces`（火山引擎）、`tobsnssdk`（字节 toB SDK）、`log.aliyuncs.com`（阿里云日志）、`im.qcloud.com`（腾讯云 IM）。交易所主域名不受影响
- `Game_Domain` 停用 `DOMAIN-KEYWORD,adjust`：全体 App 共用的归因 SDK，且命中境内端点 `adjust.cn`；与 `UK_Domain` 的「跨平台共享服务」处理一致

## 2026-09-24（二）

清理 PT 相关的异组冲突（按 V2 规则链：`PT_Domain`[PT] → `PrivateTracker_Domain` / `Direct_Domain`[Global Direct]）。异组冲突 1657 → 1459。

- 停用 `PrivateTracker_Domain` 102 条、`Direct_Domain` 88 条与 `PT_Domain` 完全重复的 PT 站点：排在 PT 之后永不命中，PT 站点统一由 PT 分组管理，行为不变
- 停用 `PrivateTracker_Domain` 的 `DOMAIN-KEYWORD,torrent`：常见单词，把 `torrentkitty.tv` 等被墙站点截到直连
- `Direct_Domain` 停用 4 条外部列表收录、压过专属分组的规则：`blog.google` / `googletraveladservices.com` 交还 Google，`trip.com` 交还 HK_Domain（「旅行」），`icloud.com` 交还 Apple 分组
- `China_Domain` 的 `trip.com` 由 dedupe 恢复（不再与 Direct 同组冗余，仍被 HK_Domain 先命中，行为不变）
- 遗留：`Direct_Domain` 的 `ls.apple.com` 仍截走 `UK-wifi-call_Domain` 的地区检测端点 `gspe1-ssl.ls.apple.com`，需在 Openclash-Config 把 UK-wifi-call_Domain 移到 Direct_Domain 之前

## 2026-09-24

修复 `scripts/dedupe.py` 覆盖判定错误，并按 V2 规则链重新评估冗余。

- 判定修正：`DOMAIN-SUFFIX` 不再被同名 `DOMAIN` 判为已覆盖（盖不住子域）；`DOMAIN-KEYWORD` 只由更短的 keyword 覆盖，不再被同名 suffix 判为已覆盖
- 恢复被误停用的 12 条：`Apple_Domain` 推送 4 条（`push.apple.com` 等）、`Microsoft_Domain` 的 `microsoft`、`YouTube_Domain` 的 `youtube`、`Netflix_Domain` 的 `netflix.com.edgesuite.net`、`TikTok_Domain` 的 `musical.ly`、`Emby_Domain` 的 `emby.wtf`、`PT_Domain` 的 `tjupt.org`，以及 `ProxyGFWlist_Domain_1/3` 各 1 条（`Custom_Proxy_Domain` 已不再收录）
- 新停用 5 条：`JP_Domain` 4 条文件内冗余，`Direct_Domain` 的 `hdsky.me`（已被 `PrivateTracker_Domain` 同组命中）
- `--apply` 改为循环到不动点：恢复一条规则会重新遮蔽链上靠后的同名规则，单轮应用不一定收敛
- `SG_Domain` 的 `phantom` 是人工停用，改用 `# [已停用]` 标记 —— 借用脚本的 `# [已停用-冗余]` 会被自动恢复，且原因前只有一个空格，恢复时会把说明一起写进规则行

## 2026-09-12

配合模板把「地区专属」名单块上移到「泛分类 GeoSite」之前，宽泛 keyword 的误伤面随之扩大，逐条收敛为精确域名。

- `UKNet_Domain`：`osl` / `adjust` / `pusher` / `yuh` / `bitsa` / `pendo` 六条 DOMAIN-KEYWORD 换成对应 DOMAIN-SUFFIX
  - Adjust 补齐区域端点 `adjust.world` / `adjust.net.in` 与短链域 `adj.st`；`adjust.cn` 为境内端点，不收
  - Pusher 补 `pusherapp.com`（mt1 主集群的默认 host），只钉 `pusher.com` 会漏
- `SG_Domain`：`trae` → `trae.ai`（`trae.com.cn` 为国内站，不收）；`plasma` → `plasma.to`
- `SG_Domain`：停用 `keystone` / `keyst` / `ledger` / `phantom` 四条冗余 keyword，同文件已有对应 suffix
- `SG_Domain`：停用 `onelink` —— `onelink.me` 是 AppsFlyer 全体客户共用的深链域名，与 OneKey 无关

## 2026-09-05

- 构建脚本修复 yaml 注释归位：注释不再被抽到 `payload:` 之前，回到各自规则上方（97 个文件受影响）
- 构建 workflow 末尾新增 `repository_dispatch`，完成后通知 Openclash-Config 跑联网校验，防止改文件名或目录结构导致对方静默断链
- GitHub Actions 升级到 Node 24 运行时（`checkout@v6` / `setup-python@v6`）
- 新增 `scripts/dedupe.py`：读取配置仓库的产物 ini 还原规则链，做首命中模拟，识别冗余规则
- 变更记录改名为 `CHANGELOG.md`，长期约定拆分到 `docs/`
- 补充 `LICENSE`（MIT）与 `.gitignore`

## 2026-08-05 —— 规则库整理

规模：166 个规则集 / 81 个平台 / 26452 条规则。

- **修复规则集完全不生效**：配置引用的是纯文本 `.list`，而带更新间隔的 ruleset 会生成 rule-provider，`classical` behavior 要求 payload 是 YAML 数组。166 个 provider 全部加载为 0 条规则，长期被 GeoSite 兜底掩盖。新增 `rules/yaml/` 自动生成目录
- 修复 CRLF 换行（11 个文件）、逗号后多余空格（7 个文件）、IP 规则缺 `no-resolve`
- `GoogleVoice.list` 内容与文件名不符，已修正
- 停用 124 条规则（均保留为注释可恢复）：PROCESS-NAME 81 条、恒不生效 8 条、范围过宽 35 条
- 文件组织：合并同源文件，域名与 IP 强制成对，超长文件按 2500 条分片，统一命名规范与 header 格式
- 新增 `scripts/build.py` 与 `scripts/validate.py`，接入 GitHub Actions 自动构建

---

### 遗留事项（状态更新于 2026-09-25）

1. ~~**`AU_Domain` / `AU_IP` / `BR_Domain` / `BR_IP`** 为占位文件（0 条规则），待补充。~~ 部分完成：`AU_Domain` 7 条、`BR_Domain` 15 条；`AU_IP` / `BR_IP` 仍为占位。
2. ~~**`Others.list` 的 `DOMAIN-KEYWORD,ipinfo` 与 `Custom_Direct` 的 `ipinfo.io` 冲突**~~ 已结论：`ipinfo.io` 直连为**有意保留**（需要真实出口）。`Others_Domain` 的 keyword 已改为精确后缀，IP 查询服务由新增的 `IPCheck_Domain` 承接。
3. **`Download_Domain`** 停用 PROCESS-NAME 后仅剩 6 条域名关键词，可考虑补充下载站域名或停止引用。——仍有效
4. **IP 合并未执行**——`Amazon_IP`、`China_IP`（6894）为官方发布的精确段，做 /24→/16 合并会吞掉大量不属于它们的地址（AWS 的段尤其碎）。该策略适用于零散收集的 IP，不适用于官方段。——仍有效，作为长期约定

---
