#!/usr/bin/env python3
"""Validate one research content source and render offline HTML/Markdown. Stdlib."""
import argparse
import base64
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import io
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile
from research_details import V3, expanded_sections, validate_details
from briefing import V4, CHAPTERS, BLOCKS, initial_briefing, validate_briefing, markdown_briefing
from deep_briefing import V5, initial_depth, validate_depth, markdown_depth

V1 = 'product-idea-research/v1'
V2 = 'product-idea-research/v2'
SECTIONS = [
    ('decomposition', '想法与子方向'), ('demand', '需求证据'), ('jobs', '用户要完成的任务'),
    ('market', '市场规模与走势'), ('environment', '外部环境与平台'), ('competition', '竞品与差评'),
    ('segments', '先服务哪一群人'), ('business', '收费与商业情景'), ('risks', '优劣势与风险'),
    ('decision', '原想法结论与验证'), ('alternatives', '同领域机会'),
    ('discarded', '放弃与待验证方向'), ('limitations', '研究局限'),
]
V2_SECTIONS = [
    ('signals', '需求与近期话题'), ('market', '市场规模与走势'), ('competition', '竞品与差评'),
    ('environment', '外部环境与平台'), ('validation', '先验证什么'), ('limitations', '依据与缺口'),
]
WEIGHTS = {'demand': .25, 'jobs': .15, 'competition': .20, 'market': .10, 'business': .15, 'buildability': .10, 'risk': .05}
SCORE_NAMES = dict(demand='需求依据', jobs='结果机会', competition='竞争缺口', market='市场与趋势', business='付费与商业', buildability='小团队可做性', risk='风险可控程度')
V2_WEIGHTS = dict(attention=.20, competition=.20, gap=.25, timing=.10, validation=.15, solo_cost=.10)
V2_SCORE_NAMES = dict(attention='近期需求与话题热度', competition='入场拥挤程度', gap='可抓住的具体缺口', timing='现在入场的时机', validation='低成本验证难度', solo_cost='独立开发投入')
CERTAINTIES = dict(supported='直接证据', inferred='有限证据推断', unknown='未知')
CONFIDENCE_NAMES = dict(high='高', medium='中', low='低')
STANCES = dict(recommended='优先验证', explore='可探索', avoid='暂不建议')
LABELS = dict(fact='已核实事实', estimate='估算', hypothesis='假设', unverified='未核实', inference='研究推断')
VERDICTS = dict(go='行', conditional='有条件行', no_go='不行')
STATUS = dict(complete='已研究', partial='部分覆盖', not_run='未开展')


def url_ok(value):
    if not isinstance(value, str) or re.search(r'[\s\x00-\x1f\x7f\\]', value):
        return False
    try:
        u = urlsplit(value)
        return u.scheme in ('http', 'https') and bool(u.hostname) and not u.username and not u.password
    except (TypeError, ValueError):
        return False


def is_v2(data):
    return data.get('schema_version') in (V2, V3, V4, V5)


