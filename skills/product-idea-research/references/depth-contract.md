# v5：简明概览，深入研究

默认schema_version=product-idea-research/v5。沿用v3证据层与v4四章核心，见deep-data-contract.md和briefing-contract.md；本文覆盖v4展示上限和阅读策略。v1–v4仍按原合同渲染，不静默重排/重算。评分公式/权重不变。research.json同源生成离线HTML、Markdown和ZIP；分享ZIP仅含research.json/research.md/sources.json，raw/work不进入。

## 四章与核心层

四个一级章节固定：研究概览、市场调研、竞品、产品研究。sections块沿v4，renderer插入深度子目录。概览仍无链接/编号、最多900字符、评分理由每项最多90字符；四象限最多12点，不代表份额或质量。重点最多12款、功能最多20项、展示评价最多80条，不要求填满。目录按任务覆盖全景，四象限只选代表。

## briefing.depth

所有source_ids必须存在；post/competitor/feature/review/direction ID指向证据层真实记录，不在展示层另造事实。

### market

- social_platforms：[{id,label,state,summary,pain,opportunity,post_ids,source_ids}]。逐平台说明讨论/痛点/现办法/机会，post_ids只能引用该平台。状态与业务判断分开；30/90天与历史、用户与宣传分开。
- social_findings：[{title,need,newness,opportunity,avoid,source_ids}]。需求→新旧→满足程度→可做/不值得做。没有讨论不等于无需求。
- keyword_groups：[{id,title,intent,keywords,summary,source_ids}]。通常2–4组、8–15词，话题/问题、方案、产品词分开，每组最多5词；不足不造数据。id对应trends.group，keywords列全该组词。按组/窗口/关键词切换。

Trends实际点保存到trends。window/group/geo/category/search_type/granularity为合线边界。默认12月，能选30/90天；排除污染词须说明且可恢复；低量0不是零需求，partial不连线。不同组/窗口的指数不能相除算增长，话题热不是App购买热。MD保留各组判断/口径/来源，完整点位留JSON。

### competition

- catalog_groups：[{id,title,description,competitor_ids,source_ids}]。覆盖全目录，按用户任务/方向分类，允许多归属；通常15–25款，不机械凑数。
- selection：[{competitor_id,roles,reason,source_ids}]。逐一覆盖重点；roles为leader/similar/new/adjacent，可重叠。leader只能表达已核验口径，例如样本内评分数领先，不能冒称全球头部/下载量。
- feature_groups：[{id,title,job,feature_ids,takeaway,source_ids}]。覆盖所选功能，以JTBD任务链分组，记录→理解→行动/回看，每组矩阵附差异价值。官网未写只能unknown，声明不是实测；无用户研究不编Kano重要性或功能权重。
- product_reviews：[{competitor_id,summary,positive,negative,judgment,review_ids,state,source_ids}]。逐一覆盖重点，positive/negative为忠实概括文本数组，review_ids只能属于本产品。summary写文字样本量/日期/版本/排序偏差，总评分数不是文字量。无评论仍有记录，状态unknown/unavailable，不强凑正负。judgment说明价值/摩擦/解决程度/竞争机会。

功能与口碑是独立小节；逐家评论不混成大池。好差评选择不代表发生比例，旧差评不当现版本缺陷。无收入/留存不判增长。competition_judgment最后回答能/有条件/不能/未知及我们的优劣势。

### directions

[{direction_id,description,pain,better_because,cost:{level,build,ongoing},feasibility:{verdict,summary,dependencies},source_ids}]，与顶层directions一一对应。通常3–5个不同任务的方向；证据不足可更少并解释，不换名凑数。description说明是什么/干什么，顶层direction提供人群/MVP/现有替代/剩余差异。cost.level为low/medium/high/unknown，build/ongoing为文本，区分开发/持续投入；feasibility.verdict为feasible/conditional/not_feasible/unknown，dependencies为文本数组。技术能写不等于商业成立。

平台/口碑state允许available/partial/blocked/unavailable/not_run/unknown，真实实测才用verified。未研究初始化可空，真实complete报告的方向为3–5个；不足则保持partial并解释，不以状态凑数。

## 阅读和验收

概览30–60秒、主线约五分钟是设计目标，不声称实测。详细市场/竞品按子目录深入阅读，不设全文字数硬上限；每小节先判断，关键限制就地可见，长细节/来源可折叠。1440/390检查目录、概览无链接、分类/重点、分组矩阵、逐产品口碑、方向成本技术、趋势组/窗口/词、局部横滑、MD/ZIP下载字节一致，保留v1–v4烟测。结构视觉校验不证明商业或AI效果。
