"""V6 decision-first stress test; evidence grades are not legacy evidence types."""
import math
import re
from urllib.parse import urlsplit

SCRIPT_INTERFACE = 'internal-module'
SCRIPT_INTERFACE_REASON = 'Imported by report.py for V6 director validation and Markdown.'
V6 = 'product-idea-research/v6'
GRADES = dict(A='行为证据', B='一手资料', C='佐证', D='间接指标', E='断言/推断')
BELIEF_STATUS = dict(supported='有支持', mixed='证据冲突', unsupported='有反证', unknown='仍是假设')
CATEGORIES = {'pain', 'behavior', 'feasibility', 'retention_payment', 'acquisition_competition'}
ACTIONS = dict(test='只投入小测试', invest='有限投入', hold='暂缓投入', stop='停止原案')
LINK_PATTERN = re.compile(r'https?://|www\.|\[[^\]]+\]\s*\(|<a\b', re.I)
SIX = 'investigator-six'
MEASURES = dict(task_completion='完整任务', return_use='主动回访', stated_intent='口头意愿', acquisition_response='点击/获客响应', actual_payment='实际付款', technical_reliability='技术可靠性')


def initial_stress_test():
    return dict(
        state='not_run', presentation=SIX,
        thesis=dict(statement='尚未锁定原案论点。', founder_goal='默认个人开发者的小型可盈利产品，待依据用户目标调整。', decision='判断是否值得继续投入。'),
        beliefs=[], bottleneck=None, tests=[], adjacent=None, adjacent_hypothesis=None,
        no_test_reason='尚未研究，当前没有依据设计测试。',
        commitment=dict(action='hold', summary='尚未研究，不作进入或否决建议。', cap='尚未分配进一步投入。', escalation_condition='取得能改变判断的证据后再决定。'))


def _objects(value):
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def selected_evidence(data, polarity):
    """Deduplicate supporting/opposing records in belief order, preserving provenance."""
    evidence = {e.get('id'): e for e in _objects(data.get('evidence')) if isinstance(e.get('id'), str)}
    result, seen = [], set()
    for belief in _objects(data.get('stress_test', {}).get('beliefs')):
        for eid in belief.get(polarity + '_evidence_ids', []):
            if isinstance(eid, str) and eid in evidence and eid not in seen:
                result.append(evidence[eid])
                seen.add(eid)
    return result


def threshold_text(threshold):
    operator = {'gte': '≥', 'lte': '≤'}[threshold['operator']]
    return operator + str(threshold['value']) + ' ' + threshold['unit']


