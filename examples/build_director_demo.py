"""Synthetic six-section director brief; no live market claims."""
from copy import deepcopy
import json
from pathlib import Path

from build_stress_demo import build_fixture, ROOT, SKILL
from build_evals import record, assertion
from report import render, validate


def build():
    d = build_fixture()
    d['title'] = '合成样例：用户抱怨，不等于愿意换工具'
    d['conclusion']['summary'] = '能做一个减少重复录入的小工具，但目前不值得开发完整订阅App。样例里的现有工具已能完成主要任务；用户抱怨不能证明会换工具、反复用或付费。先看下一次真实任务会不会回来。'
    s = d['stress_test']
    s['presentation'] = 'investigator-six'
    s['bottleneck']['why'] = '用户第一次觉得省事，但每次仍要准备输入和核对结果；若这抵消省下的操作，下次就会回到原表格。这是合成失败假设，不是已观察的流失。'
    s['tests'][0].update(measures='return_use', time_window='首次任务后7天，须确有下一次同类任务。', sample_definition='5位反复整理资料且已有下一次任务的样例用户。', assistance='首次说明操作；后续不提醒、不催促提交。', cannot_establish='长期留存、实际付款和整个市场需求。')
    direction = d['directions'][0]
    direction.update(name='探索假设：在现有表格中减少一步', change='把独立订阅App改为现有流程中的一次性批量整理工具。', why='可能减少迁移负担；尚无新方向的需求或付款证据。', mvp_focus='只处理一次批量重复录入。', main_risk='与用户真实表格兼容和付费价值均未验证。')
    depth = d['briefing']['depth']['directions'][0]
    depth.update(description='在用户现有表格中减少一次批量整理步骤；仅为探索假设。', better_because='如果不愿迁移是瓶颈，嵌入原流程可能减少摩擦；尚未证明。')
    s['adjacent_hypothesis'] = dict(direction_id=direction['id'], summary='嵌入现有表格的批量整理工具，按一次任务交付。', why_better='若用户不愿换工具，留在原流程可能避开迁移问题；不依赖每天回访的订阅。', new_risk='真实文件兼容、授权及单次付费价值仍未知。', missing_evidence='没有新方向的真实使用或付款证据，不能叫已验证机会。')
    assert not validate(d), validate(d)
    cases = [record('v6-six-section-brief', d, [assertion('six', 'Six-section synthesis with a labelled adjacent hypothesis.', required=['1）一句话结论', '4）最可能杀死它的假设', '6）可能更强的相邻方向', '未验证的探索假设', '本次只测主动回访', '长期留存'], forbidden=['### 现在值得投入多少', '### 一句话论点'])])]
    invalid = deepcopy(d)
    invalid['directions'][0]['stance'] = 'recommended'
    cases.append(record('v6-six-reject-promoted-hypothesis', invalid, [assertion('hypothesis', 'Exploratory ideas cannot silently become recommendations.', required=['stance=explore'])], reject=True))
    invalid = deepcopy(d)
    del invalid['stress_test']['tests'][0]['cannot_establish']
    cases.append(record('v6-six-reject-unbounded-test', invalid, [assertion('bounded-test', 'Test must state what it cannot establish.', required=['cannot_establish'])], reject=True))
    invalid = deepcopy(d)
    hypothesis = invalid['stress_test'].pop('adjacent_hypothesis')
    invalid['stress_test']['adjacent'] = dict(direction_id=hypothesis['direction_id'], summary=hypothesis['summary'], evidence_ids=['E1'])
    cases.append(record('v6-six-reject-unvalidated-recommendation', invalid, [assertion('recommendation', 'An exploratory direction cannot be promoted through the adjacent field.', required=['stance=recommended'])], reject=True))
    path = SKILL / 'evals/output/cases.jsonl'
    previous = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    path.write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in previous if not c['id'].startswith('v6-six-')) + ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in cases))
    root = ROOT / 'examples/director-demo'
    root.mkdir(exist_ok=True)
    (root / 'research.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    render(root)
    print(root / 'report.html')
    return d


if __name__ == '__main__':
    build()
