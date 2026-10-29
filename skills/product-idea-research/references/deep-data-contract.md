# v3 深度数据契约

schema_version=product-idea-research/v3，保留v2六章、六维评分和方向。v1/v2历史读取不变，新init默认v3。报告脚本把下列结构转成同一组正文blocks，HTML/Markdown相同；原始输入不写回。不得只写自由段落跳过这些对象。未知对象也保留状态与缺口。

## social_research

对象含summary(文本)、platforms/pains/posts(数组)。

platforms每项：id/name/status(available/partial/blocked/not_run)/query_scope/time_range/discussion/assessment/limitation/source_ids。所有文本非空；受阻允许空引用，不能称没有讨论。

posts每项：id/platform_id/author_key/published_at(YYYY-MM-DD或null)/region/state(verified/unverified)/query_origin(need/brand/other)/behavior(problem/current_use/recommendation/switch/reject/creator/promotion)/context/quote(文本或null)/brand_mentions(competitor ID数组)/source_ids。state=verified必须已核实来源；quote仅verified可用。作者key用于去重，不暴露隐私。未核实索引线索不是完整原帖。

pains每项：id/name/audience/situation/current_workaround/problem/consequence/recurrence/counterevidence/status(recurring/signal/unknown)/post_ids/source_ids。recurring须至少两位不同作者的verified且非creator/promotion帖子；孤例为signal。未知可以空post_ids，不能因此宣称无需求。

## need_assessment

对象：classification(new_task/new_context/new_solution/mature/unknown)、novelty_reason、demand_summary、existing_solutions、satisfaction、remaining_gap、original_action、source_ids。各文本非空。分类是研究判断；新能力不等于新需求。original_action解释继续/收窄/不建议/补证据，后续机会表同时展示原案和相邻方向。

## competitors 的v3扩展

每项在v2 id/name/kind/summary/pricing/limitation/source_ids上增加positioning、audience(非空文本)、category_ids、official_keywords、user_keywords、strengths、weaknesses(文本数组)。未知直接写未核实，不臆造用户关键词；category_ids引用下述categories。保留人工替代，零新增软件费用不等于零时间成本。

## competitive_analysis

categories：[{id,name,description,competitor_ids,source_ids}]，ID与competitor.category_ids双向一致。一款可跨类。

feature_competitor_ids：本次重点比较对手ID，通常3–5款，取决实际资料。

features：[{id,name,cells:[{competitor_id,state(yes/partial/no/unknown),basis,source_ids}]}]。每行恰好覆盖feature_competitor_ids，不重复。非unknown格必须有已核实来源；no明确证据不是官网没写，unknown不能编有/没有。通常5–8项决定性功能，不机械配额。

reviews：[{id,competitor_id,rating(1–5整数),published_at(YYYY-MM-DD或null),version(文本或null),summary,quote(文本或null),source_ids}]。摘要非空、引用已核实来源。来源是精选/全量/官网证言需在coverage说明；quote遵守引用限额。

review_coverage：[{competitor_id,scope,time_range,limitation,source_ids}]。样本总数、4–5星/1–3星数量由reviews按产品计算，不手填比例；取得0条也写原因。近期数量由真实日期判断，不造历史基线。

review_themes：[{id,sentiment(positive/negative),theme,task,impact,current_status(unresolved/resolved/unknown),assessment,competitor_ids,review_ids,source_ids}]。review_ids须存在且产品在competitor_ids内；positive只能指4–5星，negative只能指1–3星。current_status对于好评可unknown并在assessment说明；团队回复不能当修复验证。

mindshare对象：status(measured/insufficient)、summary、eligible_post_ids、limitation。measured的每个post必须verified、query_origin=need、behavior为problem/current_use/recommendation/switch/reject且作者可去重。denominator由这些posts的独立author_key计算，包含未提品牌者；分子按该集合中提及每个注册竞品的独立作者计算。研究者不能手填比例。insufficient时eligible_post_ids=[]，不显示占比。多个品牌可被同一作者提及，不相加100%；不是市场份额。

## 方向与来源

v3每个direction增加pain_ids、competitor_ids、existing_alternatives、remaining_gap。ID必须存在；recommended须至少关联一个有verified帖子支持的痛点、一个已核实竞品/人工替代，且source_ids至少有一条已核实来源。其余v2约束保留。v3允许directions=[]，但须no_directions_reason非空，不能为满足格式造方向。

所有引用、分类、功能、痛点、评论、方向ID唯一/有效。缺证据保留空数组和具体未知说明，不能用fixture填真实报告。v3的supported热度/缺口仍需总监对证，结构校验不证明真实或代表性。

## 正文展开

signals自动生成：不同平台在讨论什么→用户痛点与现有办法→新旧需求与满足程度→哪些方向值得试/不建议→代表讨论明细(折叠)。

competition自动生成：按任务划分的竞品→定位/关键词/优势劣势→关键功能差异→好评/差评主题→样本品牌提及→评价覆盖及评论明细(折叠)，随后保留可筛选竞品清单。

通用table块可有row_source_ids，与rows等长，每行引用有效source；HTML在该行显示链接、Markdown在该行附同样引用。通用块可collapsed=true且title非空；正文渲染details，目录点击先展开。折叠不能隐藏决定性反证。
