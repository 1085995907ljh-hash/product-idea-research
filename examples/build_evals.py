"""Record synthetic local-renderer regression cases, not model or market evals."""
from copy import deepcopy
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
skill = repo/'skills/product-idea-research'
sys.path.insert(0, str(skill/'scripts'))
from report import V1, V2, V3, V4, V5, initial, markdown, score, validate
from research_details import mindshare_counts

LIMITATION = ('Recorded synthetic inputs and deterministic local-renderer outputs only. '
              'No model baseline, model execution, holdout, blind review, or model improvement measurement. '
              'Passing these cases does not establish factual accuracy or representative research.')


def fixture(version=V3):
    d = initial('合成回归夹具：不是市场调研', '只测试契约，不代表任何真实产品', version)
    d.update(date='2026-10-28', fixture=True)
    return d


def sources():
    return [dict(id=sid, title='Synthetic fixture ' + name, url='https://example.org/fixtures/' + sid,
                 status='verified', accessed_at='2026-10-28', published_at='2026-10-01')
            for sid, name in [('S1', 'product descriptions'), ('S2', 'review records'), ('S3', 'natural discussion records')]]


def scored(d, value, certainty='inferred'):
    for row in d['scorecard']:
        row.update(value=value, reason='合成评分，仅测试渲染及历史兼容。', source_ids=['S1'])
        if d['schema_version'] != V1:
            row['certainty'] = certainty


