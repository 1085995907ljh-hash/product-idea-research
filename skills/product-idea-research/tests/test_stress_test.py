"""Deterministic stress-test contract regressions, not market/model evaluations."""
import copy
from html import escape
from pathlib import Path
import re
import sys
import unittest
import json
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stress_test import SIX, director_reply, initial_stress_test, markdown_stress_test, validate_stress_test
from report import V6, initial, markdown, render, validate


def fixture():
    """Authored synthetic evidence: never represent this as a live research run."""
    data = dict(sources=[dict(id='S', status='verified', url='https://example.org')], directions=[],
                conclusion=dict(summary='仅适合一个小测试。'), scorecard=[], evidence=[
                    dict(id='E1', type='D', state='fact', claim='样例用户有现行土办法。', grade='A', grade_reason='记录的行为而非愿望。', limitation='合成样本，非市场证据。', source_ids=['S']),
                    dict(id='E2', type='A', state='fact', claim='样例旧工具已覆盖部分需求。', grade='B', grade_reason='产品本身可查的功能。', limitation='功能不等于有人付费。', source_ids=['S'])], stress_test=initial_stress_test())
    stress = data['stress_test']
    stress.update(state='researched', thesis=dict(statement='替样例用户节省一次重复录入。', founder_goal='个人可维护的小产品。', decision='是否值得做原型。'),
                  beliefs=[dict(id=bid, claim=claim, category=category, status='mixed' if i == 0 else 'unknown', support_evidence_ids=['E1'] if i == 0 else [], oppose_evidence_ids=['E2'] if i == 0 else [], disconfirmation=dict(searched=True, summary='已查替代方案；仍有未知。', source_ids=['S'])) for i, (bid, claim, category) in enumerate([('B1', '用户愿意为减少重复操作迁移。', 'behavior'), ('B2', '真实环境下可可靠完成。', 'feasibility'), ('B3', '节省的时间值得持续付费。', 'retention_payment')])],
                  bottleneck=dict(belief_id='B1', why='迁移行为最可能改变投入判断。', decision_if_true='追加小额原型投入。', decision_if_false='停止独立产品。'),
                  tests=[dict(belief_id='B1', method='让有同样任务的用户用可点击原型完成原任务。', observed_behavior='自发继续使用，而非口头赞同。', metric='五位用户中主动再次使用的人数', pass_threshold=dict(operator='gte', value=3, unit='人'), fail_threshold=dict(operator='lte', value=1, unit='人'), inconclusive_rule='两人时不加码，调整后重测。', failure_action='停止原案，保留现有工具。', resource_cap='仅使用已有原型工具。', selection_reason='比开发完整产品更便宜，并观察真实行为。')],
                  commitment=dict(action='test', summary='当前仅值得测试迁移。', cap='不开发完整产品。', escalation_condition='按事先门槛观察到重复行为。'))
    for test in stress['tests']:
        test.update(measures='return_use', time_window='一周内有下一次任务时。', sample_definition='五位有重复任务的合成用户。', assistance='后续不提醒。', cannot_establish='实际付款和长期留存。')
    return data


class StressTestContractTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_initial_unknown_is_valid_and_nonmutating(self):
        data = dict(sources=[], evidence=[], directions=[], scorecard=[], conclusion=dict(summary='尚未研究。'), stress_test=initial_stress_test())
        before = copy.deepcopy(data)
        self.assertEqual(validate_stress_test(data), [])
        self.assertEqual(data, before)
        data['stress_test']['commitment']['action'] = 'stop'
        self.assertTrue(any('未开展' in e for e in validate_stress_test(data)))

    def test_populated_preserves_legacy_types_and_unknowns(self):
        before = copy.deepcopy(self.data)
        self.assertEqual(validate_stress_test(self.data), [])
        self.assertEqual(self.data, before)
        self.assertEqual(self.data['evidence'][0]['type'], 'D')
        self.assertEqual(self.data['evidence'][0]['grade'], 'A')
        self.assertEqual(self.data['stress_test']['beliefs'][1]['status'], 'unknown')

    def test_proxy_or_assertion_never_validates(self):
        for grade in ('D', 'E'):
            data = copy.deepcopy(self.data)
            data['evidence'][0].update(grade=grade, validated=True, validation_scope='样例观察')
            self.assertTrue(any('不能算验证' in e for e in validate_stress_test(data)))
        self.data['evidence'][0].update(grade='A', state='inference', validated=True, validation_scope='样例观察')
        self.assertTrue(any('不能算验证' in e for e in validate_stress_test(self.data)))

    def test_validation_needs_scope_not_just_high_grade(self):
        self.data['evidence'][0]['validated'] = True
        self.assertTrue(any('validation_scope' in e for e in validate_stress_test(self.data)))
        self.data['evidence'][0]['validation_scope'] = '仅支持样例用户过去做过此行为。'
        self.assertEqual(validate_stress_test(self.data), [])

    def test_dangling_refs_and_unverified_strong_sources_fail(self):
        cases = [lambda d: d['stress_test']['beliefs'][0].update(support_evidence_ids=['missing']),
                 lambda d: d['evidence'][0].update(source_ids=['missing']),
                 lambda d: d['sources'][0].update(status='unverified')]
        for change in cases:
            data = copy.deepcopy(self.data)
            change(data)
            self.assertTrue(validate_stress_test(data))

    def test_one_existing_bottleneck_and_tests_target_it(self):
        for value in (None, [], {}, [self.data['stress_test']['bottleneck']]):
            data = copy.deepcopy(self.data)
            data['stress_test']['bottleneck'] = value
            self.assertTrue(validate_stress_test(data))
        self.data['stress_test']['tests'][0]['belief_id'] = 'B2'
        self.assertTrue(any('唯一关键假设' in e for e in validate_stress_test(self.data)))

    def test_thresholds_are_finite_disjoint_and_same_unit(self):
        for value in (True, float('nan'), float('inf'), '3'):
            data = copy.deepcopy(self.data)
            data['stress_test']['tests'][0]['pass_threshold']['value'] = value
            self.assertTrue(any('有限数值' in e for e in validate_stress_test(data)))
        for threshold in (dict(operator='gte', value=1, unit='人'), dict(operator='lte', value=3, unit='人'), dict(operator='gte', value=3, unit='次')):
            data = copy.deepcopy(self.data)
            data['stress_test']['tests'][0]['pass_threshold'] = threshold
            self.assertTrue(validate_stress_test(data))

    def test_counterevidence_and_search_are_not_optional(self):
        self.data['stress_test']['beliefs'][0]['oppose_evidence_ids'] = []
        self.assertTrue(any('须关联反证' in e for e in validate_stress_test(self.data)))
        self.data = fixture()
        self.data['stress_test']['beliefs'][1]['disconfirmation']['searched'] = False
        self.assertTrue(any('主动寻找反证' in e for e in validate_stress_test(self.data)))

    def test_stopping_can_skip_tests_only_with_reason(self):
        self.data['stress_test'].update(tests=[], commitment=dict(action='stop', summary='有独立反证，停止原案。', cap='不追加投入。', escalation_condition='出现改变结论的新行为证据。'), no_test_reason='该原案已有决定性限制，不建议另花时间测试。')
        self.assertEqual(validate_stress_test(self.data), [])
        del self.data['stress_test']['no_test_reason']
        self.assertTrue(any('no_test_reason' in e for e in validate_stress_test(self.data)))

    def test_adjacent_requires_real_direction_and_evidence(self):
        self.data['stress_test']['adjacent'] = dict(direction_id='missing', summary='另一个方向。', evidence_ids=[])
        self.assertTrue(validate_stress_test(self.data))
        self.data['directions'] = [dict(id='other', stance='recommended')]
        self.data['stress_test']['adjacent'].update(direction_id='other', evidence_ids=['E1'])
        self.assertEqual(validate_stress_test(self.data), [])
        self.data['evidence'][0]['grade'] = 'D'
        self.assertTrue(any('A/B/C事实' in e for e in validate_stress_test(self.data)))

    def test_verdict_commitment_and_completion_do_not_conflict(self):
        self.data['conclusion']['verdict'] = 'no_go'
        self.assertTrue(any('停止原案' in e for e in validate_stress_test(self.data)))
        data = initial('Unknown', 'Unknown')
        data['status'] = 'complete'
        self.assertTrue(any('已开展前提研究' in e for e in validate_stress_test(data)))

    def test_v6_render_zip_and_markdown_share_one_source(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root/'evals/output/fixtures/v6-director-stress-brief.json').read_text())
        self.assertEqual(data['schema_version'], V6)
        self.assertEqual(validate(data), [])
        before = copy.deepcopy(data)
        md = markdown(data)
        self.assertEqual(re.findall(r'^## (.+)$', md, re.M), ['一、研究综述', '二、市场调研', '三、竞品', '四、产品研究'])
        self.assertNotIn('https://', md.split('## 二、市场调研')[0])
        self.assertIn('关键前提的证据', md)
        detail = md.split('### 关键前提的证据', 1)[1].split('### 市场全貌', 1)[0]
        belief = data['stress_test']['beliefs'][0]
        self.assertIn('#### ' + belief['claim'], detail)
        self.assertIn('**支持 · C：**', detail)
        self.assertIn('**反对 · B：**', detail)
        self.assertIn('#### 其他已记录的线索', detail)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            raw = json.dumps(data, ensure_ascii=False)
            (path/'research.json').write_text(raw)
            html = render(path).read_text()
            payload = json.loads(re.search(r'id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
            self.assertEqual(payload['markdown'], md)
            self.assertEqual(payload['stress_test'], data['stress_test'])
            with zipfile.ZipFile(path/'research.zip') as z:
                self.assertEqual(z.read('research.json').decode(), raw)
                self.assertEqual(z.read('research.md').decode(), md)
                self.assertEqual(set(z.namelist()), {'research.json','research.md','sources.json'})
        self.assertEqual(data, before)

    def test_complete_v6_does_not_require_inventing_three_directions(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root/'evals/output/fixtures/v6-director-stress-brief.json').read_text())
        data.update(status='complete', fixture=False)
        for section in data['sections']:
            section['status'] = 'complete'
        data['directions'] = []
        data['briefing']['depth']['directions'] = []
        data['no_directions_reason'] = '本轮没有足够依据提出更强相邻方向。'
        self.assertEqual(validate(data), [])

    def test_complete_v6_still_requires_platform_coverage(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root/'evals/output/fixtures/v6-director-stress-brief.json').read_text())
        data.update(status='complete', fixture=False)
        for section in data['sections']:
            section['status'] = 'complete'
        data['briefing']['depth']['market']['social_platforms'] = []
        self.assertTrue(any('逐平台展示覆盖状态' in e for e in validate(data)))

    def test_markdown_is_link_free_and_uses_safe_text(self):
        self.data['conclusion']['summary'] = '<script>alert(1)</script>'
        def safe(value):
            return re.sub(r'([\\`*_{}\[\]()#+!|>])', r'\\\1', escape(str(value), quote=False))
        rendered = markdown_stress_test(self.data, safe)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertNotIn('https://', rendered)
        self.assertNotIn('E1', rendered)
        self.assertIn('拟定的决策规则', rendered)
        self.data['conclusion']['summary'] = 'Read https://example.org'
        self.assertTrue(any('禁止链接' in e for e in validate_stress_test(self.data)))

    def test_malformed_containers_never_crash(self):
        for key, value in [('stress_test', []), ('evidence', [None]), ('sources', {}), ('directions', None)]:
            data = copy.deepcopy(self.data)
            data[key] = value
            self.assertTrue(validate_stress_test(data))
        for key, value in [('beliefs', None), ('tests', [None]), ('thesis', []), ('adjacent', []), ('commitment', [])]:
            data = copy.deepcopy(self.data)
            data['stress_test'][key] = value
            self.assertTrue(validate_stress_test(data))

    def test_exploratory_direction_cannot_be_promoted_through_adjacent(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root/'evals/output/fixtures/v6-six-section-brief.json').read_text())
        hypothesis = data['stress_test'].pop('adjacent_hypothesis')
        data['stress_test']['adjacent'] = dict(direction_id=hypothesis['direction_id'], summary=hypothesis['summary'], evidence_ids=['E1'])
        self.assertTrue(any('stance=recommended' in e for e in validate(data)))

    def test_six_sections_split_chat_links_from_report_overview(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root/'evals/output/fixtures/v6-six-section-brief.json').read_text())
        md = markdown(data)
        overview = md.split('## 二、市场调研')[0]
        headings = re.findall(r'^### (.+)$', overview, re.M)
        self.assertEqual(headings, ['1）一句话结论', '2）必须成立的前提', '3）证据', '4）最可能杀死它的假设', '5）下一步最便宜的测试', '6）可能更强的相邻方向'])
        self.assertNotIn('https://', overview)
        reply = director_reply(data, lambda s: escape(str(s)))
        self.assertIn('https://example.org', reply)
        self.assertIn('未验证的探索假设', reply)
        self.assertIn('不能证明', reply)
        self.assertEqual(len(re.findall(r'^### ', reply, re.M)), 6)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path/'research.json').write_text(json.dumps(data, ensure_ascii=False))
            render(path)
            self.assertIn('https://example.org', (path/'director-reply.md').read_text())
            self.assertNotIn('https://', (path/'research.md').read_text().split('## 二、市场调研')[0])

    def test_six_tests_require_observation_scope(self):
        self.assertEqual(self.data['stress_test']['presentation'], SIX)
        for key in ['measures', 'cannot_establish', 'time_window', 'sample_definition', 'assistance']:
            data = copy.deepcopy(self.data)
            del data['stress_test']['tests'][0][key]
            self.assertTrue(any(key in e for e in validate_stress_test(data)))

    def test_hypothesis_is_not_an_evidenced_recommendation(self):
        s = self.data['stress_test']
        self.data['directions'] = [dict(id='other', stance='explore')]
        s['adjacent_hypothesis'] = dict(direction_id='other', summary='一个未验证方向。', why_better='可能减少迁移操作。', new_risk='真实授权未知。', missing_evidence='无真实使用/付款证据。')
        self.assertEqual(validate_stress_test(self.data), [])
        self.data['directions'][0]['stance'] = 'recommended'
        self.assertTrue(any('stance=explore' in e for e in validate_stress_test(self.data)))


if __name__ == '__main__':
    unittest.main()
