# 设计约定

本文件是维护规则库时的查阅手册，记录长期有效的约定。
一次性的变更过程记录在 [../CHANGELOG.md](../CHANGELOG.md)，踩过的坑在 [troubleshooting.md](troubleshooting.md)。

配置侧（策略组、检索顺序、subconverter 行为）的约定在
[Openclash-Config/docs/design-notes.md](https://github.com/MAXLYEN/Openclash-Config/blob/main/docs/design-notes.md)。

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

---

## 与 Openclash-Config 的边界

- 本仓库只产出**规则内容**，不决定规则的先后顺序
- 一条规则是否冗余，取决于它在 `Openclash-Config` 的 ini 里被排在第几位 ——
  所以 `scripts/dedupe.py` 需要读取配置仓库的产物 ini 才能判断
- 改动本仓库的**文件名或目录结构**会让配置仓库的引用断链。构建 workflow 末尾
  会向 `Openclash-Config` 发 `repository_dispatch`，触发对方跑一次联网校验