def deep_fixture():
    """Every claim and identity in this fixture is invented and visibly synthetic."""
    d = fixture()
    d['sources'] = sources()
    d['conclusion'].update(summary='合成案例：原任务已存在，仍需验证一个小缺口。', reasons=['合成讨论包含反证，不代表真实需求频率。'])
    d['decision'].update(recommendation='仅演示先验证缺口的建议。', mvp_focus='合成 MVP：仅测试一个任务结果。', main_risk='这是一组虚构资料，不能支持真实入场决策。', next_step='在真实研究中重新核验用户与替代方案。', source_ids=['S1', 'S3'])
    sr = d['social_research']
    sr['summary'] = '合成平台材料仅用于合同回归，不能推断实际需求强弱。'
    sr['platforms'] = [
        dict(id='forum', name='合成论坛', status='available', query_scope='合成需求查询；未按品牌筛选', time_range='2026-10-01 至 2026-10-07（虚构）', discussion='合成讨论同时出现时间成本问题与无需新工具的反证。', assessment='仅演示多位作者的材料组织。', limitation='全部内容均为 synthetic fixture。', source_ids=['S3']),
        dict(id='video', name='合成短视频平台', status='blocked', query_scope='尚未取得原始材料', time_range='尚未核实', discussion='未取得讨论材料，不能称没有讨论。', assessment='访问受阻不构成没有需求。', limitation='无可用原帖，不补造样本。', source_ids=[])]
    sr['posts'] = [dict(id=pid, platform_id='forum', author_key=author, published_at='2026-10-01', region='US（合成身份）', state='verified', query_origin='need', behavior='problem', context=context, quote=None, brand_mentions=brands, source_ids=['S3'])
                   for pid, author, brands, context in [
                       ('P1', 'synthetic-author-a', ['C1'], '合成作者 A：现有工具需要反复手工整理。'),
                       ('P2', 'synthetic-author-b', [], '合成作者 B：手工办法够用，不愿安装新软件。'),
                       ('P3', 'synthetic-author-a', ['C1', 'C2'], '同一合成作者 A 再次提及两个品牌，须去重。'),
                       ('P4', 'synthetic-author-c', ['C1', 'C2'], '合成作者 C 比较两个已有办法。')]]
    sr['pains'] = [dict(id='pain', name='合成痛点：重复整理', audience='合成用户', situation='虚构的重复任务', current_workaround='合成现办法：人工表格', problem='合成问题：重复录入', consequence='合成影响：额外时间成本', recurrence='两位合成作者提供线索，不能推出总体频率。', counterevidence='决定性合成反证：有人认为人工办法已足够。', status='recurring', post_ids=['P1', 'P2'], source_ids=['S3'])]
    d['need_assessment'].update(classification='new_solution', novelty_reason='合成分类演示：旧任务的新解法，不是新出现的需求。', demand_summary='只能展示证据结构，不能判定真实需求。', existing_solutions='合成工具 Alpha、Beta 及人工表格。', satisfaction='部分合成用户满意，部分仍需手工整理。', remaining_gap='合成剩余缺口：一个重复整理步骤。', original_action='合成原案：收窄后补证据。', source_ids=['S1', 'S3'])
    d['competitors'] = [dict(id=cid, name=name, kind=kind, summary='合成替代方案，不是真实产品。', pricing='合成价格未知；人工办法也有时间成本。', limitation='不得当作真实竞争格局。', positioning='合成定位：完成同一旧任务。', audience='合成用户', category_ids=[category], official_keywords=['合成官方词'], user_keywords=[], strengths=['合成优势：已有完整流程'], weaknesses=['合成边界：仍有人工步骤'], source_ids=['S1'])
                        for cid, name, kind, category in [('C1', '合成工具 Alpha', 'direct', 'software'), ('C2', '合成工具 Beta', 'indirect', 'software'), ('C3', '合成人工表格', 'manual', 'manual')]]
    ca = d['competitive_analysis']
    ca['categories'] = [dict(id='software', name='合成分类：软件流程', description='围绕同一个任务的合成软件替代。', competitor_ids=['C1', 'C2'], source_ids=['S1']), dict(id='manual', name='合成分类：人工办法', description='零新增软件费不代表零时间成本。', competitor_ids=['C3'], source_ids=['S1'])]
    ca['feature_competitor_ids'] = ['C1', 'C2']
    ca['features'] = [dict(id='feature', name='合成功能：减少重复录入', cells=[dict(competitor_id='C1', state='partial', basis='合成功能依据：仍有一个手工步骤。', source_ids=['S1']), dict(competitor_id='C2', state='unknown', basis='合成功能尚未核实，不能编有或没有。', source_ids=[])])]
    ca['reviews'] = [dict(id=rid, competitor_id='C1', rating=rating, published_at='2026-10-02', version=None, summary=summary, quote=None, source_ids=['S2']) for rid, rating, summary in [('R1', 5, '合成好评：完整流程省时间。'), ('R2', 2, '合成差评：重复录入仍然费时。')]]
    ca['review_coverage'] = [dict(competitor_id=cid, scope='合成精选评论，非全量', time_range='2026-10（虚构）', limitation='两条虚构评论不代表真实用户分布。' if cid == 'C1' else '未取得评论，零条不代表无用户或无差评。', source_ids=['S2'] if cid == 'C1' else []) for cid in ('C1', 'C2', 'C3')]
    ca['review_themes'] = [dict(id=tid, sentiment=sentiment, theme=theme, task='完成合成旧任务', impact=impact, current_status='unknown', assessment='合成现状未核实，不能把回复当修复验证。', competitor_ids=['C1'], review_ids=[rid], source_ids=['S2']) for tid, sentiment, theme, impact, rid in [('positive', 'positive', '合成好评主题：流程完整', '合成结果：减少操作', 'R1'), ('negative', 'negative', '合成差评主题：重复录入', '合成结果：仍有时间成本', 'R2')]]
    ca['mindshare'].update(status='measured', summary='仅统计合成自然讨论样本中的品牌提及，不是市场份额。', eligible_post_ids=['P1', 'P2', 'P3', 'P4'], limitation='分母包含未提品牌者，同作者去重，可同时提及多个品牌；不推导销量或份额。')
    direction = deepcopy(initial('合成方向', '合成 idea', V2)['directions'][0])
    direction.update(id='narrow-task', name='合成方向：一个整理步骤', stance='recommended', target_user='合成重复任务用户', change='合成原案收窄为一个步骤。', mvp_focus='仅验证减少一次重复操作。', why='合成证据只能演示结构，不支持真实产品建议。', first_test='真实研究应重新寻找独立用户并做小测试。', main_risk='尚未验证真实需求。', pain_ids=['pain'], competitor_ids=['C1', 'C3'], existing_alternatives='合成工具 Alpha 与人工表格。', remaining_gap='合成缺口：重复录入。', source_ids=['S1', 'S3'])
    scored(d, 3)
    for row in direction['scorecard']:
        row.update(value=3, certainty='inferred', reason='合成方向评分，仅测试相同维度。', source_ids=['S1', 'S3'])
    d['directions'] = [direction]
    return d


