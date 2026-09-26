# 编程模型网站与 API 分流规格

更新：2026-09-26。范围以 [Artificial Analysis Coding Agent Index](https://artificialanalysis.ai/zh/agents/coding-agents) 展示的厂商为基线，补充对应编程智能体的官方站点与 API。规则匹配的是 DNS 主机名；URL 路径、模型名称和登录账号不参与匹配。`rules/list/` 是源文件，`rules/yaml/` 是生成产物。

## 地区选择

| 厂商 / 产品 | 网站与 API 主机名（子域由后缀规则覆盖） | 当前出口 | 依据 |
|---|---|---|---|
| OpenAI / Codex | `openai.com`、`chatgpt.com`、`chat.com`、`api.openai.com` | ChatGPT | [ChatGPT 支持地区](https://help.openai.com/en/articles/7947663-chatgpt-supported-countries)、[API 支持地区](https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories)、[Codex 网络域名](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)；美国在支持列表内 |
| Anthropic / Claude Code | `claude.ai`、`claude.com`、`api.anthropic.com`、Claude MCP 独立域 | USNet | [Claude 支持地区](https://support.claude.com/en/articles/8461763-where-can-i-access-claude)；美国出口 |
| Google / Gemini、Antigravity、Jules | `gemini.google.com`、`aistudio.google.com`、`generativelanguage.googleapis.com`、`cloudaicompanion.googleapis.com`、`cloudcode-pa.googleapis.com` 等 | USNet | [Gemini API/AI Studio 可用地区](https://ai.google.dev/gemini-api/docs/available-regions)、[Code Assist 接口](https://developers.google.com/gemini-code-assist/docs/set-up-gemini-standard-enterprise)；美国出口 |
| xAI / Grok | `x.ai`（含 `api.x.ai`、`management-api.x.ai`、`us.api.x.ai`）、`grok.com` | USNet | [官方 API 主机名](https://docs.x.ai/developers/rest-api-reference/inference)、[地区端点](https://docs.x.ai/developers/advanced-api-usage/regions)；US 端点是服务方的数据处理选项，USNet 代理本身不等于该保证 |
| Meta / Muse、Llama、Facebook、Instagram、WhatsApp、Threads、Messenger、Oculus | `meta.ai`（含 `dev.meta.ai`、`api.meta.ai`）、`meta.com`、`llama.com` 与各产品一方主域 | USNet | [Meta Model API 主机名](https://dev.meta.ai/docs/overview)、[API 地区说明](https://dev.meta.ai/help/accounts-and-login/supported-countries)、[Meta geosite 域名参考](https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/meta.list)；美国出口 |
| Cognition / Devin、Windsurf；Cursor | `devin.ai`（含 `api.devin.ai`）、`cognition.com`、`windsurf.com`、`codeium.com`（含 `server.codeium.com`）、`cursor.com`（含 `api.cursor.com`）、`cursorapi.com`、`cursorvm.com`、`accounts.spacex.ai` | USNet | [Devin API](https://docs.devin.ai/api-reference/authentication)、[Windsurf API](https://docs.windsurf.com/de/windsurf/accounts/api-reference/introduction)、[Cursor 登录域名公告](https://cursor.com/help/troubleshooting/sign-in-domains)；美国出口是本规则库的选路偏好，不是厂商公布的唯一可用地区 |
| Z.ai / GLM 国际平台 | `z.ai`（含 `api.z.ai`） | USNet | [Z.ai 与国内 BigModel 两套端点](https://zcode.z.ai/en/docs/configuration)；美国是本库的国际站选路偏好 |
| Moonshot / Kimi 国际平台 | `moonshot.ai`（含 `api.moonshot.ai`）、`kimi.ai` | USNet | [Kimi Code 国际 API](https://moonshotai.github.io/kimi-code/en/configuration/providers)；国际端点与国内端点区分 |
| StepFun / 阶跃星辰、Step Code | `stepfun.com`（含 `platform.stepfun.com`、`studio.stepfun.com`、`api.stepfun.com`、`static-openapi.stepfun.com`）→ Global Direct；`stepfun.ai`（含 `platform.stepfun.ai`、`studio.stepfun.ai`、`api.stepfun.ai`）→ USNet | 按中国站 / 国际站区分 | [官方两站说明](https://www.stepfun.com/step-3.7-flash)、[中国站 API](https://platform.stepfun.com/)、[国际站 API](https://platform.stepfun.ai/)；USNet 是本库对国际站的出口偏好，不代表官方要求美国来源 IP |
| DeepSeek、BigModel/GLM 国内平台、Kimi 国内站、Qwen 聊天 | `deepseek.com`、`bigmodel.cn`、`kimi.com`（含 `api.kimi.com`）、`moonshot.cn`、`qwen.ai`、`qianwenai.com` | Global Direct | [DeepSeek API](https://api-docs.deepseek.com/guides/harness)、[BigModel 国内 API](https://zcode.z.ai/en/docs/configuration)、[Kimi 产品](https://www.kimi.com/products/download)、[Qwen 官方站](https://chat.qwen.ai/chat)；这些是一方国内站点或国内服务入口 |
| 阿里云百炼 / Qwen API | `dashscope.aliyuncs.com`、`*.cn-beijing.maas.aliyuncs.com` → Global Direct；`dashscope-intl.aliyuncs.com`、`*.ap-southeast-1.maas.aliyuncs.com` → SGNet；`dashscope-us.aliyuncs.com`、`*.us-east-1.maas.aliyuncs.com` → USNet；`*.cn-hongkong.maas.aliyuncs.com`、`cn-hongkong.dashscope.aliyuncs.com` → Proxy；`*.ap-northeast-1.maas.aliyuncs.com` → JPNet；`*.eu-central-1.maas.aliyuncs.com` → EUNet | 按 API 主机名对应地区 | [百炼全部地域及接入域名](https://help.aliyun.com/zh/model-studio/regions/)；各地域 API Key、模型列表互不通用 |
| GitHub Copilot | `githubcopilot.com`；`github.com`、`githubusercontent.com` 已在 GitHub 规则内 | GitHub | [GitHub 官方网络域名清单](https://docs.github.com/en/copilot/reference/copilot-allowlist-reference)；不把 GitHub 全站转成 USNet |

地区出口仅影响请求来源 IP，不保证账号、付款方式、功能或模型在该地区开放。厂商的支持地区可能变化，新增独立域名需依据官方文档或连接日志再收录。共享登录、遥测、云存储和 CDN 主域不按单个 AI 厂商一概改路由，避免影响其他应用。

## 首命中与待配合项

V2 配置先匹配 OpenAI、Claude、Gemini，随后匹配 GitHub、各地区规则，再匹配通用 AI/社交 geosite。`Game_Domain` 原有 `fbsbx` 关键字会先于 `US_Domain` 命中，现已停用，交由 Meta 的 `fbsbx.com` / `fbsbx.net` 后缀规则匹配。

直接用 IP 连接、没有可用域名元数据的 Meta 流量需要在 Openclash-Config 源配置中将 `GEOIP,facebook` 指向 `USNet`。配置源文件应独立提交，由云端构建并发布 `dist`；仅有本仓库的域名规则无法覆盖这种连接。
