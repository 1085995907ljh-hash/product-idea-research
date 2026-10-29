# Agent Skills 宿主适配

本包只有一套研究规则：标准 `SKILL.md` + 相对路径资源。Codex、Claude Code，以及支持 Agent Skills 的编码 Agent 共用它；不要求安装 Yao Meta Skill 才能运行。Yao 是作者维护工具。

## 定位资源与调用

- `<SKILL_DIR>` 指当前加载的 `product-idea-research` 完整目录。先定位它，再解析 `references/`、`scripts/`、`assets/`；不要从项目 cwd 猜路径。
- `<RUN_DIR>` 使用用户工作区内新的可写目录，不能放进已安装 Skill。不得覆盖旧研究。
- Codex 可显式使用 `$product-idea-research`；Claude Code 可使用 `/product-idea-research`。其他宿主用它支持的 Skill 调用或明确要求读取本包 `SKILL.md`。
- `agents/openai.yaml` 只是 Codex 展示信息；`agents/interface.yaml` 是维护元数据。其他宿主忽略即可，核心工作流不依赖这些文件。

## 按能力适配，不按品牌猜权限

| 能力 | 执行方式 | 不具备时 |
| --- | --- | --- |
| 文件与 Shell | 用当前工具读写；Python 3.10+ 运行标准库脚本 | 说明不能生成/校验文件，不冒称交付完整报告 |
| 公开网络研究 | 读取当前 Agent Reach Skill，运行 preflight，选择实际可用且已授权的后端；有本地 web-access 规则则遵守 | 保留 blocked/partial/unavailable，其他合法公开来源补查；不据此判市场没需求 |
| 新上下文子代理 | Codex 的 spawn_agent / Claude Code 的 Agent 或 Task / 宿主同类接口，均以当前工具定义为准；只发中性 brief | 顺序执行角色工作单，明确“上下文未隔离”；不要伪造多代理结论 |
| 浏览器 | 使用宿主批准的浏览器工具读动态内容、检查报告 | 静态结构校验可做；动态取证和视觉/下载检查标未完成，不冒称浏览器验收 |
| 报告预览 | 有右侧面板则打开；否则交付 HTML 路径和 MD/ZIP，可由用户本机浏览器打开 | 不依赖 Codex 专用 UI，不自动发布公网 |

总监始终留在主对话，不把整个 Skill 设为自动 fork。研究员只拥有各自 work/raw 子目录；报告由总监整合。各宿主均保持四章、六维评分、反证和未知处理不变。

## 完整安装与更新

Skills CLI 可从仓库的 `skills/product-idea-research/` 发现本包。手动安装也必须复制整个目录，不能只放 `SKILL.md`。Python 不需要 pip 依赖；安装器、网络后端及 Agent Reach 的依赖另行满足。不要自动改账号、Cookie、MCP、权限配置，或下载执行陌生脚本。

更新前比较同名目录的版本及自定义修改，再用当前安装器更新；不得覆盖旧研究运行目录。ZIP 有带目录和根级 `SKILL.md` 两种布局；选择宿主明确支持的格式，不能把所有产品都说成支持 ZIP 上传。

安装通过仅表示资源可发现/可加载。实际研究质量仍取决于模型、网络、渠道、上下文隔离及预算；不同宿主的完整研究结果不能由安装测试替代。
