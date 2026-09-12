# 更新记录

规则内容的更新与 [Openclash-Config](https://github.com/MAXLYEN/Openclash-Config) 模板的更新相互独立。

设计约定见 [docs/design-notes.md](docs/design-notes.md)，排查记录见 [docs/troubleshooting.md](docs/troubleshooting.md)。

---

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