def director_reply(data, md_text, with_sources=True):
    """Six-part decision brief; source links are allowed only in the chat variant."""
    s = data['stress_test']
    c = s['commitment']
    out = ['### 1）一句话结论', '', md_text(data['conclusion']['summary']), '',
           md_text(c['summary'] + ' 投入边界：' + c['cap'] + ' 追加条件：' + c['escalation_condition']), '',
           '### 2）必须成立的前提', '']
    if data.get('fixture'):
        out[2:2] = ['> 合成阅读样例，非真实市场调研。', '']
    for i, b in enumerate(s['beliefs'], 1):
        out.append(str(i) + '. ' + md_text(b['claim']))
    if not s['beliefs']:
        out.append('尚未研究，不能把空白当作失败。')
    out.extend(['', '### 3）证据', '', 'A是真实行为，B是一手资料，C是评论/论坛等佐证，D是间接指标，E是推断；等级仅适用于具体论断。', ''])
    source_map = {r['id']: r for r in data['sources']}
    for polarity, title in [('support', '支持'), ('oppose', '反对')]:
        out.extend(['**' + title + '**', ''])
        rows = selected_evidence(data, polarity)
        for e in rows:
            line = '- ' + md_text(e['claim']) + ' 等级 ' + e['grade'] + '。' + md_text(e['limitation'])
            if with_sources:
                links = []
                for sid in dict.fromkeys(e['source_ids']):
                    source = source_map[sid]
                    url = source['url']
                    try:
                        parsed = urlsplit(url)
                        safe = parsed.scheme in ('https', 'http') and parsed.netloc and not parsed.username and not parsed.password and not any(ch.isspace() for ch in url)
                    except ValueError:
                        safe = False
                    if safe:
                        links.append('[' + md_text(source.get('display_title') or source['title']) + '](' + url.replace('(', '%28').replace(')', '%29') + ')')
                if links:
                    line += ' ' + '、'.join(links[:2])
            out.append(line)
        if not rows:
            out.append('本轮没有足够材料，不据此证明成立或不成立。')
        out.append('')
    out.extend(['### 4）最可能杀死它的假设', ''])
    b = s['bottleneck']
    if b:
        premise = next(r for r in s['beliefs'] if r['id'] == b['belief_id'])
        out.extend([md_text(premise['claim'] + ' ' + b['why']), '', md_text('若不成立：' + b['decision_if_false'] + ' 若成立：' + b['decision_if_true']), ''])
    else:
        out.extend(['尚未取得足够材料选定一个决定性假设；不作致命风险判断。', ''])
    out.extend(['### 5）下一步最便宜的测试', ''])
    if s['tests']:
        out.extend(['门槛是执行前拟定的决策规则，不是行业基准或已经取得的结果。', ''])
    for i, t in enumerate(s['tests'], 1):
        out.extend(['**测试 ' + chr(64 + i) + '：**' + md_text(t['method']), '',
                    md_text('对象/分母：' + t.get('sample_definition', '未记录。') + ' 时间：' + t.get('time_window', '未记录。') + ' 协助方式：' + t.get('assistance', '未记录。')), '',
                    md_text(t['observed_behavior'] + ' 主要指标：' + t['metric'] + '；通过 ' + threshold_text(t['pass_threshold']) + '，失败 ' + threshold_text(t['fail_threshold']) + '。' + t['inconclusive_rule'] + ' ' + t['failure_action']), '',
                    md_text('投入上限：' + t['resource_cap'] + ' 取舍：' + t['selection_reason']), '',
                    md_text('本次只测' + MEASURES.get(t.get('measures'), '已说明的行为') + '；不能证明：' + t.get('cannot_establish', '未记录。')), ''])
    if not s['tests']:
        out.extend([md_text(s['no_test_reason']), ''])
    out.extend(['### 6）可能更强的相邻方向', ''])
    if s['adjacent']:
        out.extend(['**相对推荐：**' + md_text(s['adjacent']['summary']), ''])
    hypothesis = s.get('adjacent_hypothesis')
    if hypothesis:
        out.extend(['**未验证的探索假设：**' + md_text(hypothesis['summary']), '',
                    md_text(hypothesis['why_better'] + ' 新风险：' + hypothesis['new_risk'] + ' 尚缺：' + hypothesis['missing_evidence']), ''])
    if not s['adjacent'] and not hypothesis:
        out.extend(['本轮没有足够依据提出更强的相邻方向，不为凑建议换一个故事。', ''])
    return '\n'.join(out)


