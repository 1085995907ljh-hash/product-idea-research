import copy
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from report import V1, V2, V3, V4, V5, V2_WEIGHTS, computed_directions, expanded_sections, initial, score, validate, markdown, render
from research_details import mindshare_counts


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.d=initial('Test','Idea',V1)
    def test_unknown_does_not_become_zero(self):
        self.assertEqual(validate(self.d),[])
        self.assertIsNone(score(self.d)['value'])
    def test_payment_cap_and_weighted_score(self):
        for r in self.d['scorecard']:
            r.update(value=5,reason='fixture',source_ids=['S'])
        self.d['sources']=[dict(id='S',title='fixture',url='https://example.org',status='verified',accessed_at='2026-10-27')]
        self.assertEqual(score(self.d)['value'],5)
        self.assertEqual(score(self.d)['stars'],2.5)
        self.d['payment_evidence_ids']=['S']
        self.assertEqual(score(self.d)['stars'],4)
    def test_unverified_cannot_support_fact_or_veto(self):
        self.d['sources']=[dict(id='S',title='fixture',url='https://example.org',status='unverified',accessed_at='2026-10-27')]
        self.d['evidence']=[dict(id='E1',type='A',state='fact',claim='unsupported',source_ids=['S'])]
        self.assertTrue(validate(self.d))
        self.d['evidence']=[];self.d['hard_vetoes']=[dict(reason='unsupported',source_ids=['S'])]
        self.assertTrue(validate(self.d))
    def test_failed_idea_requires_alternative_work(self):
        self.d['conclusion']['verdict']='no_go'
        self.assertTrue(any('候选' in x for x in validate(self.d)))
    def test_unsafe_source_and_partial_points(self):
        self.d['sources']=[dict(id='S',title='bad',url='javascript:alert(1)',status='verified',accessed_at='2026-10-27')]
        self.assertTrue(validate(self.d))
        self.d['sources'][0]['url']='https://example.org'
        self.d['trends']=[dict(keyword='test',group='test',window='12m',geo='US',reason='fixture',source_ids=['S'],points=[dict(date='2026-10-27',value=101,partial=False)])]
        self.assertTrue(validate(self.d))
    def test_out_of_range_score_and_duplicate_dimensions(self):
        self.d['scorecard'][0]['value']=0
        self.assertTrue(validate(self.d))

    def test_missing_evidence_type_is_validation_error(self):
        self.d['evidence']=[dict(id='E1',claim='test',state='hypothesis')]
        self.assertTrue(any('类别' in x for x in validate(self.d)))

    def test_markdown_preserves_quotes_and_limits(self):
        self.d['sources']=[dict(id='S',title='fixture',url='https://example.org',status='verified',accessed_at='2026-10-27')]
        self.d['evidence']=[dict(id='E1',type='D',state='fact',claim='Observation',quote='Original quote',limitation='Sample limit',source_ids=['S'])]
        self.d['competitors']=[dict(id='C1',name='Fixture',kind='manual',summary='Test',limitation='Not tested',source_ids=[])]
        self.assertEqual(validate(self.d),[])
        md=markdown(self.d)
        for text in ['Original quote','Sample limit','Not tested','人工办法']:
            self.assertIn(text,md)
        self.d=initial('Test','Idea',V1);self.d['scorecard'].append(copy.deepcopy(self.d['scorecard'][0]))
        self.assertTrue(validate(self.d))


