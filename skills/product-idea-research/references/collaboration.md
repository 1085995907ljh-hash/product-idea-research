# 总监派工协议 v0.5

总监负责问题、比较、评分和报告；四种研究员负责事实。spawn_agent使用fork_turns="none"，只传中性brief和角色工作单，不传旧结论、分数或“证明方向成立”。共享目录不代表可读其他角色结果。不能隔离的宿主声明“上下文未隔离”。

第一批最多三人并行：社交需求、竞品格局、市场与平台。事实包完成后启用新的功能与口碑研究员，只传必要事实和待核验问题，不传总监偏好。最后独立挑战者审查。研究员不写research.json、不打整体分、不外发、不购买；只拥有自己的work/raw目录，明确“你不是独自在目录，不撤销别人编辑”。

## 中性brief

work/brief.json含idea原文、market=US、platform、audience、constraints、as_of、user_materials、questions。用户猜测标user_hypothesis。可以读本Skill及访问/证据规范，不读未经授权的历史判断。工作单明确ownership、questions、time_windows、outputs、stop_condition、round。

## 四种事实包

### 社交需求 SD

所有权work/social-demand/与raw/social-demand/。按deep-research.md从问题表达、现办法、选择/放弃挖不同平台，争取三种不同性质渠道，不机械凑数。交平台覆盖、帖子/评论、痛点聚类、行为、反证、30/90天及历史对照。作者去重、地区不推定、摘要不当原文；提供新旧需求线索，不给全案分数。

### 竞品格局 CL

所有权work/competitive-landscape/与raw/competitive-landscape/。用自然任务词发现通常15–25款产品及人工替代，分类且可多归属。挑8–10款重点：可核验头部/高评分数、最相似、近期首发必须各有覆盖或解释缺失。核验定位、人群、关键词、功能、价格周期、首发/更新；交分类地图、逐款选择角色/理由、功能草表和待复核问题。自然提及与品牌检索分开，不以评分数造份额。及时交首版事实供后续核验，勿让各角色重复全量采集。

### 市场与平台 MP

所有权work/market-platform/与raw/market-platform/。交所属领域与官方分类、细分玩家/样本演变、市场规模边界、美国用户习惯/心理的一手依据、美国Trends30/90天/12月原始点/意图、时机、影响入场的平台规则、核心承诺可实现性和个人投入构成。普通技术可用不等于AI效果可用；成本无预算依据不报精确金额/工期。历史数据保留时间；无可靠细分不乘假比例。不得扩成架构、合规全审或PRD。

### 功能与口碑 RV

所有权work/product-validation/与raw/product-validation/。输入必要事实包、重点对手及争议功能/痛点，独立核验。功能按用户任务链分组，交yes/partial/no/unknown及逐格依据和组内差异判断；官方声明与实测分开。口碑单独逐家覆盖所有重点：总评分/评分数、文字样本量/日期/版本/排序偏差、好评价值、差评摩擦、现版本/他品解决情况、竞争含义。近半年优先，历史说明时间；团队回复不当修复证明。无评论/未安装写缺口，不凑正负或以零差评证明优秀。

## 统一事实包

每角色输出work/<role>/round-1.json及summary.md：role/round/coverage/scope/sources/findings/missing/decisive_questions；再附平台/posts/pains、分类/competitors/features、market/trends或reviews/review_themes等。来源前缀SD-/CL-/MP-/RV-。发现含claim、state(fact/estimate/hypothesis/unverified/inference)、source_ids、opposing_source_ids、limitation、decision_impact。访问状态available/partial/blocked/unavailable/not_configured不代替业务判断。

保存查询范围、实际时间、原始出处和短摘录，遵守引用限制。合并ID保留provenance，同作者/转载/评论不重复计数。原始材料不默认进分享包。

## 总监汇总与定向补查

依“需求存在→新旧性质→已怎样满足→剩余缺口→可进入切口”汇总。决定性问题表含问题、支持/反对证据、影响哪项分数/方向、角色与停止条件。最多两轮广泛研究；补查不附期待答案。新输入可开迭代但保留旧快照。

独立挑战者只收中性brief、证据和拟定报告，检查痛点匹配、竞品已解决、好差评平衡、热闹与需求区别、差异是否值得迁移、自然提及分母、同尺评分及MVP过大。输出issue/evidence_ids/impact/suggested_fix，不是批准关卡。总监修正或公开缺口。

work/iterations.json记录新增事实、结论/分数变化及短原因、未解决问题、挑战意见与停止原因，不存隐藏推理/凭据，不进分享ZIP。仅重排标reuse_snapshot，真实验跑记录角色时间、覆盖与raw，不冒称已完整验证。