def markdown_stress_test(data, md_text):
    """Link-free overview prose, without chapter heading or the separate scorecard."""
    stress = data['stress_test']
    if stress.get('presentation') == SIX:
        return director_reply(data, md_text, with_sources=False)
    thesis = stress['thesis']
    out = [md_text(data['conclusion']['summary']), '', '### 一句话论点', '', md_text(thesis['statement']), '',
           '**用户目标：**' + md_text(thesis['founder_goal']), '', '**当前决策：**' + md_text(thesis['decision']), '',
           '### 必须成立的前提', '']
    for belief in stress['beliefs']:
        out.append('- **' + BELIEF_STATUS[belief['status']] + '：**' + md_text(belief['claim']))
    if not stress['beliefs']:
        out.append('尚未研究，不把缺失证据当成否决。')
    out.extend(['', '### 支持与反对的证据', ''])
    for polarity, title in [('support', '支持'), ('oppose', '反对')]:
        out.extend(['**' + title + '**', ''])
        rows = selected_evidence(data, polarity)
        for evidence in rows:
            out.append('- **' + evidence['grade'] + ' · ' + GRADES[evidence['grade']] + '：**' + md_text(evidence['claim']) + '；' + md_text(evidence['limitation']))
        if not rows:
            out.append('本轮没有足够材料，不据此证明成立或不成立。')
        out.append('')
    out.extend(['### 最可能改变决策的关键假设', ''])
    bottleneck = stress['bottleneck']
    beliefs = {b['id']: b for b in stress['beliefs']}
    if bottleneck:
        out.extend([md_text(beliefs[bottleneck['belief_id']]['claim']), '', md_text(bottleneck['why']), '',
                    '**成立时：**' + md_text(bottleneck['decision_if_true']), '', '**不成立时：**' + md_text(bottleneck['decision_if_false']), ''])
    else:
        out.extend(['尚未取得足够材料选定一个关键假设。', ''])
    out.extend(['### 下一步最便宜的测试', ''])
    if stress['tests']:
        out.extend(['以下门槛是执行前拟定的决策规则，不是行业基准或已经取得的结果。', ''])
    for index, test in enumerate(stress['tests'], 1):
        out.extend(['**测试 ' + str(index) + '：**' + md_text(test['method']), '',
                    '**观察行为：**' + md_text(test['observed_behavior']), '',
                    '**指标：**' + md_text(test['metric']), '',
                    '**通过：**' + md_text(threshold_text(test['pass_threshold'])), '',
                    '**失败：**' + md_text(threshold_text(test['fail_threshold'])), '',
                    '**中间结果：**' + md_text(test['inconclusive_rule']), '',
                    '**失败后：**' + md_text(test['failure_action']), '',
                    '**投入上限：**' + md_text(test['resource_cap']), '',
                    '**为何选这个测试：**' + md_text(test['selection_reason']), ''])
    if not stress['tests']:
        out.extend([md_text(stress['no_test_reason']), ''])
    adjacent = stress['adjacent']
    if adjacent:
        out.extend(['### 更强的相邻方向', '', md_text(adjacent['summary']), ''])
    commitment = stress['commitment']
    out.extend(['### 现在值得投入多少', '', '**' + ACTIONS[commitment['action']] + '：**' + md_text(commitment['summary']), '',
                '**资源上限：**' + md_text(commitment['cap']), '', '**追加投入的条件：**' + md_text(commitment['escalation_condition']), ''])
    return '\n'.join(out)