def assertion(aid, description, required=(), forbidden=()):
    return dict(id=aid, description=description, required=list(required), forbidden=list(forbidden), weight=1)


def brief_fixture():
    d = deep_fixture()
    blank = fixture(V4)
    d.update(schema_version=V4, sections=blank['sections'], briefing=blank['briefing'])
    b = d['briefing']
    b['selected_competitor_ids'] = d['competitive_analysis']['feature_competitor_ids']
    b['feature_ids'] = [f['id'] for f in d['competitive_analysis']['features']]
    b['review_ids'] = [r['id'] for r in d['competitive_analysis']['reviews']]
    b['landscape']['entries'] = [dict(competitor_id=c['id'],quadrant='top-left' if i%2==0 else 'top-right',source_ids=c['source_ids']) for i,c in enumerate(d['competitors'])]
    b['executive'].update(recommendation='合成总监建议，不构成真实入场意见。', alternative='合成相邻方向，尚未验证。', mvp_focus='合成最小任务，只测试报告。')
    return d


def deep_brief_fixture():
    """V5 author regression data; all products, people, trends and costs are synthetic."""
    d = brief_fixture()
    d.update(schema_version=V5, title='V5 合成深度展示：不是市场调研')
    d['briefing']['depth'] = fixture(V5)['briefing']['depth']
    b, depth, ca = d['briefing'], d['briefing']['depth'], d['competitive_analysis']
    ca['features'].append(dict(id='history', name='合成功能：核对历史来源', cells=[
        dict(competitor_id='C1', state='yes', basis='合成功能材料演示：可查看来源。', source_ids=['S1']),
        dict(competitor_id='C2', state='partial', basis='合成功能材料演示：只保留部分来源。', source_ids=['S1'])]))
    b['feature_ids'] = [f['id'] for f in ca['features']]
    ca['reviews'].append(dict(id='R3', competitor_id='C2', rating=4, published_at='2026-10-03', version=None,
                              summary='合成 Beta 好评：轻量流程较易上手。', quote=None, source_ids=['S2']))
    ca['review_coverage'][1].update(scope='仅一条合成精选高星文字评价', limitation='一条虚构高星评论不能支持总体口碑，也不能说明没有差评。', source_ids=['S2'])
    b['review_ids'] = [r['id'] for r in ca['reviews']]
    depth['market']['social_platforms'] = [
        dict(id='forum', label='合成论坛', state='available', summary='合成需求讨论同时包含重复整理问题与反证。', pain='合成用户反复录入同一条信息。', opportunity='只演示收窄到一个任务的机会判断，不构成真实建议。', post_ids=['P1', 'P2', 'P4'], source_ids=['S3']),
        dict(id='video', label='合成短视频平台', state='blocked', summary='合成访问受阻状态，不补造平台讨论。', pain='未取得材料，不能判定痛点。', opportunity='未知；访问失败不等于没有需求。', post_ids=[], source_ids=[])]
    depth['market']['social_findings'] = [dict(title='合成观察：旧任务在新流程里仍有手工步骤', need='合成材料演示一个旧需求，并保留无需新软件的反证。', newness='这是合成旧任务的新解法，不是新需求证据。', opportunity='合成机会：减少一次重复录入。', avoid='合成放弃项：在没有效果依据时承诺自动完成全部工作。', source_ids=['S1', 'S3'])]
    depth['market']['keyword_groups'] = [
        dict(id='synthetic-problem', title='合成关键词组：任务痛点', intent='合成意图：按任务而非品牌查找问题。', keywords=['synthetic repeated entry', 'synthetic manual sorting'], summary='全部序列为 synthetic，不能解读为真实 Google Trends 走势。', source_ids=['S3']),
        dict(id='synthetic-alternative', title='合成关键词组：现有办法', intent='合成意图：查找旧任务的替代办法。', keywords=['synthetic task workflow', 'synthetic task spreadsheet'], summary='两组独立归一化，只测试分组组织，不比较跨组绝对热度。', source_ids=['S3'])]
    d['trends'] = [dict(keyword=keyword, group=group['id'], window=window, geo='US', category='All', search_type='Web', granularity='synthetic-weekly', reason='Synthetic raw points for renderer regression only; not actual Google Trends data.', source_ids=['S3'], points=[dict(date='2026-10-01', value=10, partial=False), dict(date='2026-10-08', value=None, partial=False), dict(date='2026-10-15', value=20, partial=True)])
                   for group in depth['market']['keyword_groups'] for keyword in group['keywords'] for window in ('30d', '90d', '12m')]
    b['trend_summary'] = '合成多组关键词序列仅测试渲染，不代表真实搜索量；组间和窗口间不能比较绝对大小。'
    depth['competition']['catalog_groups'] = [dict(id=r['id'], title=r['name'], description=r['description'], competitor_ids=r['competitor_ids'], source_ids=r['source_ids']) for r in ca['categories']]
    depth['competition']['selection'] = [
        dict(competitor_id='C1', roles=['leader', 'similar'], reason='合成 Alpha 被选来比较完整流程与重复录入步骤。', source_ids=['S1']),
        dict(competitor_id='C2', roles=['new', 'adjacent'], reason='合成 Beta 被选来比较轻量流程；新进入者角色仅为虚构分类。', source_ids=['S1'])]
    depth['competition']['feature_groups'] = [
        dict(id='entry', title='合成任务链：录入整理', job='合成用户希望减少一次重复录入。', feature_ids=['feature'], takeaway='合成 Alpha 只支持部分，Beta 仍未核实；未知不等于没有。', source_ids=['S1']),
        dict(id='checking', title='合成任务链：回看核对', job='合成用户希望追溯自己整理过的资料。', feature_ids=['history'], takeaway='合成功能差异：完整来源与部分来源的区别，不代表实际使用效果。', source_ids=['S1'])]
    depth['competition']['product_reviews'] = [
        dict(competitor_id='C1', state='available', summary='合成 Alpha 两条文字评价演示正负声音并存。', positive=['合成 Alpha 好评：流程完整省时间。'], negative=['合成 Alpha 差评：重复录入仍费时。'], judgment='合成 Alpha 判断：价值与手工步骤并存，尚不能推断总体口碑。', review_ids=['R1', 'R2'], source_ids=['S2']),
        dict(competitor_id='C2', state='partial', summary='合成 Beta 只取得一条高星文字评价，不强凑差评。', positive=['合成 Beta 好评：轻量流程较易上手。'], negative=[], judgment='合成 Beta 判断：负面声音尚未取得，不能声称没有差评。', review_ids=['R3'], source_ids=['S2'])]
    base = d['directions'][0]
    for direction_id, name in [('history-check', '合成方向：回看资料来源'), ('manual-assist', '合成方向：人工表格辅助')]:
        other = deepcopy(base)
        other.update(id=direction_id, name=name, stance='explore', mvp_focus='合成范围：只支持一次人工核对。', main_risk='合成方向仍缺真实用户与效果证据。')
        d['directions'].append(other)
    depth['directions'] = [
        dict(direction_id='narrow-task', description='合成方向描述：只减少重复整理的一步。', pain='合成方向痛点：重复录入花时间。', better_because='合成取舍：任务范围较窄，可先判断是否减少一次操作。', cost=dict(level='low', build='合成搭建成本：输入整理与本地保存；不编美元或工期。', ongoing='合成持续成本：资料维护与支持，暂无真实报价。'), feasibility=dict(verdict='conditional', summary='合成技术判断：整理流程可表达，但效果尚未验证。', dependencies=['合成依赖：用户授权提供资料，不能假设跨应用读取权限。']), source_ids=['S1', 'S3']),
        dict(direction_id='history-check', description='合成方向描述：让用户回看已整理信息的来源。', pain='合成方向痛点：事后难以核对来源。', better_because='合成取舍：先提供可追溯资料，不承诺自动判断内容正确。', cost=dict(level='medium', build='合成搭建成本：来源关联与检索索引；未取得真实报价。', ongoing='合成持续成本：索引维护与存储开销，当前只有相对档位。'), feasibility=dict(verdict='feasible', summary='合成技术判断：可演示来源关联，不能代替真实技术验证。', dependencies=['合成依赖：原始内容可合法保存且来源链接仍可访问。']), source_ids=['S1', 'S3']),
        dict(direction_id='manual-assist', description='合成方向描述：在人工表格上增加一项辅助。', pain='合成方向痛点：用户不愿迁移现有表格。', better_because='合成取舍：保留现有工作办法，但能否付费仍未知。', cost=dict(level='unknown', build='合成搭建成本：取决于真实文件格式和平台能力，暂不估算。', ongoing='合成持续成本：格式兼容和维护投入未知。'), feasibility=dict(verdict='unknown', summary='合成技术判断：尚未检查真实平台导入导出能力。', dependencies=['合成依赖：补核平台文档与用户文件范围。']), source_ids=['S1', 'S3'])]
    return d


