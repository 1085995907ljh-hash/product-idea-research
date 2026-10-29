# product-idea-research · v0.6.0

给个人独立 AI 开发者的美国产品调研 Skill。输入一句 idea 或已有研究，得到明确建议、5分制判断和四章中文报告：研究概览、市场调研、竞品、产品研究。输出 HTML、Markdown、结构化 JSON 和分享 ZIP。

完整介绍、安装命令与真实报告截图见 [GitHub README](https://github.com/1085995907ljh-hash/product-idea-research#readme)。本目录是可独立安装的完整 Skill，不能只复制 `SKILL.md`。

## 使用

- Codex：`使用 $product-idea-research，研究这个想法：……`
- Claude Code：`/product-idea-research 研究这个想法：……`
- 其他 Agent Skills 宿主：按其接口调用，或让 Agent 读取本目录 `SKILL.md` 并执行。

支持模糊想法和完整 research。默认美国市场，平台按需求判断；报告推荐研究层 MVP 主攻点，不自动生成完整 PRD、UI 设计或开发代码。

运行前阅读 [宿主适配](references/agent-compatibility.md) 和 [访问规范](references/access.md)。需要 Python 3.10+、文件/Shell、公开联网能力，以及另行安装的 Agent Reach Skill 与可用后端。子代理和浏览器由宿主提供；不可用时如实披露，不把访问受阻当零需求。Yao 仅用于作者维护，不是使用依赖。

## 脚本

在本目录运行下面命令，或让 Agent 用本次加载目录的绝对路径执行：

```bash
python3 scripts/report.py init /path/to/my-research --title '产品名' --idea '原始想法'
python3 scripts/preflight.py --out /path/to/my-research/access.json
python3 scripts/report.py validate /path/to/my-research
python3 scripts/report.py render /path/to/my-research
python3 -m unittest discover -s tests -v
```

`init` 只生成研究骨架，不会联网替你完成研究。Agent 按规则取证填入 `research.json` 后再 validate/render。HTML 离线可读，MD/JSON 保留来源；分享 ZIP 不含 raw/work 或权限状态。旧 v1–v4 数据保留历史渲染。

评分权重：热度20%、竞争空间20%、具体缺口25%、时机10%、验证15%、个人投入10%。未知为 null，暂定分明确标记。无子代理则声明上下文未隔离；没有浏览器则不声称完成视觉验收。

许可保持 UNLICENSED。安装包不附第三方 Skill、账号、Cookie 或本机研究资料。
