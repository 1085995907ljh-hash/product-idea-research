# v6：主 Agent 判断在前，全面研究在后

## v0.7.1：新报告默认六段式

新初始化的stress_test.presentation=investigator-six，执行[总监综合方法](director-synthesis.md)。同一v6结构向后兼容：没有presentation字段的0.7.0报告保持旧展示，不静默改写。

新综述固定六节：1）一句话结论、2）必须成立的前提、3）证据、4）最可能杀死它的假设、5）下一步最便宜的测试、6）可能更强的相邻方向。原案/目标留工作数据，投入建议及可展开辅助评分归第一节；不另列论点、投入、评分小节。其余三章深度保持。

新测试还须measures=task_completion/return_use/stated_intent/acquisition_response/actual_payment/technical_reliability，以及time_window、sample_definition、assistance和cannot_establish文本，说明时间、分母、主持提醒及不能证明什么。结构检查看字段，主Agent/挑战者检查指标是否真的对应行为，不能把填字段当有效实验。

adjacent_hypothesis可为null或{direction_id,summary,why_better,new_risk,missing_evidence}；只关联stance=explore的真实详细方向，仅已研究六节综述可用。它是未验证的相邻设想，允许需求证据很弱，但须解释如何回应原案失败机制、缺什么和新增风险。它不能代替原有adjacent的证据要求，也不能与同一方向同时标为推荐。

六节综述的adjacent还须关联stance=recommended的真实详细方向，避免综述叫推荐、详情却仍是探索；未设置presentation的旧v6保留历史校验。

render额外生成director-reply.md：六节聊天回复，第三节可附安全http(s)来源链接，不含工具日志或隐藏推理。HTML和research.md综述依然无链接，来源映射在市场等详细正文。研究ZIP白名单仍为research.json/research.md/sources.json。以下旧v0.7.0九段展示约定仅适用于未设置presentation的旧报告。

默认 schema_version=product-idea-research/v6，包版本0.7.1。继续复用v5深度层和四章目录，仅第一章改为“研究综述”。历史v1–v5不迁移，不改旧的评分或证据含义。

## 同源报告

research.json新增 stress_test，保留 briefing/executive、depth、六维评分、全部市场/社交/竞品和方向字段。兼容字段executive须与主判断一致，v6不重复展示旧三段概览。HTML/MD/ZIP同源；只有研究综述、市场调研、竞品、产品研究四章。综述全文无外链/引文ID，证据等级可显示；市场下“关键前提的证据”显示具体论断、等级理由、边界和可点击来源。

综述顺序：一句话结论 → 原案与目标 → 必须成立的前提 → 支持和反对 → 一个关键假设 → 下一步测试 → 有证据的更强相邻方向（可无） → 当前投入建议 → 辅助评分。顶部结论/关键假设/投入建议应能快速扫读；完整测试细节折叠。30–60秒和五分钟是编辑目标，不是经过用户测试的保证。总监评分与六项子分仍有短理由，未知不画成零分。

## stress_test 数据

- state：not_run / researched，未研究可以初始化空数组，不称完成。
- thesis：{statement, founder_goal, decision}。原案、人群/任务/形态/交换价值，用户期望和当前决定；推断显式说明。
- beliefs：3–5个{id, claim, category, status, support_evidence_ids, oppose_evidence_ids, disconfirmation:{searched,summary,source_ids}}。category为pain/behavior/feasibility/retention_payment/acquisition_competition，可合并；status为supported/mixed/unsupported/unknown，均非“已商业验证”。每条都实际查反证；查不到或受阻在summary写清，不能记为没有反证。
- bottleneck：唯一{belief_id, why, decision_if_true, decision_if_false}。只能引用本轮前提，不另造一个大风险列表。
- tests：通常1–2个{belief_id,method,observed_behavior,metric,pass_threshold,fail_threshold,inconclusive_rule,failure_action,resource_cap,selection_reason}。必须针对唯一关键假设；阈值为{operator:gte/lte,value:数字,unit:文本}，同一指标/单位，互不重叠，拒绝NaN/无穷和布尔值。门槛都是建议的事先决策规则，不能称已经通过或市场验证。
- 已足够否决且commitment.action=stop时允许tests=[]，但须no_test_reason。其他已研究报告需测试建议，不能无理由省略。
- adjacent：null或{direction_id,summary,evidence_ids}；必须链接详细方向及已核验A/B/C支持材料，若只有代理或推理可在产品研究写探索假设，但不能叫更强方向。
- commitment：{action:test/invest/hold/stop,summary,cap,escalation_condition}。当前该投入什么、上限是什么、什么事实允许升级。原案no_go必须stop；原案go不能配stop。停止指当前原案，不代替用户作不可逆财务决定。

## 证据等级不重写旧类型

顶层evidence保留type原有A–E分类，每条新增grade与grade_reason。type是旧主题/形态分类，grade是论断强度，二者独立。可加validated=true，仅当非D/E且fact、有已核验来源时结构上允许；仍需人工检查是否只验证了对应范围，不能把“有报价”说成“有人付款”。默认false，不要求任何前提被验证。

A行为（付费、迁移、签约、实际变通）；B强一手（过去行为访谈、产品/客户数据、真实定价、披露、反复一手抱怨）；C佐证（评论、从业者、论坛、案例）；D间接指标（Trends/市场报告/融资等）；E断言或推理。等级依论断而非平台；一条评论转述行为并不自动成为已观察付费。D/E永远不是验证。未核实来源不能支撑已核实事实。

## 详细研究作为分支

市场、竞品、产品研究保留v5详细数据和交互。每条分支结论要能关联原案前提，不用为了显示全面堆无关材料。产品研究方向允许0–5个，complete不再强制凑三个；无方向保留no_directions_reason。发现相邻方向不能覆盖原案分数/结论。历史v5的3–5要求仅用于历史渲染，不扩散到v6。

验收覆盖未知初始化、唯一关键假设、支持/反对引用、等级与旧type独立、代理证据不可冒充验证、无证据不荐相邻方向、测试门槛互斥、HTML/MD/ZIP一致、四章目录和1440/390布局。结构检查不能判断论断真实性或替代真实用户实验。
