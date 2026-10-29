# 输出契约 v3：给独立开发者的机会判断

历史格式参考。当前默认生成v4四部分简报，见briefing-contract.md；v4继承下列评分及深度证据规则，但不沿用六章正文、独立方向章和附录目录。

research.json 是唯一内容源。脚本生成 research.md、report.html、research.zip；ZIP 只含 research.json、research.md、sources.json，不含 raw/、access.json 和内部协作记录。历史 v1 报告仍能验证和渲染，不能用新权重重新解释旧分数。

新研究默认product-idea-research/v3，使用下列v2基础并加上[深度数据契约](deep-data-contract.md)的social_research、need_assessment、competitive_analysis与方向/竞品扩展。v2仍按原格式渲染，不能把缺少新字段的旧报告冒充完整v3研究。

## 读完第一屏应知道什么

原始 idea 值几分；建议继续、缩小方向还是放弃；优先服务谁、MVP 主攻什么；先做哪个低成本验证。最多三条理由。建议是研究判断，不是成功概率或承诺。

## v2 数据结构

沿用 v1 的 title/date/scope/idea/fixture/status/conclusion/sources/evidence/sections/competitors/trends/glossary。schema_version 改为 product-idea-research/v2。新增 decision 和 directions。所有内容用纯文本，链接经 source_ids 生成，不能插入 HTML。

conclusion：verdict 为 go/conditional/no_go；summary 是原始 idea 的总体判断；reasons 最多三条。status 为 complete/partial，表示研究覆盖。date 为用户所在日期；source.accessed_at 保留实际核验时间，不因重排报告而更新。

decision：recommendation、mvp_focus、main_risk、next_step 为非空文本；source_ids 引用建议依据。即使不建议入场，也说明值得验证的相邻方向或为什么暂时没有。

sections 恰好六章，顺序如下；每章含 id/title/status/summary/blocks，status 为 complete/partial/not_run：

| id | 章节 | 深度 |
|---|---|---|
| signals | 需求与近期话题 | 重点：跨平台讨论、痛点、新旧需求/满足程度、机会取舍 |
| market | 市场规模与走势 | 重点，说明可观察的市场边界 |
| competition | 竞品格局与用户评价 | 重点：分类、清单、定位/功能/好差评/自然提及与竞争结论 |
| environment | 外部环境与平台 | 重点，只写影响入场的变化和约束 |
| validation | 先验证什么 | 简短，低投入检验关键假设 |
| limitations | 依据与缺口 | 简短，哪些结论还不稳 |

blocks 继续支持 paragraph(text)、list(items)、table(title/headers/rows)，均含 source_ids。table 每行长度等于 headers。每章和 block 可有 source_ids；事实必须有已核验来源。搜索兴趣走势由 trends 独立生成，紧邻市场章，不放到附录。

## 六维评分

scorecard 恰好包含以下六维，每行：dimension、value、certainty、reason、source_ids。value 为 1–5 或 null；certainty 为 supported/inferred/unknown。null 必须 unknown；非 null 必须引用已核验来源。supported 表示有直接匹配的证据，inferred 表示从有限证据推断，不能伪装成已证实。

| dimension | 名称 | 权重 | 高分含义 |
|---|---|---:|---|
| attention | 近期需求与话题热度 | 20% | 近期有多个独立用户主动表达，且有增长迹象 |
| competition | 入场拥挤程度 | 20% | 有需求验证，但玩家不拥挤、未见强壁垒 |
| gap | 可抓住的具体缺口 | 25% | 有反复出现且现有产品尚未解决的问题 |
| timing | 现在入场的时机 | 10% | 有具体变化使此刻比过去更适合进入 |
| validation | 低成本验证难度 | 15% | 很快能用小测试推翻或支持核心假设 |
| solo_cost | 独立开发投入 | 10% | 一个人能以较少资源做出核心价值 |

各维始终高分更有利。value 为 null 时，保留 null，计算总分临时按中性 2.5 占位，醒目标记“暂定”并列出占位项；绝不能解释成已有中等需求。总分一位小数 /5；不用星级暗示精度。证据把握单独计算：supported=1，inferred=0.5，unknown=0，按同权重加权，>=0.75 高、>=0.4 中、否则低。这是证据覆盖的描述，不是统计置信度。

总分标签按未四舍五入的值：>=3.6 优先验证；>=3.0 小成本试；>=2.3 先改方向；其余不建议入场。competition或gap未知时，标签为“证据不足，先补关键证据”；否则证据把握低于0.4时显示“证据不足，先验证假设”。已核实 hard_vetoes 或 no_go 的结论优先覆盖标签为“不建议按原方案入场”，但不偷偷改变分数。旧版“没有付费证据就封顶”的规则不用于 v2；早期研究应诚实说明付费未知。

v2 的 directions 为 1–3 个相邻方向；v3 允许零个并说明 no_directions_reason。每项包含 id/name/stance/target_user/change/mvp_focus/why/first_test/main_risk/source_ids/scorecard，v3 再关联痛点与竞品（见深度数据契约）。stance 为 recommended/explore/avoid；最多一个 recommended，不强迫出现。scorecard 使用同六维和权重。缩小功能可以改善验证和投入分，不能凭空抬高市场热度或竞争分；方向间变化必须写明理由。directions 是切口建议，不是完整 PRD 或技术方案。

computed_score 是渲染器的计算结果，不写回 research.json：value、label、provisional、unknown_dimensions、confidence（high/medium/low）、confidence_value、reason。computed_directions 为 [{id,score:同结构}]。网页和 Markdown 使用同一结果。

## 证据与限制

sources：id/title/url/status(verified/unverified)/accessed_at/published_at；只允许 http/https。evidence：id/type(A–E)/state(fact/estimate/hypothesis/unverified/inference)/claim/source_ids/limitation，可选 quote。quote 只能用于已核验原文。事实须引用 verified 来源。竞品沿用 id/name/kind(direct/indirect/manual)/summary/pricing/limitation/source_ids。商店套餐不等于用户付费，不以评论数推导份额、收入或垄断。

hard_vetoes 为 [{reason,source_ids}]，必须有已核验依据且结论 no_go；访问失败不构成否决。payment_evidence_ids 保留兼容，引用真实付费依据，非套餐价格。

trends：keyword/group/window/geo/reason/source_ids/points；点为 date/value(0–100 或 null)/partial。未完成点不连线，缺点不补零。保留地区、时间窗、搜索词或 Topic、类别、搜索类型和粒度；不同归一化窗口不能直接比较增长率。拿不到数据就空数组并明确缺口。

## 阅读与交付

先展示研究概览、方向建议和 MVP 主攻点，再展示六章及搜索兴趣走势。需求与竞品两章按深度契约展开；完整帖子/评论、证据明细、评分依据、术语和来源默认折叠。正文以读懂判断为准，不为字数删关键反证，也不把原始日志全铺开。概览只留三个决定性理由，数量和日期如实呈现。

目录按章分组并保留子目录。链接可点击，窄屏表格可横滑，正文不横溢；MD/HTML 判断一致，下载文件与磁盘一致；ZIP 不含内部协作和原始私密文件。validate 只检查结构，不证明事实。不得用 demo/fixture 填补真实调研。
