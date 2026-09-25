# 更新记录

规则内容的更新与 [Openclash-Config](https://github.com/MAXLYEN/Openclash-Config) 模板的更新相互独立。

设计约定见 [docs/design-notes.md](docs/design-notes.md)，排查记录见 [docs/troubleshooting.md](docs/troubleshooting.md)。

---

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

## 六、遗留事项

1. **`AU_Domain` / `AU_IP` / `BR_Domain` / `BR_IP`** 为占位文件（0 条规则），待补充。
2. **`Others.list` 的 `DOMAIN-KEYWORD,ipinfo` 与 `Custom_Direct` 的 `ipinfo.io` 冲突**——模板中 Custom_Direct 位置靠前，ipinfo.io 走直连。若用于检测节点出口 IP，看到的将是真实出口而非节点 IP。
3. **`Download.list`** 停用 PROCESS-NAME 后仅剩 6 条域名关键词，可考虑补充下载站域名或停止引用。
4. **IP 合并未执行**——`Amazon_IP`（1802）、`China_IP`（6894）为官方发布的精确段，做 /24→/16 合并会吞掉大量不属于它们的地址（AWS 的段尤其碎）。该策略适用于零散收集的 IP，不适用于官方段。

---