def score(data):
    """Compute presentation data without mutating the research source."""
    if is_v2(data):
        rows = {r['dimension']: r for r in data.get('scorecard', [])}
        if len(data.get('scorecard', [])) != len(V2_WEIGHTS) or set(rows) != set(V2_WEIGHTS):
            raise ValueError('v2评分须恰好包含六个维度')
        unknown = [k for k in V2_WEIGHTS if rows[k].get('value') is None]
        value = sum(Decimal(str(rows[k]['value'] if rows[k].get('value') is not None else 2.5)) * Decimal(str(w)) for k, w in V2_WEIGHTS.items())
        certainty_values = dict(supported=Decimal('1'), inferred=Decimal('.5'), unknown=Decimal('0'))
        confidence_value = sum(certainty_values[rows[k]['certainty']] * Decimal(str(w)) for k, w in V2_WEIGHTS.items())
        confidence = 'high' if confidence_value >= Decimal('.75') else 'medium' if confidence_value >= Decimal('.4') else 'low'
        label = '优先验证' if value >= Decimal('3.6') else '小成本试' if value >= Decimal('3.0') else '先改方向' if value >= Decimal('2.3') else '不建议入场'
        reason = '研究者按经验权重评分，不是成功概率；证据把握描述证据覆盖，不是统计置信度'
        if unknown:
            reason += '；暂定：' + '、'.join(V2_SCORE_NAMES[k] for k in unknown) + '未知，计算时临时按中性2.5占位，不代表已证实的中等表现'
        if data.get('hard_vetoes') or data.get('conclusion', {}).get('verdict') == 'no_go':
            label = '不建议按原方案入场'
            reason += '；原案结论或已核实硬否决覆盖建议标签，未改变分数'
        elif any(k in unknown for k in ('competition', 'gap')):
            label = '证据不足，先补关键证据'
        elif confidence == 'low':
            label = '证据不足，先验证假设'
        return dict(value=float(value.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)), label=label, provisional=bool(unknown), unknown_dimensions=unknown, confidence=confidence, confidence_value=float(confidence_value), reason=reason)
    # v1 retains its historical weights, payment cap and result shape.
    rows = {r['dimension']: r for r in data.get('scorecard', [])}
    if set(rows) != set(WEIGHTS) or any(rows[k].get('value') is None for k in WEIGHTS):
        return {'value': None, 'stars': None, 'reason': '评分依据不完整，暂不计算综合分'}
    value = sum(rows[k]['value'] * w for k, w in WEIGHTS.items())
    stars = 4 if value >= 4.2 else 3 if value >= 3.5 else 2.5 if value >= 3 else 2 if value >= 2.5 else 1
    reason = '研究者按经验权重评分，不是成功概率'
    if not data.get('payment_evidence_ids'):
        stars = min(stars, 2.5)
        reason += '；无有效付费证据，星级上限2.5'
    if data.get('hard_vetoes'):
        reason += '；已核实硬否决优先于综合分'
    return dict(value=round(value, 2), stars=stars, reason=reason)


def computed_directions(data):
    """Adjacent directions do not inherit the original idea's no-go or veto."""
    return [dict(id=d['id'], score=score(dict(schema_version=V2, scorecard=d['scorecard']))) for d in data.get('directions', [])]


