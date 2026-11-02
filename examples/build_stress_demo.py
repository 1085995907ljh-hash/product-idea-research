"""Authored V6 presentation fixtures; no real market facts or model evaluation."""
from copy import deepcopy
import json
from pathlib import Path
import sys

from build_evals import deep_brief_fixture, record, assertion

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/product-idea-research'
sys.path.insert(0, str(SKILL / 'scripts'))
from report import V6, initial, render, validate


def build_fixture():
    d = deep_brief_fixture()
    d.update(schema_version=V6, title='合成阅读样例：一个 idea 现在值得投入多少', date='2026-11-02')
    d['conclusion'].update(verdict='conditional', summary='只值得测试一次真实迁移，暂不开发完整产品；用户抱怨重复录入，但现有表格也可能足够。')
    d['directions'] = d['directions'][:1]
    d['directions'][0]['stance'] = 'explore'
    d['briefing']['depth']['directions'] = d['briefing']['depth']['directions'][:1]
    d['evidence'] = [
        dict(id='E-support', type='D', grade='C', grade_reason='样例论坛用户自报，未直接观察行为。', state='fact', claim='合成讨论中有用户抱怨重复录入。', limitation='虚构样本，只展示证据结构，不能推断真实频率。', source_ids=['S3']),
        dict(id='E-oppose', type='A', grade='B', grade_reason='样例产品资料说明已有功能，不证明付费。', state='fact', claim='合成旧工具和表格已能完成主要任务。', limitation='虚构产品，不代表实际竞品能力或用户选择。', source_ids=['S1']),
        dict(id='E-proxy', type='C', grade='D', grade_reason='搜索兴趣是间接信号。', state='fact', claim='合成趋势只演示交互，不能说明购买需求。', limitation='曲线全部为synthetic，非Google Trends数据。', source_ids=['S3'])]
    s = initial('合成', '合成')['stress_test']
    s.pop('presentation', None)  # Freeze the original v0.7 presentation fixture.
    s.update(state='researched', thesis=dict(statement='为反复整理资料的个人用户减少一次重复录入，以付费小工具交换节省的时间。', founder_goal='默认独立开发者可维护的盈利小产品；这是推断。', decision='是否值得投入一个最小原型。'),
             beliefs=[dict(id=bid, claim=claim, category=category, status='mixed' if i == 0 else 'unknown', support_evidence_ids=['E-support'] if i == 0 else [], oppose_evidence_ids=['E-oppose'] if i == 0 else [], disconfirmation=dict(searched=True, summary='合成演示：对照了旧工具与不愿换软件的声音，真实行为仍未知。', source_ids=['S1', 'S3'])) for i, (bid, claim, category) in enumerate([
                 ('pain', '重复录入的麻烦足以让用户更换现办法。', 'pain'),
                 ('behavior', '用户在实际任务中会持续采用少一步的流程。', 'behavior'),
                 ('feasibility', '真实文件和系统权限下仍能稳定省步骤。', 'feasibility'),
                 ('payment', '节省的时间足以支持付费，并能触达同类用户。', 'retention_payment')])],
             bottleneck=dict(belief_id='pain', why='技术可以先模拟，是否值得换工具更会改变此刻的投入决定。', decision_if_true='继续做一个仅省重复录入的原型。', decision_if_false='停止独立工具，不用多功能掩盖弱价值。'),
             tests=[dict(belief_id='pain', method='用现有原型工具让5位有同样任务的人比较两种流程。', observed_behavior='观察一周内是否主动带来下一份真实任务；不以“不错”代替行为。', metric='5人中主动再次提交任务的人数', pass_threshold=dict(operator='gte', value=3, unit='人'), fail_threshold=dict(operator='lte', value=1, unit='人'), inconclusive_rule='2人或观察不完整时不加码，先说明原因。', failure_action='停止原案；只有新证据指出特定子群时才重开。', resource_cap='一周内；仅现成工具，不买服务、不建完整后端。', selection_reason='3人是这轮继续小试的预设门槛，不是市场基准；比口头意愿更接近迁移。')],
             adjacent=None, commitment=dict(action='test', summary='只为识别迁移价值投入一次小测试。', cap='不做完整产品，不因话题热度追加开发。', escalation_condition='看到预设的重复使用行为，并补核真实文件可实现性后再讨论。'))
    d['stress_test'] = s
    assert not validate(d), validate(d)
    return d


def main():
    d = build_fixture()
    cases = [record('v6-director-stress-brief', d, [assertion('v6-brief', 'Director contract retains four chapters and one bottleneck.', required=['研究综述', '必须成立的前提', '支持与反对的证据', '关键假设', '现在值得投入多少', '逐产品口碑'], forbidden=['## 一、研究概览'])])]
    proxy = deepcopy(d)
    proxy['evidence'][-1].update(validated=True, validation_scope='不能用间接指标证明购买。')
    cases.append(record('v6-reject-proxy-validation', proxy, [assertion('proxy', 'Proxy evidence cannot be validation.', required=['不能算验证'])], reject=True))
    overlap = deepcopy(d)
    overlap['stress_test']['tests'][0]['pass_threshold']['value'] = 1
    cases.append(record('v6-reject-overlap-thresholds', overlap, [assertion('threshold', 'Passing/failing sets must be disjoint.', required=['互斥'])], reject=True))
    path = SKILL / 'evals/output/cases.jsonl'
    previous = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    cases = [c for c in previous if not c['id'].startswith('v6-')] + cases
    path.write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in cases))
    root = ROOT / 'examples/stress-test-demo'
    root.mkdir(exist_ok=True)
    (root / 'research.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    render(root)
    print(root / 'report.html')


if __name__ == '__main__':
    main()