def validate_stress_test(data):
    """Validate decision structure/provenance; cannot establish factual or business truth."""
    errors = []
    def need(ok, message):
        if not ok:
            errors.append('v6 stress test: ' + message)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def obj(value, label):
        need(isinstance(value, dict), label + '须对象')
        return value if isinstance(value, dict) else {}
    def rows(value, label):
        need(isinstance(value, list) and all(isinstance(row, dict) for row in value), label + '须对象数组')
        return _objects(value)
    def fields(record, names, label):
        for name in names.split():
            need(text(record.get(name)), label + '缺文本 ' + name)
    def choice(value, values, label):
        need(isinstance(value, str) and value in values, label + '无效')
    def index(records, label):
        ids = [row.get('id') for row in records]
        strings = [value for value in ids if text(value)]
        need(len(strings) == len(ids) and len(strings) == len(set(strings)), label + ' ID缺失或重复')
        return {row['id']: row for row in records if text(row.get('id'))}
    def refs(record, key, universe, label):
        values = record.get(key)
        valid = isinstance(values, list) and all(text(value) for value in values)
        need(valid, label + '.' + key + '须文本数组')
        values = values if valid else []
        need(len(values) == len(set(values)) and set(values).issubset(universe), label + '.' + key + '重复或引用不存在的对象')
        return values
    source_map = index(rows(data.get('sources'), 'sources'), 'sources')
    evidence = index(rows(data.get('evidence'), 'evidence'), 'evidence')
    direction_map = index(rows(data.get('directions'), 'directions'), 'directions')
    for item in evidence.values():
        choice(item.get('grade'), GRADES, 'evidence.grade')
        fields(item, 'claim grade_reason limitation', 'evidence')
        source_ids = refs(item, 'source_ids', source_map, 'evidence')
        if item.get('grade') in ('A', 'B', 'C'):
            need(bool(source_ids) and all(source_map[sid].get('status') == 'verified' for sid in source_ids if sid in source_map), 'A/B/C证据须有已查阅的直接来源')
        validated = item.get('validated', False)
        need(type(validated) is bool, 'evidence.validated须布尔值')
        if validated:
            need(item.get('grade') in ('A', 'B', 'C') and item.get('state') == 'fact', 'D/E或非事实证据不能算验证')
            fields(item, 'validation_scope', 'validated evidence')
            need(bool(source_ids) and all(source_map[sid].get('status') == 'verified' for sid in source_ids if sid in source_map), '验证须可追溯到已查阅来源')
    stress = obj(data.get('stress_test'), 'stress_test')
    if 'presentation' in stress:
        choice(stress['presentation'], (SIX,), 'stress_test.presentation')
    six = stress.get('presentation') == SIX
    choice(stress.get('state'), ('not_run', 'researched'), 'stress_test.state')
    researched = stress.get('state') == 'researched'
    if data.get('status') == 'complete':
        need(researched, 'complete报告须已开展前提研究')
    thesis = obj(stress.get('thesis'), 'thesis')
    fields(thesis, 'statement founder_goal decision', 'thesis')
    beliefs = rows(stress.get('beliefs'), 'beliefs')
    belief_map = index(beliefs, 'beliefs')
    need(3 <= len(beliefs) <= 5 if researched else not beliefs, '已研究须3–5条前提；未开展不得装成完成')
    for belief in beliefs:
        fields(belief, 'claim', 'belief')
        choice(belief.get('category'), CATEGORIES, 'belief.category')
        choice(belief.get('status'), BELIEF_STATUS, 'belief.status')
        supports = refs(belief, 'support_evidence_ids', evidence, 'belief')
        opposes = refs(belief, 'oppose_evidence_ids', evidence, 'belief')
        need(not set(supports).intersection(opposes), '同一前提的同一证据不能同时列支持和反对')
        if belief.get('status') in ('supported', 'mixed'):
            need(bool(supports), '有支持/证据冲突的前提须关联支持证据')
        if belief.get('status') in ('unsupported', 'mixed'):
            need(bool(opposes), '有反证/证据冲突的前提须关联反证，缺失不等于反对')
        disconfirmation = obj(belief.get('disconfirmation'), 'disconfirmation')
        fields(disconfirmation, 'summary', 'disconfirmation')
        need(disconfirmation.get('searched') is True, '每个重要前提都须主动寻找反证')
        refs(disconfirmation, 'source_ids', source_map, 'disconfirmation')
    bottleneck = stress.get('bottleneck')
    if researched:
        bottleneck = obj(bottleneck, 'bottleneck')
        need(isinstance(bottleneck.get('belief_id'), str) and bottleneck.get('belief_id') in belief_map, '须选且只选一个已列前提作为关键假设')
        fields(bottleneck, 'why decision_if_true decision_if_false', 'bottleneck')
    else:
        need(bottleneck is None, '未开展时bottleneck须null')
        bottleneck = {}
    commitment = obj(stress.get('commitment'), 'commitment')
    choice(commitment.get('action'), ACTIONS, 'commitment.action')
    fields(commitment, 'summary cap escalation_condition', 'commitment')
    verdict = data.get('conclusion', {}).get('verdict')
    if researched and verdict == 'no_go':
        need(commitment.get('action') == 'stop', '原案不行须停止原案，不能同时建议加大投入')
    if researched and verdict == 'go':
        need(commitment.get('action') != 'stop', '原案值得做不能同时建议停止')
    if not researched:
        need(commitment.get('action') == 'hold', '未开展时只能暂缓，不能据缺失证据进入或否决')
    tests = rows(stress.get('tests'), 'tests')
    if researched:
        need(1 <= len(tests) <= 2 or commitment.get('action') == 'stop' and not tests, '已研究须1–2个测试；仅停止原案可不给测试')
    else:
        need(not tests, '未开展时tests须为空')
    if not tests:
        fields(stress, 'no_test_reason', 'stress_test')
    for test in tests:
        need(test.get('belief_id') == bottleneck.get('belief_id') and test.get('belief_id') in belief_map if isinstance(test.get('belief_id'), str) else False, '测试必须针对唯一关键假设')
        fields(test, 'method observed_behavior metric inconclusive_rule failure_action resource_cap selection_reason', 'test')
        if six:
            choice(test.get('measures'), MEASURES, 'test.measures')
            fields(test, 'cannot_establish time_window sample_definition assistance', 'test')
        thresholds = []
        for key in ('pass_threshold', 'fail_threshold'):
            threshold = obj(test.get(key), key)
            choice(threshold.get('operator'), ('gte', 'lte'), key + '.operator')
            value = threshold.get('value')
            need(type(value) in (int, float) and math.isfinite(value), key + '.value须有限数值，不能布尔值')
            fields(threshold, 'unit', key)
            thresholds.append(threshold)
        passed, failed = thresholds
        need(passed.get('unit') == failed.get('unit'), '通过/失败门槛须同单位')
        pv, fv = passed.get('value'), failed.get('value')
        if type(pv) in (int, float) and type(fv) in (int, float) and math.isfinite(pv) and math.isfinite(fv):
            disjoint = (passed.get('operator') == 'gte' and failed.get('operator') == 'lte' and pv > fv or
                        passed.get('operator') == 'lte' and failed.get('operator') == 'gte' and pv < fv)
            need(disjoint, '通过与失败门槛必须互斥，不能重叠')
    adjacent = stress.get('adjacent')
    if adjacent is not None:
        adjacent = obj(adjacent, 'adjacent')
        cid = adjacent.get('direction_id')
        need(isinstance(cid, str) and cid in direction_map, '相邻论点须引用真实方向')
        if six:
            need(isinstance(cid, str) and cid in direction_map and direction_map[cid].get('stance') == 'recommended', '相邻推荐须引用stance=recommended的真实方向，不能把探索假设升级为推荐')
        fields(adjacent, 'summary', 'adjacent')
        supporting = refs(adjacent, 'evidence_ids', evidence, 'adjacent')
        need(bool(supporting), '更强相邻论点须有证据，不硬凑方向')
        need(any(evidence[eid].get('grade') in ('A', 'B', 'C') and evidence[eid].get('state') == 'fact' for eid in supporting if eid in evidence), '更强相邻方向须有A/B/C事实支撑；D/E仅能提出探索假设')
    hypothesis = stress.get('adjacent_hypothesis')
    if hypothesis is not None:
        need(six and researched, '探索相邻假设只用于已研究的六节综述')
        hypothesis = obj(hypothesis, 'adjacent_hypothesis')
        cid = hypothesis.get('direction_id')
        need(isinstance(cid, str) and cid in direction_map and direction_map[cid].get('stance') == 'explore', '探索相邻假设须引用stance=explore的真实方向，不能冒充推荐')
        fields(hypothesis, 'summary why_better new_risk missing_evidence', 'adjacent_hypothesis')
        if isinstance(adjacent, dict):
            need(cid != adjacent.get('direction_id'), '同一相邻方向不能同时是推荐和未验证假设')
    # Inspect only rendered overview text; provenance IDs and source URLs stay in data/body.
    if not errors:
        visible = markdown_stress_test(data, lambda value: str(value))
        reasons = [row.get('reason', '') for row in _objects(data.get('scorecard'))]
        need(not LINK_PATTERN.search(visible + '\n'.join(reasons)), '研究概览禁止链接；来源放详细分支')
        # Count visible prose, including labels; provenance IDs never enter this string.
        prose = re.sub(r'[#*≥≤\s]', '', visible) + ''.join(value for value in reasons if isinstance(value, str))
        need(len(prose) <= 1800, '研究概览过长，含评分理由最多1800字符')
    return errors
