# v0.6.0 兼容性验证

验证日期：2026-10-28。标准资源包只有一份，`skills/product-idea-research/` 是安装源。

## 实际验证范围

环境：macOS，Python 3.10.7，Node.js 25.8.0，Skills CLI 1.7.4。

| 检查 | 结果 | 能证明什么 |
| --- | --- | --- |
| Codex 项目级安装 | 通过，50个资源文件逐字节一致 | CLI 安装路由、目录和资源完整性 |
| Claude Code 项目级安装 | 通过，50个资源文件逐字节一致 | CLI 安装路由、目录和资源完整性 |
| Codex / Claude Code 全局安装路由 | 在隔离的测试用户目录通过，分别落入 `.agents/skills/` 与 `.claude/skills/` | `-g -a codex -a claude-code --copy` 的目录路由及完整复制 |
| 安装后的脚本 | 两个宿主目录各通过 init → validate → render | 安装资源足以生成 HTML、MD、JSON、分享 ZIP |
| 带目录 ZIP / Flat ZIP | 各50个文件，内容一一相同 | 两种布局仅目录层级有区别 |
| ZIP 可复现性 | 重复构建 SHA256 一致 | 同一源码可重建相同安装包 |
| 报告回归 | 46项通过 | 评分、未知态、证据引用、v1–v5渲染与分享边界等确定性行为 |
| 触发样例 | 26/26通过 | 固定语义规则样例，无模型调用；不是实测模型路由准确率 |
| 输出夹具 | 12/12通过 | 明确标注的 file-backed fixture 契约检查；不是市场研究或模型效果评测 |
| Yao基础检查、IR、编译与契约适配 | 通过，openai / claude / agent-skills / generic 四目标 | 静态格式与接口一致性，不证明四个宿主均已完整研究实跑 |
| README截图 | 3张实际研究页面截图，JPEG格式与SHA256记录在manifest | 展示已完成报告的阅读体验；不构成新增市场证据 |

全局安装测试仅在子 Node 进程中将 `os.homedir()` 映射到临时目录；没有改 `$HOME`、`$CODEX_HOME` 或真实用户配置。研究脚本烟测使用未研究的空白案例，未知不会转为零需求或入场结论。

公开仓库的远程安装检查与提交信息在发布时核对；不把本地安装替代远程发现检查。

## 尚未验证

- Claude Code、Cursor、Gemini CLI、OpenCode、GitHub Copilot 等宿主的完整联网研究、独立子代理编排和视觉验收；不能用安装器支持列表替代端到端验证。
- 各用户的 Agent Reach 后端、社交平台可达性、额度、登录态和付费权限。
- Windows / Linux 上的完整运行。Python脚本使用标准库，但本轮执行环境是macOS。
- 报告阅读时间的真人测试、长期采用率和外部模型基准。

## 作者工具的边界

本轮使用 Yao Meta Skill 进行作者侧检查，并运行了信任、Atlas、打包、安装模拟、升级比较、漂移、waiver和Review Studio。升级比较及包结构校验通过；本轮未录入任何虚构审批或运行遥测。

Yao的严格安装治理模拟仍缺少其专用的逐目标人工权限批准、权限执行记录及部分维护材料，Review Studio因此保留blocked/warning，不宣称全部治理门禁通过。这与上表已实测的Skills CLI安装是两套检查。分发包不伪造授权、不捆绑该维护系统；研究实际权限由各宿主控制，运行前按Skill指引预检。

## 对照依据

- [iphone-ui](https://github.com/1085995907ljh-hash/iphone-ui)：一套标准源、指定Agent的安装命令、完整资源分发、能力与安装验证分开。
- [Agent Skills规范](https://agentskills.io/specification)：标准目录、frontmatter和相对资源。
- [Skills CLI](https://github.com/vercel-labs/skills)、[Agent列表](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)：安装参数和宿主目录。
- [Claude Code Skills](https://code.claude.com/docs/en/skills)：个人/项目Skill与显式调用方式。

本包没有专门为每个Agent复制研究工作流。宿主变化只影响工具映射和不可用能力的披露，四章、证据与评分规则保持一致。
