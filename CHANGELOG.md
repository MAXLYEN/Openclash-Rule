# 更新记录

规则内容的更新与 [Openclash-Config](https://github.com/MAXLYEN/Openclash-Config) 模板的更新相互独立。

设计约定见 [docs/design-notes.md](docs/design-notes.md)，排查记录见 [docs/troubleshooting.md](docs/troubleshooting.md)。

---

## 2026-09-24（三）

全链路复查的高风险项：排在 `China_Domain` / `GEOSITE,cn` 之前的列表把国内流量送去了海外节点。

- `TikTok_Domain` / `GlobalMedia_Domain` 停用 `snssdk.com`：字节国内域名（抖音 / 头条 / 西瓜），v2fly 上游归在 bytedance 而非 tiktok；TikTok 分组没有直连选项，国内 App 全走美国节点。现由 `ChinaMedia_Domain` 接管，国际版仍由 `isnssdk.com` 命中
- `EUNet_Domain` 停用 8 条国内基础设施 / 通用词：`volces`（火山引擎）、`tobsnssdk`（字节 toB SDK）、`log.aliyuncs.com`（阿里云日志）、`im.qcloud.com`（腾讯云 IM）、`pushsdk`、`pushcloud`、`qq-os`、`we-api`。交易所主域名不受影响
- `SG_Domain`：`cloudauth-device` 会命中阿里云国内实人认证 `cloudauth-device.aliyuncs.com`，收窄为 `cloudauth-device.ap-`（亚太海外区域端点）
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