def record(case_id, data, assertions, reject=False):
    """Read the persisted fixture and exercise the real validator and renderer."""
    relative = Path('fixtures')/(case_id + '.json')
    path = skill/'evals/output'/relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    loaded = json.loads(path.read_text(encoding='utf-8'))
    errors = validate(loaded)
    if reject:
        if not errors:
            raise AssertionError(case_id + ': invalid fixture unexpectedly accepted')
        output = 'STRUCTURAL_VALIDATION_REJECTED\n' + '\n'.join(errors) + '\n'
    else:
        if errors:
            raise AssertionError(case_id + ': ' + '\n'.join(errors))
        output = markdown(loaded)
        if loaded['schema_version'] == V5:
            report_path = skill/'evals/output/reports'/(case_id + '.md')
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(output, encoding='utf-8')
    for item in assertions:
        missing = [x for x in item['required'] if x not in output]
        forbidden = [x for x in item['forbidden'] if x in output]
        if missing or forbidden:
            raise AssertionError(f'{case_id}/{item["id"]}: missing={missing}, forbidden={forbidden}')
    return dict(id=case_id, prompt=('Reject this invalid synthetic input before rendering.' if reject else 'Render this explicitly synthetic file-backed contract fixture.') + ' Do not research or execute a model.', input_files=[relative.as_posix()], baseline_output='', with_skill_output=output,
                execution=dict(mode='recorded_fixture', provider='local-renderer', holdout=False),
                metadata=dict(fixture=True, synthetic=True, expected_result='validation_rejected' if reject else 'rendered', model_comparison=False, blind_review=False, scope=LIMITATION), assertions=assertions)