class V2ContractTests(unittest.TestCase):
    def setUp(self):
        self.d = initial('Test', 'Idea', V2)

    def source(self, status='verified'):
        self.d['sources'] = [dict(id='S', title='Fixture only', url='https://example.org/a(b)?x=1&y=2', status=status, accessed_at='2026-10-27T12:00:00Z', published_at='2026-10-01')]

    def scores(self, value=4, certainty='supported', owner=None):
        self.source()
        for row in (owner or self.d)['scorecard']:
            row.update(value=value, certainty=certainty, reason='Test scoring only', source_ids=['S'])

    def test_v2_init_is_valid_unknown_and_nonmutating(self):
        self.assertEqual(self.d['schema_version'], V2)
        self.assertEqual(validate(self.d), [])
        before = copy.deepcopy(self.d)
        result = score(self.d)
        self.assertEqual(result['value'], 2.5)
        self.assertTrue(result['provisional'])
        self.assertEqual(result['unknown_dimensions'], list(V2_WEIGHTS))
        self.assertEqual((result['confidence'], result['confidence_value']), ('low', 0))
        self.assertEqual(result['label'], '证据不足，先补关键证据')
        self.assertIn('不代表已证实的中等表现', result['reason'])
        self.assertNotIn('stars', result)
        self.assertEqual(self.d, before)
        self.assertEqual(computed_directions(self.d)[0]['score'], result)

    def test_six_weighted_dimensions_and_separate_confidence(self):
        self.scores()
        rows = {r['dimension']: r for r in self.d['scorecard']}
        rows['attention'].update(value=5, certainty='supported')
        rows['competition'].update(value=2, certainty='inferred')
        rows['gap'].update(value=None, certainty='unknown', source_ids=[])
        rows['timing'].update(value=3, certainty='inferred')
        rows['validation'].update(value=5, certainty='supported')
        rows['solo_cost'].update(value=1, certainty='supported')
        result = score(self.d)
        # 1 + .4 + .625 + .3 + .75 + .1 = 3.175; coverage .6.
        self.assertEqual((result['value'], result['label']), (3.2, '证据不足，先补关键证据'))
        self.assertEqual((result['confidence'], result['confidence_value']), ('medium', .6))
        self.assertEqual(result['unknown_dimensions'], ['gap'])
        self.assertEqual(validate(self.d), [])

    def test_labels_use_unrounded_value_and_v2_has_no_payment_cap(self):
        for value, label in [(3.6, '优先验证'), (3.58, '小成本试'), (3, '小成本试'), (2.99, '先改方向'), (2.3, '先改方向'), (2.29, '不建议入场')]:
            with self.subTest(value=value):
                self.scores(value)
                result = score(self.d)
                self.assertEqual(result['label'], label)
        self.scores(5)
        self.assertEqual(score(self.d)['value'], 5)
        self.assertEqual(score(self.d)['label'], '优先验证')
        self.assertFalse(score(self.d)['provisional'])
        self.assertEqual(self.d['payment_evidence_ids'], [])

    def test_confidence_thresholds_and_low_coverage_label(self):
        self.source()
        rows = {r['dimension']: r for r in self.d['scorecard']}
        for key in ('attention', 'competition'):
            rows[key].update(value=5, certainty='supported', source_ids=['S'])
        self.assertEqual((score(self.d)['confidence'], score(self.d)['confidence_value']), ('medium', .4))
        rows['attention'].update(value=None, certainty='unknown', source_ids=[])
        rows['competition'].update(value=5, certainty='inferred', source_ids=['S'])
        rows['gap'].update(value=5, certainty='inferred', source_ids=['S'])
        self.assertEqual(score(self.d)['label'], '证据不足，先验证假设')
        self.scores()
        rows['gap'].update(value=None, certainty='unknown', source_ids=[])
        self.assertEqual((score(self.d)['confidence'], score(self.d)['confidence_value']), ('high', .75))

    def test_buildability_alone_cannot_imply_market_opportunity(self):
        self.source()
        rows = {r['dimension']: r for r in self.d['scorecard']}
        for key in ('validation', 'solo_cost'):
            rows[key].update(value=5, certainty='supported', source_ids=['S'])
        result = score(self.d)
        self.assertEqual((result['value'], result['confidence_value']), (3.1, .25))
        self.assertEqual(result['label'], '证据不足，先补关键证据')
        # Even sufficient overall coverage cannot substitute for a concrete gap.
        for key in ('attention', 'timing'):
            rows[key].update(value=5, certainty='supported', source_ids=['S'])
        self.assertEqual(score(self.d)['confidence'], 'medium')
        self.assertEqual(score(self.d)['label'], '证据不足，先补关键证据')
        self.d['conclusion']['verdict'] = 'no_go'
        self.assertEqual(score(self.d)['label'], '不建议按原方案入场')

    def test_no_go_and_veto_change_label_not_score_or_adjacent_direction(self):
        self.scores(5)
        self.scores(4, owner=self.d['directions'][0])
        self.d['conclusion']['verdict'] = 'no_go'
        self.d['hard_vetoes'] = [dict(reason='Verified constraint fixture', source_ids=['S'])]
        self.assertEqual(validate(self.d), [])
        result = score(self.d)
        self.assertEqual((result['value'], result['label']), (5, '不建议按原方案入场'))
        self.assertEqual(computed_directions(self.d)[0]['score']['label'], '优先验证')
        self.d['sources'][0]['status'] = 'unverified'
        self.assertTrue(validate(self.d))

    def test_v2_scores_require_certainty_and_verified_references(self):
        self.scores()
        self.d['sources'][0]['status'] = 'unverified'
        self.assertTrue(any('未核实来源' in x for x in validate(self.d)))
        self.source()
        self.d['scorecard'][0].update(value=None, certainty='supported')
        self.assertTrue(any('certainty' in x for x in validate(self.d)))
        self.d['scorecard'][0].update(value=4, certainty='unknown')
        self.assertTrue(any('certainty' in x for x in validate(self.d)))
        self.d['scorecard'][0].update(certainty='inferred', source_ids=[])
        self.assertTrue(any('缺少来源' in x for x in validate(self.d)))
        self.d['scorecard'].pop()
        self.assertTrue(any('六个维度' in x for x in validate(self.d)))

    def test_six_sections_order_reasons_and_complete_coverage(self):
        self.d['sections'].reverse()
        self.assertTrue(any('六章' in x for x in validate(self.d)))
        self.d = initial('Test', 'Idea', V2)
        self.d['conclusion']['reasons'] = ['a', 'b', 'c', 'd']
        self.assertTrue(any('三条' in x for x in validate(self.d)))
        self.d['conclusion']['reasons'] = []
        self.d['status'] = 'complete'
        self.assertTrue(any('未完成章节' in x for x in validate(self.d)))
        for section in self.d['sections']:
            section['status'] = 'complete'
        self.assertEqual(validate(self.d), [])

    def test_direction_count_identity_and_recommendation_evidence(self):
        self.d['directions'][0]['stance'] = 'recommended'
        self.assertTrue(any('已核实来源' in x for x in validate(self.d)))
        self.source()
        self.d['directions'][0]['source_ids'] = ['S']
        self.assertEqual(validate(self.d), [])
        other = copy.deepcopy(self.d['directions'][0])
        other['id'] = 'second'
        self.d['directions'].append(other)
        self.assertTrue(any('最多一个' in x for x in validate(self.d)))
        other['stance'] = 'explore'
        self.assertEqual(validate(self.d), [])
        other['id'] = self.d['directions'][0]['id']
        self.assertTrue(any('方向 ID' in x for x in validate(self.d)))
        self.d['directions'] = []
        self.assertTrue(any('一至三条' in x for x in validate(self.d)))

    def test_section_references_and_table_shape_are_checked(self):
        self.d['sections'][0]['source_ids'] = ['missing']
        self.assertTrue(any('不存在' in x for x in validate(self.d)))
        self.d['sections'][0]['source_ids'] = []
        self.d['sections'][0]['blocks'] = [dict(type='table', headers=['a', 'b'], rows=[['one']], source_ids=[])]
        self.assertTrue(any('列数' in x for x in validate(self.d)))
        self.d['sections'][0]['blocks'][0]['rows'] = [['one', 'two']]
        self.assertEqual(validate(self.d), [])

    def test_markdown_order_folded_details_and_plain_text(self):
        self.source()
        self.d['decision']['mvp_focus'] = 'Only one outcome'
        self.d['sections'][0]['blocks'] = [dict(type='paragraph', text='<script>alert(1)</script> [unsafe](javascript:alert(1))', source_ids=['S'])]
        self.d['competitors'] = [dict(id='C', name='Fixture competitor', kind='manual', source_ids=['S'])]
        self.d['trends'] = [dict(keyword='Fixture trend', group='comparison', window='12m', geo='US', category='All', search_type='Web', granularity='weekly', reason='Fixture, not research', source_ids=['S'], points=[dict(date='2026-10-01', value=0, partial=False), dict(date='2026-10-08', value=None, partial=False), dict(date='2026-10-15', value=20, partial=True)])]
        self.assertEqual(validate(self.d), [])
        md = markdown(self.d)
        self.assertLess(md.index('Only one outcome'), md.index('## 需求与近期话题'))
        self.assertLess(md.index('## 市场规模与走势'), md.index('### 搜索兴趣走势'))
        self.assertLess(md.index('### 搜索兴趣走势'), md.index('## 竞品与差评'))
        self.assertLess(md.index('### 竞品与替代清单'), md.index('## 外部环境与平台'))
        self.assertIn('<summary>评分依据</summary>', md)
        self.assertIn('&lt;script&gt;', md)
        self.assertNotIn('<script>', md)
        self.assertIn(r'\[unsafe\]', md)
        self.assertIn('https://example.org/a%28b%29?x=1&y=2', md)
        self.assertIn('| 2026-10-08 | 缺失/低量 | 否 |', md)
        self.assertIn('| 2026-10-15 | 20 | 是 |', md)
        self.assertIn('粒度：weekly', md)
        self.assertNotIn('星', md)

    def test_malformed_container_shapes_return_validation_errors(self):
        for key, value in [('sections', {}), ('sources', [None]), ('scorecard', 'bad'), ('directions', [None]), ('evidence', {})]:
            with self.subTest(key=key):
                malformed = copy.deepcopy(self.d)
                malformed[key] = value
                self.assertTrue(validate(malformed))
        for key in ('sources', 'evidence', 'competitors', 'trends', 'glossary', 'scorecard', 'sections'):
            with self.subTest(missing=key):
                malformed = copy.deepcopy(self.d)
                del malformed[key]
                self.assertTrue(validate(malformed))

    def test_render_payload_zip_allowlist_and_disk_consistency(self):
        self.d['title'] = '</script><script>unsafe()</script>'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = json.dumps(self.d, ensure_ascii=False, indent=2) + '\n'
            (root/'research.json').write_text(raw, encoding='utf-8')
            (root/'access.json').write_text('private diagnostics')
            (root/'raw').mkdir()
            (root/'raw/private.txt').write_text('private input')
            html = render(root).read_text(encoding='utf-8')
            payload = json.loads(re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
            self.assertEqual(payload['computed_score'], score(self.d))
            self.assertEqual(payload['computed_directions'], computed_directions(self.d))
            self.assertEqual(payload['markdown'], (root/'research.md').read_text(encoding='utf-8'))
            self.assertEqual(base64.b64decode(payload['zip_base64']), (root/'research.zip').read_bytes())
            with zipfile.ZipFile(root/'research.zip') as archive:
                self.assertEqual(set(archive.namelist()), {'research.json', 'research.md', 'sources.json'})
                self.assertEqual(archive.read('research.json'), raw.encode())
                self.assertEqual(archive.read('research.md'), (root/'research.md').read_bytes())
            self.assertEqual((root/'research.json').read_text(encoding='utf-8'), raw)
            self.assertNotIn('</script><script>unsafe()', html)
            self.assertNotIn('computed_score', json.loads(raw))

    def test_cli_init_explicit_v1_and_v2_still_render(self):
        script = Path(__file__).resolve().parents[1]/'scripts/report.py'
        with tempfile.TemporaryDirectory() as folder:
            for version in ('v2', 'v1'):
                root = Path(folder)/version
                args = [sys.executable, str(script), 'init', str(root), '--title', 'Fixture', '--idea', 'Fixture idea', '--schema-version', version]
                subprocess.run(args, check=True, capture_output=True)
                data = json.loads((root/'research.json').read_text())
                self.assertEqual(data['schema_version'], 'product-idea-research/' + version)
                subprocess.run([sys.executable, str(script), 'validate', str(root)], check=True, capture_output=True)
                subprocess.run([sys.executable, str(script), 'render', str(root)], check=True, capture_output=True)
                html = (root/'report.html').read_text()
                payload = json.loads(re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
                if version == 'v1':
                    self.assertEqual(set(payload['computed_score']), {'value', 'stars', 'reason'})
                    self.assertNotIn('computed_directions', payload)


class V3ContractTests(unittest.TestCase):
    def setUp(self):
        self.d = initial('Fixture tests only', 'Not a market claim', V3)
        self.d['fixture'] = True

    def populated(self):
        d = self.d
        d['sources'] = [dict(id=sid, title='Fixture ' + sid, url='https://example.org/' + sid, status='verified', accessed_at='2026-10-28') for sid in ('S1', 'S2')]
        d['social_research']['platforms'] = [dict(id='platform', name='Fixture platform', status='available', query_scope='Fixture need queries', time_range='Fixture range', discussion='Fixture discussion', assessment='Fixture assessment', limitation='Synthetic contract test only', source_ids=['S1'])]
        posts = []
        for pid, author, brands in [('P1', 'author-a', ['C1']), ('P2', 'author-b', []), ('P3', 'author-a', ['C1', 'C2'])]:
            posts.append(dict(id=pid, platform_id='platform', author_key=author, published_at='2026-10-01', region='US (fixture)', state='verified', query_origin='need', behavior='problem', context='Fixture context ' + pid, quote=None, brand_mentions=brands, source_ids=['S1']))
        d['social_research']['posts'] = posts
        d['social_research']['pains'] = [dict(id='pain', name='Fixture pain', audience='Fixture audience', situation='Fixture situation', current_workaround='Fixture workaround', problem='Fixture problem', consequence='Fixture consequence', recurrence='Two fixture authors', counterevidence='Fixture counterevidence', status='recurring', post_ids=['P1', 'P2'], source_ids=['S1'])]
        d['competitors'] = [dict(id=cid, name='Fixture ' + cid, kind='manual' if cid == 'C2' else 'direct', summary='Fixture summary', pricing='Not a real price', limitation='Fixture only', positioning='Fixture positioning', audience='Fixture audience', category_ids=['category'], official_keywords=[], user_keywords=[], strengths=['Fixture strength'], weaknesses=['Fixture limitation'], source_ids=[sid]) for cid, sid in [('C1', 'S1'), ('C2', 'S2')]]
        ca = d['competitive_analysis']
        ca['categories'] = [dict(id='category', name='Fixture task category', description='Fixture category scope', competitor_ids=['C1', 'C2'], source_ids=['S1', 'S2'])]
        ca['feature_competitor_ids'] = ['C1', 'C2']
        ca['features'] = [dict(id='feature', name='Fixture decisive feature', cells=[dict(competitor_id='C1', state='yes', basis='Fixture verified basis', source_ids=['S1']), dict(competitor_id='C2', state='unknown', basis='Not verified', source_ids=[])])]
        ca['reviews'] = [dict(id=rid, competitor_id=cid, rating=rating, published_at='2026-10-01', version=None, summary='Fixture review ' + rid, quote=None, source_ids=[sid]) for rid, cid, rating, sid in [('R1', 'C1', 5, 'S1'), ('R2', 'C1', 2, 'S2'), ('R3', 'C2', 4, 'S2')]]
        ca['review_coverage'] = [dict(competitor_id=cid, scope='Selected fixture reviews', time_range='Fixture range', limitation='Not representative', source_ids=[sid]) for cid, sid in [('C1', 'S1'), ('C2', 'S2')]]
        ca['review_themes'] = [dict(id=tid, sentiment=sentiment, theme='Fixture theme ' + tid, task='Fixture task', impact='Fixture impact', current_status='unknown', assessment='Status not verified', competitor_ids=['C1'], review_ids=[rid], source_ids=[sid]) for tid, sentiment, rid, sid in [('T1', 'positive', 'R1', 'S1'), ('T2', 'negative', 'R2', 'S2')]]
        ca['mindshare'].update(status='measured', summary='Fixture eligible sample', eligible_post_ids=['P1', 'P2', 'P3'], limitation='Sample mentions only, not market share')
        return d

    def direction(self):
        direction = copy.deepcopy(initial('Fixture', 'Fixture', V2)['directions'][0])
        direction.update(id='direction', stance='recommended', pain_ids=['pain'], competitor_ids=['C1'], existing_alternatives='Fixture competitor and workaround', remaining_gap='Fixture remaining gap', source_ids=['S1'])
        self.d['directions'] = [direction]
        return direction

    def test_default_v3_unknown_structure_and_zero_directions(self):
        self.assertEqual(self.d['schema_version'], V3)
        self.assertEqual(validate(self.d), [])
        self.assertEqual(self.d['directions'], [])
        self.assertTrue(self.d['no_directions_reason'])
        self.assertEqual(self.d['need_assessment']['classification'], 'unknown')
        self.assertEqual(self.d['competitive_analysis']['mindshare']['status'], 'insufficient')
        self.assertEqual(computed_directions(self.d), [])
        self.assertEqual(score(self.d)['value'], 2.5)
        self.assertTrue(score(self.d)['provisional'])
        self.assertIn(self.d['no_directions_reason'], markdown(self.d))
        del self.d['no_directions_reason']
        self.assertTrue(any('no_directions_reason' in error for error in validate(self.d)))

    def test_recurring_pain_requires_distinct_verified_natural_authors(self):
        self.populated()
        self.assertEqual(validate(self.d), [])
        pain = self.d['social_research']['pains'][0]
        pain['post_ids'] = ['P1', 'P3']
        self.assertTrue(any('独立用户' in error for error in validate(self.d)))
        pain['post_ids'] = ['P1', 'P2']
        second = self.d['social_research']['posts'][1]
        for change in [dict(behavior='creator'), dict(behavior='promotion'), dict(state='unverified')]:
            with self.subTest(change=change):
                old = copy.deepcopy(second)
                second.update(change)
                self.assertTrue(any('独立用户' in error for error in validate(self.d)))
                second.clear(); second.update(old)

    def test_feature_claims_need_verified_evidence_and_exact_coverage(self):
        self.populated()
        feature = self.d['competitive_analysis']['features'][0]
        feature['cells'][0]['source_ids'] = []
        self.assertTrue(any('缺来源' in error for error in validate(self.d)))
        feature['cells'][0].update(state='unknown', source_ids=[])
        self.assertEqual(validate(self.d), [])
        feature['cells'][0].update(state='no', source_ids=['S1'])
        self.d['sources'][0]['status'] = 'unverified'
        self.assertTrue(any('未核实来源' in error for error in validate(self.d)))
        self.d['sources'][0]['status'] = 'verified'
        feature['cells'][1]['competitor_id'] = 'C1'
        self.assertTrue(any('恰好覆盖' in error for error in validate(self.d)))

    def test_review_themes_match_products_and_ratings(self):
        self.populated()
        theme = self.d['competitive_analysis']['review_themes'][0]
        theme['review_ids'] = ['R2']
        self.assertTrue(any('星级不匹配' in error for error in validate(self.d)))
        theme['review_ids'] = ['R3']
        self.assertTrue(any('产品不匹配' in error for error in validate(self.d)))
        theme['review_ids'] = ['R1']
        self.d['competitive_analysis']['reviews'][0]['rating'] = True
        self.assertTrue(any('1–5整数' in error for error in validate(self.d)))
        self.d['competitive_analysis']['reviews'][0]['rating'] = 5
        self.assertEqual(validate(self.d), [])
        blocks = expanded_sections(self.d)[2]['blocks']
        coverage = next(b for b in blocks if b['title'] == '评价样本覆盖')
        self.assertEqual(coverage['rows'][0][1], '2条 / 好评1 / 低星1')

    def test_mindshare_deduplicates_authors_and_keeps_nonmentioners(self):
        self.populated()
        result = mindshare_counts(self.d)
        self.assertEqual(result['denominator'], 2)
        self.assertEqual({r['competitor_id']: r['count'] for r in result['rows']}, {'C1': 1, 'C2': 1})
        rows = next(b for b in expanded_sections(self.d)[2]['blocks'] if b['title'] == '本次样本品牌主动提及（不是市场份额）')['rows']
        self.assertEqual([r[1] for r in rows], ['1/2', '1/2'])
        self.assertEqual(validate(self.d), [])

    def test_mindshare_excludes_brand_search_ads_creators_and_unverified(self):
        self.populated()
        post = self.d['social_research']['posts'][2]
        for change in [dict(query_origin='brand'), dict(query_origin='other'), dict(behavior='promotion'), dict(behavior='creator'), dict(state='unverified')]:
            with self.subTest(change=change):
                old = copy.deepcopy(post)
                post.update(change)
                self.assertTrue(any('分母只能' in error for error in validate(self.d)))
                post.clear(); post.update(old)
        ms = self.d['competitive_analysis']['mindshare']
        ms['status'] = 'insufficient'
        self.assertTrue(any('不得携带' in error for error in validate(self.d)))
        ms['eligible_post_ids'] = []
        self.assertEqual(validate(self.d), [])
        self.assertIsNone(mindshare_counts(self.d))
        self.assertFalse(any(b['title'].startswith('本次样本品牌主动提及') for b in expanded_sections(self.d)[2]['blocks']))

    def test_recommended_direction_needs_real_pain_and_verified_alternative(self):
        self.populated()
        direction = self.direction()
        self.assertEqual(validate(self.d), [])
        direction['pain_ids'] = []
        self.assertTrue(any('用户痛点' in error for error in validate(self.d)))
        direction['pain_ids'] = ['pain']
        direction['competitor_ids'] = []
        self.assertTrue(any('替代/竞品' in error for error in validate(self.d)))
        direction['competitor_ids'] = ['C1']
        direction['remaining_gap'] = ''
        self.assertTrue(any('remaining_gap' in error for error in validate(self.d)))

    def test_categories_are_bidirectional_and_detail_ids_unique(self):
        self.populated()
        self.d['competitive_analysis']['categories'][0]['competitor_ids'] = ['C1']
        self.assertTrue(any('双向一致' in error for error in validate(self.d)))
        self.d['competitive_analysis']['categories'][0]['competitor_ids'] = ['C1', 'C2']
        self.d['social_research']['posts'][1]['id'] = 'P1'
        self.assertTrue(any('ID缺失或重复' in error for error in validate(self.d)))

    def test_collapsed_titles_and_per_row_references_are_validated(self):
        block = dict(type='table', title='Fixture folded table', collapsed=True, headers=['Item'], rows=[['row-a'], ['row-b']], row_source_ids=[[], []], source_ids=[])
        self.d['sections'][0]['blocks'] = [block]
        self.assertEqual(validate(self.d), [])
        for key, value, message in [('title', '', 'title'), ('collapsed', 'yes', 'collapsed'), ('row_source_ids', [[]], '等长'), ('row_source_ids', [[], ['missing']], '不存在'), ('row_source_ids', [[], 'S1'], '数组')]:
            with self.subTest(key=key, value=value):
                before = copy.deepcopy(block)
                block[key] = value
                self.assertTrue(any(message in error for error in validate(self.d)))
                block.clear(); block.update(before)

    def test_shared_expansion_markdown_payload_row_links_and_zip(self):
        self.populated()
        self.d['sections'][0]['blocks'] = [dict(type='table', title='Fixture folded <text>', collapsed=True, headers=['Item'], rows=[['unique row-a'], ['unique row-b']], row_source_ids=[['S1'], ['S2']], source_ids=[])]
        before = copy.deepcopy(self.d)
        expected_sections = expanded_sections(self.d)
        self.assertEqual(validate(self.d), [])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = json.dumps(self.d, ensure_ascii=False, indent=2) + '\n'
            (root/'research.json').write_text(raw, encoding='utf-8')
            (root/'access.json').write_text('private')
            html = render(root).read_text(encoding='utf-8')
            payload = json.loads(re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
            md = (root/'research.md').read_text(encoding='utf-8')
            self.assertEqual(payload['sections'], expected_sections)
            self.assertEqual(payload['markdown'], md)
            self.assertEqual(markdown(self.d), md)
            for text in ['不同平台在讨论什么', 'Fixture workaround', 'Fixture counterevidence', '关键功能差异', 'Fixture decisive feature', '好评：用户为什么留下', '差评：用户遇到了什么问题', 'Fixture review R1']:
                self.assertIn(text, md)
                self.assertIn(text, json.dumps(payload['sections'], ensure_ascii=False))
            self.assertIn('| unique row-a [S1](https://example.org/S1) |', md)
            self.assertIn('| unique row-b [S2](https://example.org/S2) |', md)
            self.assertIn('<summary>Fixture folded &lt;text&gt;</summary>', md)
            self.assertIn('<summary>代表讨论与取证边界</summary>', md)
            self.assertIn('<summary>评论明细</summary>', md)
            self.assertEqual(base64.b64decode(payload['zip_base64']), (root/'research.zip').read_bytes())
            with zipfile.ZipFile(root/'research.zip') as archive:
                self.assertEqual(set(archive.namelist()), {'research.json', 'research.md', 'sources.json'})
                self.assertEqual(archive.read('research.json'), raw.encode())
                self.assertEqual(archive.read('research.md'), md.encode())
            self.assertEqual((root/'research.json').read_text(encoding='utf-8'), raw)
        self.assertEqual(self.d, before)

    def test_malformed_deep_containers_return_errors(self):
        self.populated()
        cases = [('social_research', None), ('need_assessment', []), ('competitive_analysis', []), ('sources', None), ('directions', [None])]
        for key, value in cases:
            with self.subTest(key=key):
                malformed = copy.deepcopy(self.d)
                malformed[key] = value
                self.assertTrue(validate(malformed))
        nested = [('social_research', 'posts', [None]), ('social_research', 'pains', {}), ('competitive_analysis', 'features', [None]), ('competitive_analysis', 'mindshare', None), ('competitive_analysis', 'review_coverage', None)]
        for owner, key, value in nested:
            with self.subTest(owner=owner, key=key):
                malformed = copy.deepcopy(self.d)
                malformed[owner][key] = value
                self.assertTrue(validate(malformed))
        malformed = copy.deepcopy(self.d)
        malformed['social_research']['posts'][0]['behavior'] = []
        self.assertTrue(validate(malformed))
        malformed = copy.deepcopy(self.d)
        malformed['competitors'][0]['category_ids'] = None
        self.assertTrue(validate(malformed))

    def test_cli_defaults_v5_and_does_not_overwrite_existing_research(self):
        script = Path(__file__).resolve().parents[1]/'scripts/report.py'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'new'
            args = [sys.executable, str(script), 'init', str(root), '--title', 'Fixture', '--idea', 'Fixture idea']
            subprocess.run(args, check=True, capture_output=True)
            data = json.loads((root/'research.json').read_text())
            self.assertEqual(data['schema_version'], V5)
            self.assertEqual(data['directions'], [])
            subprocess.run([sys.executable, str(script), 'validate', str(root)], check=True, capture_output=True)
            subprocess.run([sys.executable, str(script), 'render', str(root)], check=True, capture_output=True)
            self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)
            self.assertEqual(json.loads((root/'research.json').read_text()), data)


class V4BriefingTests(unittest.TestCase):
    def setUp(self):
        self.d = initial('Fixture only', 'Not market evidence', V4)
        self.d['fixture'] = True

    def test_four_chapters_and_link_free_overview_in_markdown_and_payload(self):
        self.assertEqual(validate(self.d), [])
        self.assertEqual(self.d['schema_version'], V4)
        md = markdown(self.d)
        self.assertEqual(re.findall(r'^## (.+)$', md, re.M), ['一、研究概览', '二、市场调研', '三、竞品', '四、产品研究'])
        overview = md.split('## 二、市场调研')[0]
        self.assertNotIn('https://', overview)
        for forbidden in ('先验证什么', '依据与缺口', '方向建议与 MVP'):
            self.assertNotIn('## ' + forbidden, md)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'research.json').write_text(json.dumps(self.d))
            render(root)
            html = (root/'report.html').read_text()
            payload = json.loads(re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
            self.assertEqual(payload['markdown'], md)
            self.assertEqual([s['id'] for s in payload['sections']], ['market','competition','product'])
            self.assertIn('竞品定性四象限', html)

    def test_reject_overview_links_and_excess_length(self):
        self.d['briefing']['executive']['recommendation'] = 'see https://example.org'
        self.assertTrue(any('禁止链接' in x for x in validate(self.d)))
        self.d['briefing']['executive']['recommendation'] = '长'*1000
        self.assertTrue(any('过长' in x for x in validate(self.d)))

    def test_quadrants_require_existing_competitors_and_sources(self):
        self.d['briefing']['landscape']['entries'] = [dict(competitor_id='invented',quadrant='top-left',source_ids=[])]
        self.assertTrue(any('四象限竞品不存在' in x for x in validate(self.d)))
        self.assertTrue(any('可追溯来源' in x for x in validate(self.d)))

    def test_feature_and_review_selection_cannot_invent_objects(self):
        self.d['briefing']['feature_ids'] = ['made-up']
        self.d['briefing']['review_ids'] = ['made-up']
        self.assertTrue(any('feature_ids' in x for x in validate(self.d)))
        self.assertTrue(any('review_ids' in x for x in validate(self.d)))

    def test_malformed_briefing_is_rejected_without_crash(self):
        for key in ('executive','landscape','competition_judgment'):
            d = copy.deepcopy(self.d)
            d['briefing'][key] = []
            self.assertTrue(validate(d))


class V5DepthTests(unittest.TestCase):
    def setUp(self):
        self.d = initial('Fixture only', 'Not market evidence')
        self.d['fixture'] = True

    def populated(self):
        V3ContractTests.populated(self)
        V3ContractTests.direction(self)
        self.d['directions'][0]['stance'] = 'explore'
        b = self.d['briefing']
        b.update(selected_competitor_ids=['C1', 'C2'], feature_ids=['feature'], review_ids=['R1', 'R2', 'R3'])
        depth = b['depth']
        depth['market'].update(
            social_platforms=[dict(id='platform', label='Fixture platform', state='available', summary='Fixture platform summary', pain='Fixture platform pain', opportunity='Fixture platform opportunity', post_ids=['P1', 'P2'], source_ids=['S1'])],
            social_findings=[dict(title='Fixture finding', need='Fixture need', newness='Fixture new context', opportunity='Fixture opportunity', avoid='Fixture avoid', source_ids=['S1'])],
            keyword_groups=[dict(id='need', title='Fixture need terms', intent='Problem-led intent', keywords=['fixture need'], summary='Fixture group summary', source_ids=['S1']), dict(id='alternative', title='Fixture alternative terms', intent='Alternative-led intent', keywords=['fixture alternative'], summary='Fixture alternative summary', source_ids=['S2'])])
        self.d['trends'] = [dict(keyword=term, group=group, window=window, geo='US', category='All', search_type='Web', granularity='weekly', reason='Fixture only, not market evidence', source_ids=['S1'], points=[dict(date='2026-10-01', value=10, partial=False), dict(date='2026-10-08', value=None, partial=False), dict(date='2026-10-15', value=20, partial=True)]) for group, term in [('need', 'fixture need'), ('alternative', 'fixture alternative')] for window in ['30d', '12m']]
        depth['competition'].update(
            catalog_groups=[dict(id='task', title='Fixture task catalog', description='Fixture catalog description', competitor_ids=['C1', 'C2'], source_ids=['S1', 'S2'])],
            selection=[dict(competitor_id=cid, roles=['leader' if cid == 'C1' else 'adjacent'], reason='Fixture reason ' + cid, source_ids=[sid]) for cid, sid in [('C1', 'S1'), ('C2', 'S2')]],
            feature_groups=[dict(id='job', title='Fixture job chain', job='Fixture user job', feature_ids=['feature'], takeaway='Fixture task takeaway', source_ids=['S1'])],
            product_reviews=[dict(competitor_id=cid, state='available', summary='Fixture product summary ' + cid, positive=['Fixture positive'], negative=['Fixture negative'] if cid == 'C1' else [], judgment='Fixture product judgment ' + cid, review_ids=rids, source_ids=[sid]) for cid, rids, sid in [('C1', ['R1', 'R2'], 'S1'), ('C2', ['R3'], 'S2')]])
        depth['directions'] = [dict(direction_id='direction', description='Fixture direction description', pain='Fixture direction pain', better_because='Fixture better because', cost=dict(level='low', build='Fixture build cost', ongoing='Fixture ongoing cost'), feasibility=dict(verdict='conditional', summary='Fixture feasibility', dependencies=['Fixture platform dependency']), source_ids=['S1'])]
        return self.d

    def test_initial_is_valid_unknown_v5_and_keeps_four_chapters(self):
        self.assertEqual(self.d['schema_version'], V5)
        self.assertEqual(validate(self.d), [])
        md = markdown(self.d)
        self.assertEqual(re.findall(r'^## (.+)$', md, re.M), ['一、研究概览', '二、市场调研', '三、竞品', '四、产品研究'])
        self.assertNotIn('https://', md.split('## 二、市场调研')[0])

    def test_depth_references_cannot_invent_or_mix_records(self):
        self.populated()
        self.assertEqual(validate(self.d), [])
        cases = [
            ('market', 'social_platforms', 'post_ids', ['invented'], 'post_ids'),
            ('market', 'social_findings', 'source_ids', [], '缺少来源'),
            ('competition', 'catalog_groups', 'competitor_ids', ['invented'], 'competitor_ids'),
            ('competition', 'selection', 'competitor_id', 'invented', 'selection'),
            ('competition', 'feature_groups', 'feature_ids', ['invented'], 'feature_ids'),
            ('competition', 'product_reviews', 'review_ids', ['R3'], '产品不匹配'),
        ]
        for owner, key, field, value, expected in cases:
            with self.subTest(field=field, key=key):
                d = copy.deepcopy(self.d)
                d['briefing']['depth'][owner][key][0][field] = value
                self.assertTrue(any(expected in e for e in validate(d)))
        d = copy.deepcopy(self.d)
        d['social_research']['platforms'].append(dict(d['social_research']['platforms'][0], id='other'))
        d['social_research']['posts'][0]['platform_id'] = 'other'
        self.assertTrue(any('原帖与平台不匹配' in e for e in validate(d)))
        d = copy.deepcopy(self.d)
        d['briefing']['depth']['directions'][0]['direction_id'] = 'invented'
        self.assertTrue(any('逐一覆盖详细directions' in e for e in validate(d)))
        d = copy.deepcopy(self.d)
        d['trends'][0]['group'] = 'invented'
        self.assertTrue(any('对应keyword_groups.id' in e for e in validate(d)))

    def test_missing_reviews_are_explicit_without_fabricated_sentiment(self):
        self.populated()
        review = self.d['briefing']['depth']['competition']['product_reviews'][1]
        review.update(state='blocked', review_ids=[], positive=[], negative=[], source_ids=[])
        self.d['briefing']['review_ids'].remove('R3')
        self.assertEqual(validate(self.d), [])
        md = markdown(self.d)
        self.assertIn('Fixture C2 · 访问受限', md)
        self.assertIn('本轮未取得足够材料，不作结论。', md)
        review['positive'] = ['Invented positive']
        self.assertTrue(any('缺失口碑' in e for e in validate(self.d)))

    def test_real_complete_needs_three_to_five_costed_directions(self):
        self.populated()
        self.d.update(fixture=False, status='complete')
        for section in self.d['sections']:
            section['status'] = 'complete'
        self.assertTrue(any('三至五' in e for e in validate(self.d)))
        dr, depth = self.d['directions'][0], self.d['briefing']['depth']['directions'][0]
        for i in range(2, 5):
            self.d['directions'].append(dict(copy.deepcopy(dr), id='direction-' + str(i)))
            self.d['briefing']['depth']['directions'].append(dict(copy.deepcopy(depth), direction_id='direction-' + str(i)))
        self.assertEqual(validate(self.d), [])
        del self.d['briefing']['depth']['directions'][0]['cost']
        self.assertTrue(any('direction.cost' in e for e in validate(self.d)))

    def test_v5_relaxes_reading_limits_without_changing_v4(self):
        self.populated()
        feature = self.d['competitive_analysis']['features'][0]
        for i in range(2, 21):
            self.d['competitive_analysis']['features'].append(dict(copy.deepcopy(feature), id='feature-' + str(i)))
        ids = [f['id'] for f in self.d['competitive_analysis']['features']]
        self.d['briefing']['feature_ids'] = ids
        self.d['briefing']['depth']['competition']['feature_groups'][0]['feature_ids'] = ids
        self.assertEqual(validate(self.d), [])
        self.d['schema_version'] = V4
        self.assertTrue(any('feature_ids无效或过多' in e for e in validate(self.d)))

    def test_depth_markdown_and_offline_payload_are_consistent_and_safe(self):
        self.populated()
        self.d['briefing']['depth']['market']['social_findings'][0]['title'] = '</script><img src=x onerror=unsafe()> [link](javascript:unsafe())'
        self.d['briefing']['depth']['directions'][0]['description'] = '<script>unsafe()</script>'
        before = copy.deepcopy(self.d)
        self.assertEqual(validate(self.d), [])
        md = markdown(self.d)
        for text in ['Fixture platform pain', 'Fixture need terms', 'Fixture task catalog', 'Fixture reason C1', 'Fixture job chain', 'Fixture product judgment C2', 'Fixture build cost', 'Fixture platform dependency']:
            self.assertIn(text, md)
        self.assertLess(md.index('### 可考虑的产品方向'), md.index('### 投入成本'))
        self.assertNotIn('<script>', md)
        self.assertIn('&lt;script&gt;', md)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = json.dumps(self.d, ensure_ascii=False)
            (root/'research.json').write_text(raw)
            html = render(root).read_text()
            self.assertNotIn('</script><img', html)
            payload = json.loads(re.search(r'<script[^>]*id="report-data"[^>]*>(.*?)</script>', html, re.S).group(1))
            self.assertEqual(payload['briefing']['depth'], self.d['briefing']['depth'])
            self.assertEqual(payload['markdown'], md)
            self.assertEqual((root/'research.md').read_text(), md)
            self.assertEqual((root/'research.json').read_text(), raw)
            with zipfile.ZipFile(root/'research.zip') as z:
                self.assertEqual(z.read('research.md').decode(), md)
                self.assertEqual(set(z.namelist()), {'research.md', 'research.json', 'sources.json'})
        self.assertEqual(self.d, before)

    def test_malformed_depth_containers_return_validation_errors(self):
        self.populated()
        for owner, key, value in [('market', 'social_platforms', [None]), ('market', 'keyword_groups', {}), ('competition', 'selection', None), ('competition', 'product_reviews', [None])]:
            with self.subTest(key=key):
                d = copy.deepcopy(self.d)
                d['briefing']['depth'][owner][key] = value
                self.assertTrue(validate(d))


if __name__=='__main__':unittest.main()
