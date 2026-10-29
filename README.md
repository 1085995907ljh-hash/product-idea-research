# Indie Idea Research

面向个人独立 AI 开发者的美国产品调研 Skill。输入一个 idea，获得有来源的市场、社交需求和竞品分析，以及明确的投入建议。

从一句产品想法或已有research开始，判断美国市场值不值得做。v0.5.0；总监派隔离研究员深入取证，简明主线与深度研究分层阅读：

1. **研究概览**：30–60秒讲清行/不行/观望、建议、更好方向和MVP；总分/5及六项短理由，无链接。
2. **市场调研**：领域/分类/演变，逐平台讨论与痛点、需求新旧及满足程度、规模/美国用户、多组关键词搜索趋势。
3. **竞品**：四象限、15–25款分类目录、头部/相似/新品重点、JTBD任务组功能、逐家口碑与竞争判断。
4. **产品研究**：3–5个不同任务方向，分别讲是什么/为谁做什么、痛点、差异与MVP、开发和维护成本、平台与技术依赖。

不再有“先验证什么”“依据与缺口”章节。重要反证和未知贴在相关结论旁；原帖、评论全集和证据链保留结构数据，不让读者读研究日志。

## 使用

仓库名为 `indie-idea-research`，Skill 调用名保持 `product-idea-research`。

### 在 Codex 中安装

```bash
git clone https://github.com/1085995907ljh-hash/indie-idea-research.git
mkdir -p ~/.codex/skills
cp -R indie-idea-research/skills/product-idea-research ~/.codex/skills/
```

已有同名 Skill 时请先比较版本，避免覆盖自己的修改。也可解压 [v0.5.0 安装包](dist/product-idea-research-v0.5.0.zip)，将其中 `product-idea-research` 文件夹放到宿主 Skill 目录。

需要 Python 3.10+、宿主提供的公开网络访问能力，以及另行安装的 Agent Reach Skill；本仓库不捆绑第三方 Skill、账号或凭据。支持子代理的宿主可运行隔离研究员；不支持时会明确披露限制。

安装后打开新会话说：

> 使用 $product-idea-research，研究这个想法：……

四类角色：社交需求、竞品格局、市场/平台、功能/口碑，使用中性brief和隔离上下文；总监交叉判断，独立挑战者检查。未知不等于零，简单好做不等于市场机会。六维权重保持热度20/竞争20/缺口25/时机10/验证15/投入10；无依据的项为null，总分标暂定。宿主无代理能力时如实声明。

## 输出与运行

research.json为v5单一内容源，生成report.html、research.md和research.zip。HTML离线可读，四章子目录、真实图标/四象限、功能矩阵、Trends切换、关键来源可点，概览无链接。MD保留相同四部分，JSON保存完整取证。ZIP只含JSON/MD/来源，raw/work/权限状态不进分享包。v1–v4保留历史渲染。

Python3.10+标准库。按当前agent-reach、web-access与宿主权限访问公开资料，Skill本身不授予账号/付费/提权许可；受阻如实记录。工具和作者门禁不污染产品报告。

```bash
python3 skills/product-idea-research/scripts/report.py init ./my-research --title '产品名' --idea '想法'
python3 skills/product-idea-research/scripts/preflight.py --out ./my-research/access.json
python3 skills/product-idea-research/scripts/report.py validate ./my-research
python3 skills/product-idea-research/scripts/report.py render ./my-research
python3 -m unittest discover -s skills/product-idea-research/tests -v
```

Yao Meta Skill维护，契约见references/depth-contract.md与briefing-contract.md。五分钟是编辑目标，结构/渲染测试不是实测用户阅读时间或市场验证。只做前期产品调研；完整MVP PRD、UI设计、详细技术方案和开发属于后续独立任务。不修改旧产品系统，不自动发布GitHub；许可保持UNLICENSED。

## 示例与维护

[阅读演示](examples/reading-demo/report.html) 使用明确标注的合成数据，展示报告结构与交互，不是市场研究结论。真实研究运行目录、原始社交数据和本机审计日志不包含在此仓库。

运行 `python3 scripts/build_release.py` 可从当前源码重新生成安装包。公开可见不代表开源授权；当前版本保持 `UNLICENSED`，尚未授予再分发或修改许可。