def main():
    unknown = fixture()
    deep = deep_fixture()
    counts = mindshare_counts(deep)
    assert counts['denominator'] == 3 and {r['competitor_id']: r['count'] for r in counts['rows']} == {'C1': 2, 'C2': 2}
    invalid_evidence = fixture()
    invalid_evidence['sources'] = [dict(id='U', title='Synthetic unverified lead', url='https://example.org/fixtures/unverified', status='unverified', accessed_at='2026-10-28')]
    invalid_evidence['evidence'] = [dict(id='bad-fact', type='A', state='fact', claim='合成负例：不能把未核实线索标为事实。', source_ids=['U'], limitation='Synthetic invalid provenance.')]
    brand_search = deepcopy(deep)
    brand_search['social_research']['posts'][0]['query_origin'] = 'brand'
    v1 = fixture(V1)
    v1['sources'] = sources()
    scored(v1, 5)
    v2 = fixture(V2)
    v2['sources'] = sources()
    scored(v2, 5, 'supported')
    assert score(v1)['stars'] == 2.5 and score(v2)['value'] == 5 and 'stars' not in score(v2)
    cases = [
        record('v4-four-chapter-brief', brief_fixture(), [
            assertion('four-chapters-not-research-log', 'Four readable chapters replace six historical sections.', ['## 一、研究概览','## 二、市场调研','## 三、竞品','## 四、产品研究'], ['## 先验证什么','## 依据与缺口','## 方向建议与 MVP']),
            assertion('quadrant-features-rated-reviews', 'Qualitative landscape, selected features and review ratings remain linked.', ['### 竞品四象限','### 功能与口碑','5/5','2/5','不代表市场份额','[S1]'])]),
        record('v4-unknown-is-not-reject', fixture(V4), [
            assertion('unknown-and-no-claims', 'All-unknown template has no invented competitors or positive decision.', ['总监评分：2.5/5（暂定）','未知项仅以中性2.5计算暂定总分','尚未研究，不作入场建议'], ['## 先验证什么'])]),
        record('v3-unknown-no-directions', unknown, [
            assertion('unknown-stays-unknown', 'Neutral placeholders remain provisional and do not imply opportunity.', ['阅读样例，非真实市场调研', '综合分：2.5/5（暂定）', '证据不足，先补关键证据', '不代表已证实的中等表现']),
            assertion('no-invented-direction-or-share', 'Zero directions keeps its reason and insufficient samples produce no share table.', [unknown['no_directions_reason'], '尚未取得可去重的自然需求讨论样本'], ['### 待研究的相邻方向', '本次样本品牌主动提及（不是市场份额）'])]),
        record('v3-synthetic-deep-research', deep, [
            assertion('platforms-pains-counterevidence', 'Discussion, current workaround, recurring pain and decisive counterevidence remain visible.', ['阅读样例，非真实市场调研', 'synthetic fixture', '未取得讨论材料，不能称没有讨论', '合成现办法：人工表格', '决定性合成反证']),
            assertion('old-task-and-alternatives', 'Need classification and task-based alternatives precede feature comparisons.', ['旧任务的新解法，不是新出现的需求', '合成分类：软件流程', '合成分类：人工办法', '合成功能依据', '合成功能尚未核实']),
            assertion('reviews-and-natural-denominator', 'Good and bad review themes, actual sample counts and author deduplication survive expansion.', ['合成好评主题：流程完整', '合成差评主题：重复录入', '2条 / 好评1 / 低星1', '2/3', '分母包含未提品牌者', '不是市场份额'], ['市场份额：', '2/4']),
            assertion('row-citations-and-folded-details', 'Expanded tables retain per-row sources and discussion/review details are folded.', ['[S1](https://example.org/fixtures/S1)', '[S2](https://example.org/fixtures/S2)', '[S3](https://example.org/fixtures/S3)', '<summary>代表讨论与取证边界</summary>', '<summary>评论明细</summary>'])]),
        record('v3-reject-unverified-fact', invalid_evidence, [
            assertion('invalid-provenance-rejected', 'A fact backed by an unverified lead must stop before a report is emitted.', ['STRUCTURAL_VALIDATION_REJECTED', '未核实来源'], ['## 研究概览', '综合分：'])], reject=True),
        record('v3-reject-brand-search-denominator', brand_search, [
            assertion('brand-query-is-not-natural-sample', 'A brand-query post cannot enter the natural need sample denominator.', ['STRUCTURAL_VALIDATION_REJECTED', '分母只能含已核实自然需求用户', '不能含品牌检索/广告/创作者'], ['## 研究概览', '本次样本品牌主动提及（不是市场份额）'])], reject=True),
        record('v1-historical-rendering', v1, [
            assertion('legacy-payment-cap-preserved', 'Explicit v1 keeps its original seven-dimension score and payment cap.', ['2.5星', '无有效付费证据，星级上限2.5', '想法与子方向', '小团队可做性'], ['证据不足，先补关键证据', '不同平台在讨论什么']),
            assertion('legacy-sample-disclosed', 'Historical rendering still discloses synthetic inputs.', ['阅读样例，非真实市场调研'])]),
        record('v2-historical-rendering', v2, [
            assertion('v2-no-legacy-payment-cap', 'Explicit v2 retains six weighted dimensions without reintroducing the v1 cap.', ['综合分：5.0/5，优先验证', '独立开发投入', 'MVP 主攻点'], ['星级上限', '5.0/5，2.5星']),
            assertion('v2-no-v3-detail-injection', 'Historical v2 stays renderable without fabricated deep-research objects.', ['需求与近期话题', '竞品与差评', '搜索兴趣走势'], ['不同平台在讨论什么', '代表讨论与取证边界'])])]
    bad_brief = fixture(V4)
    bad_brief['briefing']['executive']['recommendation'] = '合成负例链接 https://example.org'
    cases.append(record('v4-reject-overview-links', bad_brief, [assertion('overview-link-rejected','Overview links must be rejected before report generation.',['STRUCTURAL_VALIDATION_REJECTED','研究概览禁止链接'])], reject=True))
    v5 = deep_brief_fixture()
    cases.append(record('v5-synthetic-deep-presentation', v5, [
        assertion('synthetic-four-chapter-depth', 'Synthetic V5 data adds depth while retaining the four chapters and real coverage states.', ['阅读样例，非真实市场调研', '## 一、研究概览', '## 二、市场调研', '## 三、竞品', '## 四、产品研究', '### 跨平台讨论与痛点', '合成短视频平台 · 访问受限', '合成关键词组：任务痛点', '合成关键词组：现有办法']),
        assertion('catalog-and-separate-job-features', 'The full synthetic task catalog and independent job-based feature comparison remain readable.', ['### 分类竞品全量目录', '合成分类：软件流程', '合成分类：人工办法', '### 重点对手为什么选它', '### 按用户任务分组的功能对比', '合成任务链：录入整理', '合成任务链：回看核对', '合成功能：核对历史来源']),
        assertion('reviews-are-product-specific-and-limited', 'Each selected synthetic product has its own review synthesis and visible sample limits without invented negative reviews.', ['### 逐产品口碑与样本限制', '合成工具 Alpha · 已取得材料', '合成 Alpha 判断', '本轮引用文字评价：2条', '合成工具 Beta · 部分覆盖', '合成 Beta 判断', '本轮引用文字评价：1条', '一条虚构高星评论不能支持总体口碑', '本轮未取得足够材料，不作结论。']),
        assertion('three-costed-technical-directions', 'Three synthetic directions preserve build and ongoing cost, technical feasibility and platform dependencies.', ['### 可考虑的产品方向', '合成方向：一个整理步骤', '合成方向：回看资料来源', '合成方向：人工表格辅助', '搭建成本', '持续成本', '技术可行性', '依赖与平台边界', '不能假设跨应用读取权限', '尚未检查真实平台导入导出能力'], ['### 功能与口碑'])]))
    cross_product = deepcopy(v5)
    cross_product['briefing']['depth']['competition']['product_reviews'][0]['review_ids'] = ['R3', 'R2']
    cross_product['briefing']['depth']['competition']['product_reviews'][1]['review_ids'] = ['R1']
    cases.append(record('v5-reject-cross-product-reviews', cross_product, [
        assertion('same-product-review-provenance', 'Existing synthetic review IDs cannot be reassigned to another selected product even when aggregate IDs and star bands still match.', ['STRUCTURAL_VALIDATION_REJECTED', 'product_review评论与产品不匹配'], ['## 一、研究概览', '### 逐产品口碑与样本限制'])], reject=True))
    wrong_keyword_group = deepcopy(v5)
    wrong_keyword_group['trends'][0]['group'] = 'synthetic-alternative'
    cases.append(record('v5-reject-keyword-group-mismatch', wrong_keyword_group, [
        assertion('keyword-group-provenance', 'A synthetic keyword cannot be placed into a different existing comparison group.', ['STRUCTURAL_VALIDATION_REJECTED', '趋势keyword须在对应关键词组内'], ['## 一、研究概览', '### 多组关键词与搜索意图'])], reject=True))
    output = skill/'evals/output/cases.jsonl'
    output.write_text(''.join(json.dumps(case, ensure_ascii=False) + '\n' for case in cases), encoding='utf-8')
    print(f'{len(cases)} recorded renderer cases / {sum(len(case["assertions"]) for case in cases)} assertions generated and locally checked; no model comparison or model gain claim.')


if __name__ == '__main__':
    main()