def validate(data):
    """Check structure and provenance references, never the truth of claims."""
    errors = []
    def need(ok, msg):
        if not ok:
            errors.append(msg)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def records(owner, key):
        values = owner.get(key, [])
        need(isinstance(values, list), key + '须数组')
        if not isinstance(values, list):
            return []
        need(all(isinstance(v, dict) for v in values), key + '须由对象组成')
        return [v for v in values if isinstance(v, dict)]
    def unique_ids(items, label):
        values = [item.get('id') for item in items]
        valid = all(text(v) for v in values)
        need(valid and len(values) == len(set(v for v in values if isinstance(v, str))), label + ' ID缺失或重复')
    if not isinstance(data, dict):
        return ['research.json须为对象']
    version = data.get('schema_version')
    v2 = is_v2(data)
    v3 = version in (V3, V4, V5)
    need(version in (V1, V2, V3, V4, V5), 'schema_version错误')
    for key in ('sources', 'evidence', 'competitors', 'trends', 'glossary', 'scorecard', 'sections'):
        need(key in data, '缺少内容数组 ' + key)
    for k in ['title', 'date', 'idea', 'scope']:
        need(text(data.get(k)), '缺少文本 ' + k)
    need(isinstance(data.get('fixture'), bool), 'fixture必须明确true/false')
    need(data.get('status') in ('complete', 'partial'), 'status须complete/partial')
    try:
        date.fromisoformat(data.get('date', ''))
    except (ValueError, TypeError):
        errors.append('date须YYYY-MM-DD')
    sources = records(data, 'sources')
    unique_ids(sources, '来源')
    ids = {s['id'] for s in sources if isinstance(s.get('id'), str)}
    verified = {s['id'] for s in sources if s.get('status') == 'verified' and isinstance(s.get('id'), str)}
    for s in sources:
        need(text(s.get('title')) and url_ok(s.get('url')), '来源标题或URL无效：' + str(s.get('id')))
        need(text(s.get('accessed_at')), '来源缺访问时间：' + str(s.get('id')))
        need(s.get('status') in ('verified', 'unverified'), '来源状态错误')
        if s.get('published_at') is not None:
            need(text(s.get('published_at')), '来源发布日期须文本或null')
    def refs(record, required=False, only_verified=False):
        values = record.get('source_ids', [])
        need(isinstance(values, list), 'source_ids须数组')
        if not isinstance(values, list):
            return
        valid = all(text(v) for v in values)
        need(valid, 'source_ids须由非空文本组成')
        if not valid:
            return
        need(set(values).issubset(ids), '引用不存在的来源：' + str(values))
        if required:
            need(bool(values), '该项缺少来源：' + str(record.get('claim', record.get('title', record.get('name', '')))))
        if only_verified:
            need(set(values).issubset(verified), '已核实事实/评分/否决引用了未核实来源')
    c = data.get('conclusion', {})
    need(isinstance(c, dict), 'conclusion须对象')
    if not isinstance(c, dict):
        c = {}
    need(isinstance(c.get('verdict'), str) and c.get('verdict') in VERDICTS and text(c.get('summary')), '结论缺判断或摘要')
    reasons = c.get('reasons', [])
    need(isinstance(reasons, list) and all(text(r) for r in reasons), '结论理由须文本数组')
    if v2 and isinstance(reasons, list):
        need(len(reasons) <= 3, '结论理由最多三条')
    sections = records(data, 'sections')
    unique_ids(sections, '章节')
    sids = [s.get('id') for s in sections]
    if version in (V4, V5):
        need(sids == [s for s, _ in CHAPTERS], 'v4/v5正文须按市场、竞品、产品排列')
    elif v2:
        need(sids == [s for s, _ in V2_SECTIONS], 'v2须恰好六章且按约定顺序排列')
    else:
        need({s for s, _ in SECTIONS}.issubset(s for s in sids if isinstance(s, str)), '缺少方法论章节；未开展也须说明原因')
    for s in sections:
        need(isinstance(s.get('id'), str) and bool(re.fullmatch(r'[a-z][a-z0-9-]*', s.get('id', ''))), '章节ID无效')
        need(text(s.get('title')), '章节缺标题')
        need(isinstance(s.get('status'), str) and s.get('status') in STATUS, '章节状态错误')
        need(text(s.get('summary')), '章节缺摘要或未开展原因')
        if data.get('status') == 'complete':
            need(s.get('status') == 'complete' if v2 else s.get('status') != 'partial', '整体complete不能有未完成章节')
        refs(s)
        for b in records(s, 'blocks'):
            kind = b.get('type')
            need(kind in ('paragraph', 'list', 'table'), '不支持的内容块')
            if 'title' in b:
                need(text(b.get('title')), '内容块标题须非空文本')
            if 'collapsed' in b:
                need(type(b['collapsed']) is bool, 'collapsed须true/false')
            if b.get('collapsed') is True:
                need(text(b.get('title')), '折叠内容块须非空title')
            refs(b)
            if 'row_source_ids' in b:
                need(kind == 'table', 'row_source_ids只用于table')
            if kind == 'paragraph':
                need(text(b.get('text')), '段落缺文本')
            elif kind == 'list':
                items = b.get('items')
                need(isinstance(items, list) and bool(items) and all(text(x) for x in items), '列表须含非空文本')
            elif kind == 'table':
                headers, rows = b.get('headers'), b.get('rows', [])
                need(isinstance(headers, list) and bool(headers) and all(text(h) for h in headers), '表格缺文本表头')
                need(isinstance(rows, list), '表格行须数组')
                if 'row_source_ids' in b:
                    row_refs = b['row_source_ids']
                    need(isinstance(row_refs, list) and isinstance(rows, list) and len(row_refs) == len(rows), 'row_source_ids须与rows等长')
                    if isinstance(row_refs, list):
                        for values in row_refs:
                            refs(dict(source_ids=values))
                if isinstance(headers, list) and isinstance(rows, list):
                    for row in rows:
                        need(isinstance(row, list) and len(row) == len(headers), '表格列数不一致')
                        if isinstance(row, list):
                            need(all(isinstance(x, str) or type(x) in (int, float) for x in row), '表格单元格须文本或数值')
    evidence, competitors = records(data, 'evidence'), records(data, 'competitors')
    unique_ids(evidence, 'evidence')
    unique_ids(competitors, 'competitors')
    for e in evidence:
        need(e.get('type') in ('A', 'B', 'C', 'D', 'E'), '证据类别须A–E')
        need(isinstance(e.get('state'), str) and e.get('state') in LABELS and text(e.get('claim')), '证据缺状态或内容')
        refs(e, e.get('state') in ('fact', 'estimate'), e.get('state') == 'fact')
        if e.get('quote'):
            need(text(e['quote']) and e.get('state') == 'fact' and bool(e.get('source_ids')), '引文须已核实原文')
        if e.get('limitation') is not None:
            need(isinstance(e['limitation'], str), '证据边界须文本')
    def scorecard(owner):
        rows = records(owner, 'scorecard')
        weights = V2_WEIGHTS if v2 else WEIGHTS
        dimensions = [r.get('dimension') for r in rows]
        need(len(dimensions) == len(set(d for d in dimensions if isinstance(d, str))), '评分维度重复或无效')
        if v2:
            need(len(rows) == len(weights) and set(d for d in dimensions if isinstance(d, str)) == set(weights), 'v2评分须恰好包含六个维度')
        for r in rows:
            need(isinstance(r.get('dimension'), str) and r.get('dimension') in weights, '未知评分维度')
            value = r.get('value')
            need('value' in r, '评分缺value；未知须明确null')
            need(value is None or (type(value) in (int, float) and 1 <= value <= 5), '评分须1–5或null')
            need(text(r.get('reason')), '评分缺依据说明')
            refs(r, required=value is not None, only_verified=v2 and value is not None)
            if v2:
                certainty = r.get('certainty')
                need(isinstance(certainty, str) and certainty in CERTAINTIES, '评分certainty须supported/inferred/unknown')
                need(certainty == 'unknown' if value is None else certainty in ('supported', 'inferred'), '未知评分须null且certainty为unknown；数值评分须说明证据把握')
    scorecard(data)
    payment = data.get('payment_evidence_ids', [])
    need(isinstance(payment, list) and all(isinstance(x, str) for x in payment), 'payment_evidence_ids须文本数组')
    if isinstance(payment, list) and all(isinstance(x, str) for x in payment):
        need(set(payment).issubset(verified), '付费证据必须是已核实来源')
    for veto in records(data, 'hard_vetoes'):
        refs(veto, True, True)
        need(text(veto.get('reason')), '硬否决缺原因')
        need(c.get('verdict') == 'no_go', '硬否决时原案必须不行')
    for comp in competitors:
        need(comp.get('kind') in ('direct', 'indirect', 'manual'), '竞品类型错误')
        need(text(comp.get('name')), '竞品缺名称')
        for key in ('summary', 'pricing', 'limitation'):
            if key in comp:
                need(isinstance(comp[key], str), '竞品' + key + '须文本')
        refs(comp)
    if v2:
        decision = data.get('decision', {})
        need(isinstance(decision, dict), 'decision须对象')
        if isinstance(decision, dict):
            for key in ('recommendation', 'mvp_focus', 'main_risk', 'next_step'):
                need(text(decision.get(key)), 'decision缺少 ' + key)
            refs(decision)
        directions = records(data, 'directions')
        if version == V5:
            need(0 <= len(directions) <= 5, 'v5 directions须零至五条；真实完成报告须三至五条')
            if data.get('status') == 'complete' and not data.get('fixture'):
                need(3 <= len(directions) <= 5, 'v5真实完成报告directions须三至五条')
        else:
            need(0 <= len(directions) <= 3 if v3 else 1 <= len(directions) <= 3, 'v3 directions须零至三条' if v3 else 'directions须一至三条')
        unique_ids(directions, '方向')
        need(sum(d.get('stance') == 'recommended' for d in directions) <= 1, '最多一个recommended方向')
        for direction in directions:
            need(isinstance(direction.get('id'), str) and bool(re.fullmatch(r'[a-z][a-z0-9-]*', direction.get('id', ''))), '方向ID无效')
            need(isinstance(direction.get('stance'), str) and direction.get('stance') in STANCES, '方向stance错误')
            for key in ('name', 'target_user', 'change', 'mvp_focus', 'why', 'first_test', 'main_risk'):
                need(text(direction.get(key)), '方向缺少 ' + key)
            refs(direction)
            if direction.get('stance') == 'recommended':
                values = direction.get('source_ids', [])
                need(isinstance(values, list) and any(isinstance(x, str) and x in verified for x in values), 'recommended方向须至少一条已核实来源')
            scorecard(direction)
    elif c.get('verdict') == 'no_go':
        alt = next((s for s in sections if s.get('id') == 'alternatives'), {})
        need(alt.get('status') != 'not_run', '原案不行须开展同领域候选研究，缺证据可标partial')
    for t in records(data, 'trends'):
        refs(t, True, True)
        need(all(text(t.get(k)) for k in ('keyword', 'group', 'window', 'geo', 'reason')), '趋势元信息不完整')
        for key in ('topic', 'category', 'search_type', 'granularity'):
            if key in t:
                need(isinstance(t[key], str), '趋势' + key + '须文本')
        dates = []
        for p in records(t, 'points'):
            dates.append(p.get('date'))
            try:
                date.fromisoformat(p.get('date', ''))
            except (ValueError, TypeError):
                errors.append('趋势日期须YYYY-MM-DD')
            value = p.get('value')
            need(value is None or (type(value) in (int, float) and 0 <= value <= 100), '趋势值超出0–100')
            need(type(p.get('partial')) is bool, '趋势点须标partial')
        need(len(dates) == len(set(x for x in dates if isinstance(x, str))), '趋势日期重复或无效')
        need(all(isinstance(x, str) for x in dates) and dates == sorted(x for x in dates if isinstance(x, str)), '趋势日期须升序')
    for item in records(data, 'glossary'):
        need(text(item.get('term')) and text(item.get('meaning')), '术语缺名称或解释')
    if v3:
        errors.extend(validate_details(data))
    if version == V4:
        errors.extend(validate_briefing(data))
    elif version == V5:
        errors.extend(validate_briefing(data, limits=(12, 20, 80), prefix='v5'))
        errors.extend(validate_depth(data))
    return errors


