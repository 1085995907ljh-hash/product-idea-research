# v4：四部分、五分钟产品调研

默认schema_version=product-idea-research/v4。v3深度证据字段继续保留，见deep-data-contract.md；v1/v2/v3依原report-contract.md渲染。评分公式和六维权重不变。改版已有报告保留来源时间；未重查的部分不得称新研究。

## 同源与结构

research.json是单一内容源；report.py生成HTML、MD及仅含research.json/research.md/sources.json的ZIP。raw、work、访问状态和内部迭代不进分享包。HTML和MD只有研究概览、市场调研、竞品、产品研究四个一级阅读章节。

保留title/date/idea/scope/fixture/status/conclusion/sources/evidence/competitors/trends/glossary/scorecard/decision/directions及v3的social_research/need_assessment/competitive_analysis。decision.next_step、directions.first_test为历史/内部兼容字段，不在v4阅读报告展示。directions可为零，无推荐不硬凑。

sections恰为market/市场调研、competition/竞品、product/产品研究，按此顺序。每项仍含status/summary/blocks/source_ids。内容块沿用paragraph/list/table及逐行来源。子块必须依次使用以下ID：

- market：market-overview（领域、分类、细分和演变）、market-social、market-scale、market-users；renderer再追加market-trends。
- competition：blocks为空；由briefing和competitive_analysis生成四象限、重点竞品、功能口碑、竞争判断，避免重复正文。
- product：product-potential、product-cost、product-cautions。

用户可见块标题用简短中文；目录按章节包含子目录，不能把全部标题摊平。status partial不自动改变商业判断。受阻、未知保留在影响判断的具体位置，不扩成独立缺口章。

## briefing对象

- executive：recommendation/alternative/mvp_focus，均非空文本。对应总监建议、更好的方向和MVP。概览用conclusion.summary+executive+scorecard，不显示来源链接、编号、详细证据。conclusion.reasons仍最多3条，完整证据在数据里。概览字段加评分理由总长最多900字符，建议实际300–500中文字符；每项reason最多90字符，实际尽量一句。
- landscape：x_low/x_high/y_low/y_high定义定性定位轴；entries最多12条，含competitor_id/quadrant/source_ids。quadrant为top-left/top-right/bottom-left/bottom-right之一。每点都须对应真实竞品和依据；按当前主要任务归类，note说明非市场份额 / 排名 / 质量。轴随项目确定，不固定“功能多就好”。无样本象限不等于无竞品或蓝海。禁止无依据精确坐标。
- selected_competitor_ids：0–7个在competitive_analysis.feature_competitor_ids中的ID；selection_reason解释选谁和为什么。正常研究选5–7款，无可核验样本允许空，明示不完整。
- feature_ids：最多6个competitive_analysis.features中的ID；选能改变入场判断的关键功能。整张深入矩阵继续保存，网页只展示这些行。每格yes/partial/no/unknown及basis/source_ids沿用v3。
- review_ids：最多4个真实review ID，优先同一重点竞品各取一好一差，保留rating/published_at/original_url/source_ids。review_note写清样本数、时期、版本与偏差，不用所选好差比当投诉率。评价不足就直说。
- competition_judgment：verdict为yes/conditional/no/unknown；summary/our_advantage/our_disadvantage/source_ids。必须回答能否做出有价值的差异，对手潜力缺乏收入 / 留存时不伪造增长结论。
- trend_summary：一句主要结论和必要的词义 / 低量限制。

competitors可加short_name、brief（一句定位）、primary_url（官方产品页）、icon（内嵌PNG/JPEG/WebP的data URI）、store={rating,rating_count,category,first_release,source_ids}。图标无外部运行时依赖，不制作假图标。0评级显示样本不足，不能显示成0星质量或无用户；评分样本极少须看得见分母。价格仅公开目录时说明未测购买页，不选最低SKU冒充统一报价。

trends沿用真实原始点，图按window+group+geo+category+search_type+granularity分组；不得把不同口径合线。可设置exclude_by_default=true隐藏污染词，必须明确告诉用户且能勾选恢复。默认12个月，支持30/90天。未知不补0，partial不连线。MD提供结论/口径/来源，逐期点留JSON，避免数百行淹没正文。

## 可读性验收

概览30–60秒、正文约5分钟为设计目标，不声称实测用户阅读时长。正文约1800–2600中文字符供作者压缩；图表标签与来源不计入。若超出优先删重复结论和方法解释。概览无a链接，四章完整，关键负面证据不因精简消失。

1440/390宽度检查目录树、四象限、图标加载、评分未知、表格横滑、图表切换；MD/ZIP真实下载须与本地同源文件逐字节相等。结构与渲染检查不证明商业结论、AI效果或实际阅读时长。