def md_text(value):
    """Treat research strings as text, including in Markdown-capable viewers."""
    value = escape(str(value), quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+!|>])', r'\\\1', value)


def cell(value):
    return md_text(value).replace('\n', ' ')


def markdown(d, sections=None):
    if d.get('schema_version') == V5:
        return markdown_depth(d, score(d), md_text, computed_directions(d))
    if d.get('schema_version') == V4:
        return markdown_briefing(d, score(d), md_text)
    v2 = is_v2(d)
    sections = expanded_sections(d) if sections is None else sections
    out = ['# ' + md_text(d['title']), '', md_text(d['date'] + '｜' + d['scope']), '']
    source_by_id = {s['id']: s for s in d['sources']}
    def references(ids):
        # Encode delimiters so a verified http(s) URL cannot escape Markdown links.
        return ' '.join('[' + md_text(i) + '](' + source_by_id[i]['url'].replace('<', '%3C').replace('>', '%3E').replace('(', '%28').replace(')', '%29').replace('|', '%7C') + ')' for i in ids)
    def add_refs(record):
        if record.get('source_ids'):
            out.extend([references(record['source_ids']), ''])
    def summary(sc):
        if not v2:
            return '综合分：' + (str(sc['value']) + '/5，' + str(sc['stars']) + '星' if sc['value'] is not None else '暂不评分') + '。' + sc['reason']
        return f"综合分：{sc['value']:.1f}/5{'（暂定）' if sc['provisional'] else ''}，{sc['label']}。证据把握：{CONFIDENCE_NAMES[sc['confidence']]}。{sc['reason']}"
    def competitors():
        out.extend(['### 竞品与替代清单' if v2 else '## 竞品与替代清单', ''])
        for comp in d.get('competitors', []):
            kind = dict(direct='直接竞品', indirect='间接替代', manual='人工办法')[comp['kind']]
            out.append('- ' + md_text(comp['name'] + '（' + kind + '）：' + comp.get('summary', '') + ' 收费：' + comp.get('pricing', '未核实') + ' 研究边界：' + comp.get('limitation', '未说明')) + ' ' + references(comp.get('source_ids', [])))
        if not d.get('competitors'):
            out.append('本轮尚未取得可核验的竞品清单。')
        out.append('')
    def trends():
        out.extend(['### 搜索兴趣走势' if v2 else '## 趋势数据与限制', ''])
        if not d.get('trends'):
            out.extend(['尚未取得原始时间序列，因此不显示趋势线。缺数据不等于没有需求。', ''])
        for t in d.get('trends', []):
            out.extend([('#### ' if v2 else '### ') + md_text(t['keyword'] + ' / ' + t['window']), ''])
            metadata = [t['geo'], t['group']]
            metadata += [label + '：' + t[key] for key, label in [('topic', 'Topic'), ('category', '类别'), ('search_type', '搜索类型'), ('granularity', '粒度')] if t.get(key)]
            out.extend([md_text('；'.join(metadata) + '。' + t['reason']) + ' ' + references(t['source_ids']), '', '| 日期 | 相对指数 | 未完成周期 |', '| --- | --- | --- |'])
            out.extend(f"| {p['date']} | {p['value'] if p['value'] is not None else '缺失/低量'} | {'是' if p['partial'] else '否'} |" for p in t.get('points', []))
            out.append('')
    def score_table(rows):
        names, weights = (V2_SCORE_NAMES, V2_WEIGHTS) if v2 else (SCORE_NAMES, WEIGHTS)
        out.extend(['| 维度 | 权重 | 分数 | 证据把握 | 依据 |', '| --- | --- | --- | --- | --- |'] if v2 else ['| 维度 | 权重 | 分数 | 依据 |', '| --- | --- | --- | --- |'])
        for r in sorted(rows, key=lambda r: list(weights).index(r['dimension'])):
            value = r['value'] if r['value'] is not None else ('未知（暂以2.5占位）' if v2 else '未知')
            certainty = ' ' + CERTAINTIES[r['certainty']] + ' |' if v2 else ''
            out.append(f"| {names[r['dimension']]} | {weights[r['dimension']]*100:g}% | {value} |" + certainty + f" {cell(r['reason'])} {references(r.get('source_ids', []))} |")
        out.append('')
    def fold_start(title):
        out.extend(['<details>', '<summary>' + title + '</summary>', ''] if v2 else ['## ' + title, ''])
    def fold_end():
        if v2:
            out.extend(['</details>', ''])
    if d['fixture']:
        out.extend(['> 阅读样例，非真实市场调研。所有示例判断均不构成产品建议。', ''])
    out.extend(['## 研究概览' if v2 else '## 结论先行', '', VERDICTS[d['conclusion']['verdict']] + '：' + md_text(d['conclusion']['summary']), ''])
    out.extend('- ' + md_text(x) for x in d['conclusion'].get('reasons', []))
    out.extend(['', summary(score(d)), ''])
    if v2:
        for veto in d.get('hard_vetoes', []):
            out.extend(['- 已核实不入场依据：' + md_text(veto['reason']) + ' ' + references(veto['source_ids']), ''])
        decision = d['decision']
        out.extend(['## 方向建议与 MVP', '', md_text(decision['recommendation']), '', '**MVP 主攻点：**' + md_text(decision['mvp_focus']), '', '**主要风险：**' + md_text(decision['main_risk']), '', '**下一步：**' + md_text(decision['next_step']), ''])
        add_refs(decision)
        if not d['directions'] and d.get('no_directions_reason'):
            out.extend([md_text(d['no_directions_reason']), ''])
        direction_scores = {item['id']: item['score'] for item in computed_directions(d)}
        for direction in d['directions']:
            out.extend(['### ' + md_text(direction['name']) + '（' + STANCES[direction['stance']] + '）', '', summary(direction_scores[direction['id']]), ''])
            for key, label in [('target_user', '优先用户'), ('change', '相对原案的变化'), ('mvp_focus', 'MVP 主攻点'), ('why', '判断理由与评分变化'), ('first_test', '先做的验证'), ('main_risk', '主要风险')]:
                out.extend(['**' + label + '：**' + md_text(direction[key]), ''])
            add_refs(direction)
    for section in sections:
        out.extend(['## ' + md_text(section['title']), '', STATUS[section['status']] + '：' + md_text(section['summary']), ''])
        add_refs(section)
        for b in section.get('blocks', []):
            if b.get('collapsed'):
                out.extend(['<details>', '<summary>' + escape(b['title']) + '</summary>', ''])
            elif b.get('title'):
                out.extend(['### ' + md_text(b['title']), ''])
            if b['type'] == 'paragraph':
                out.extend([md_text(b['text']), ''])
            elif b['type'] == 'list':
                out.extend('- ' + md_text(x) for x in b['items'])
                out.append('')
            else:
                out.extend(['| ' + ' | '.join(cell(x) for x in b['headers']) + ' |', '| ' + ' | '.join('---' for _ in b['headers']) + ' |'])
                for index, row in enumerate(b.get('rows', [])):
                    cells = [cell(x) for x in row]
                    row_refs = b.get('row_source_ids', [])
                    if row_refs and row_refs[index]:
                        cells[-1] += ' ' + references(row_refs[index])
                    out.append('| ' + ' | '.join(cells) + ' |')
                out.append('')
            add_refs(b)
            if b.get('collapsed'):
                out.extend(['</details>', ''])
        if v2 and section['id'] == 'market':
            trends()
        if v2 and section['id'] == 'competition':
            competitors()
    fold_start('证据清单')
    for e in d.get('evidence', []):
        out.append(f"- {md_text(e['id'])}｜{e['type']}｜{LABELS[e['state']]}：{md_text(e['claim'])} " + references(e.get('source_ids', [])))
        if e.get('quote'):
            out.extend(['', '> ' + md_text(e['quote']).replace('\n', '\n> '), ''])
        if e.get('limitation'):
            out.extend(['  研究边界：' + md_text(e['limitation']), ''])
    out.append('')
    fold_end()
    if not v2:
        competitors()
    fold_start('评分依据')
    score_table(d.get('scorecard', []))
    if v2:
        for direction in d['directions']:
            out.extend(['### ' + md_text(direction['name']) + '的评分依据', ''])
            score_table(direction['scorecard'])
    fold_end()
    if not v2:
        trends()
    fold_start('本报告术语')
    out.extend('- ' + md_text(g['term'] + '：' + g['meaning']) for g in d.get('glossary', []))
    out.append('')
    fold_end()
    fold_start('来源列表')
    for s in d['sources']:
        out.append('- ' + md_text(s['id'] + ' ' + s['title']) + ' ' + references([s['id']]) + md_text('，' + ('已查阅' if s['status'] == 'verified' else '未核实') + '；访问时间 ' + s['accessed_at'] + ('；发布时间 ' + s['published_at'] if s.get('published_at') else '')))
    out.append('')
    fold_end()
    return '\n'.join(out).strip() + '\n'


def render(root):
    root = Path(root)
    raw_json = (root / 'research.json').read_bytes()
    d = json.loads(raw_json)
    errors = validate(d)
    if errors:
        raise ValueError('\n'.join(errors))
    sections = d['sections'] if d['schema_version'] in (V4, V5) else expanded_sections(d)
    md = markdown(d, sections=sections)
    (root / 'research.md').write_text(md, encoding='utf-8')
    # Explicit allowlist: local diagnostics, credentials, raw private files never auto-published.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('research.md', md)
        z.writestr('research.json', raw_json)
        z.writestr('sources.json', json.dumps(d['sources'], ensure_ascii=False, indent=2))
    (root / 'research.zip').write_bytes(buf.getvalue())
    payload = dict(d, sections=sections, computed_score=score(d), markdown=md, zip_base64=base64.b64encode(buf.getvalue()).decode())
    if is_v2(d):
        payload['computed_directions'] = computed_directions(d)
    assets = Path(__file__).resolve().parents[1] / 'assets'
    stem = 'brief' if d['schema_version'] in (V4, V5) else 'report'
    values = dict(TITLE=escape(d['title']), DATA=json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026'), CSS=(assets/(stem+'.css')).read_text(encoding='utf-8'), JS=(assets/(stem+'.js')).read_text(encoding='utf-8'))
    page = re.sub(r'@@(TITLE|DATA|CSS|JS)@@', lambda m: values[m[1]], (assets/(stem+'.html')).read_text(encoding='utf-8'))
    (root / 'report.html').write_text(page, encoding='utf-8')
    return root / 'report.html'


def initial(title, idea, schema_version=V5):
    if schema_version in ('v1', 'v2', 'v3', 'v4', 'v5'):
        schema_version = 'product-idea-research/' + schema_version
    if schema_version not in (V1, V2, V3, V4, V5):
        raise ValueError('schema_version错误')
    v2 = schema_version in (V2, V3, V4, V5)
    weights = V2_WEIGHTS if v2 else WEIGHTS
    def blank_scores():
        return [dict(dimension=k, value=None, reason='未研究', source_ids=[], **({'certainty': 'unknown'} if v2 else {})) for k in weights]
    data = dict(schema_version=schema_version, title=title, idea=idea, date=date.today().isoformat(), scope='美国 / iOS / 消费者 / 独立开发者' if v2 else '美国 / iOS / 消费者 / 小团队', fixture=False, status='partial', conclusion=dict(verdict='conditional', summary='尚未开始研究，不能据此判断想法成立。', reasons=[]), sources=[], evidence=[], competitors=[], trends=[], glossary=[], payment_evidence_ids=[], hard_vetoes=[], scorecard=blank_scores(), sections=[dict(id=k, title=t, status='not_run', summary='尚未开展研究。', blocks=[]) for k, t in (V2_SECTIONS if v2 else SECTIONS)])
    if v2:
        data['decision'] = dict(recommendation='尚未开展研究，先收集证据再作入场判断。', mvp_focus='尚未确定，等待需求与缺口研究。', main_risk='核心假设和证据覆盖尚未核实。', next_step='先查找目标用户的近期需求表达与反证。', source_ids=[])
        data['directions'] = [dict(id='pending-research', name='待研究的相邻方向', stance='explore', target_user='尚未核实。', change='尚未研究相邻切口。', mvp_focus='等待需求证据后界定。', why='当前没有依据比较方向，评分均为未知。', first_test='先收集真实用户表达，判断是否值得提出方向假设。', main_risk='尚无已核实的方向依据。', source_ids=[], scorecard=blank_scores())]
    if schema_version in (V3, V4, V5):
        data['directions'] = []
        data['no_directions_reason'] = '尚未研究真实痛点与现有替代，当前没有依据提出相邻方向。'
        data['social_research'] = dict(summary='尚未开展跨平台研究；未知不代表没有需求。', platforms=[], posts=[], pains=[])
        data['need_assessment'] = dict(classification='unknown', novelty_reason='尚未核实任务、情境与解法的区别。', demand_summary='尚未取得真实用户表达，不能判断需求是否成立。', existing_solutions='现有产品与人工替代尚未核实。', satisfaction='现有办法的满足程度尚未核实。', remaining_gap='尚未核实具体缺口。', original_action='先补充需求与竞争证据，再判断原案是否值得验证。', source_ids=[])
        data['competitive_analysis'] = dict(categories=[], feature_competitor_ids=[], features=[], reviews=[], review_coverage=[], review_themes=[], mindshare=dict(status='insufficient', summary='尚未取得可去重的自然需求讨论样本，不计算品牌提及比例。', eligible_post_ids=[], limitation='尚未核实检索来源、作者与品牌提及；缺数据不代表没有品牌认知。'))
    if schema_version in (V4, V5):
        data['briefing'] = initial_briefing()
        data['sections'] = [dict(id=k, title=t, status='not_run', summary='尚未开展研究。', blocks=[dict(id=bid, title=title, type='paragraph', text='尚未研究，不作判断。', source_ids=[]) for bid, title in BLOCKS[k]], source_ids=[]) for k, t in CHAPTERS]
        if schema_version == V5:
            data['briefing']['depth'] = initial_depth()
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'validate', 'render'])
    parser.add_argument('root', type=Path)
    parser.add_argument('--title')
    parser.add_argument('--idea')
    parser.add_argument('--schema-version', choices=['v1', 'v2', 'v3', 'v4', 'v5', V1, V2, V3, V4, V5], default='v5', help='init内容格式，默认v5四部分深度报告；v1–v4用于历史格式')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == 'init':
        if root.exists() and (not root.is_dir() or any(root.iterdir())):
            parser.error('目录非空，不覆盖已有研究')
        if not args.title or not args.idea:
            parser.error('init需要--title与--idea')
        root.mkdir(parents=True, exist_ok=True)
        (root/'research.json').write_text(json.dumps(initial(args.title, args.idea, args.schema_version), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(root/'research.json')
    elif args.action == 'validate':
        errors = validate(json.loads((root/'research.json').read_text(encoding='utf-8')))
        if errors:
            raise SystemExit('\n'.join(errors))
        print('OK: report contract (structure only; facts not verified)')
    else:
        print(render(root))


if __name__ == '__main__':
    main()
