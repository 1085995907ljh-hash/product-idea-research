"""v3 evidence links and shared presentation blocks. Standard library only."""
from copy import deepcopy
from datetime import date

SCRIPT_INTERFACE = 'internal-module'
SCRIPT_INTERFACE_REASON = 'Imported by report.py for v3 validation and shared HTML/Markdown presentation blocks.'

V3 = 'product-idea-research/v3'
BEHAVIORS = {'problem', 'current_use', 'recommendation', 'switch', 'reject', 'creator', 'promotion'}
NATURAL = BEHAVIORS - {'creator', 'promotion'}
BEHAVIOR_NAMES = dict(problem='表达问题', current_use='正在使用', recommendation='推荐工具', switch='切换工具', reject='拒绝使用', creator='创作者自述', promotion='推广内容')
PLATFORM_NAMES = dict(available='已取得原始材料', partial='部分覆盖', blocked='访问受限', not_run='未开展')
FEATURE_NAMES = dict(yes='支持（有依据）', partial='部分支持', no='明确不支持', unknown='未核实')
NOVELTY = dict(new_task='新出现的任务', new_context='旧需求的新情境', new_solution='旧需求的新解法', mature='成熟需求', unknown='尚不能判断')


def validate_details(d):
    errors = []
    def need(ok, message):
        if not ok:
            errors.append('v3: ' + message)
    def text(v):
        return isinstance(v, str) and bool(v.strip())
    def list_value(v):
        return v if isinstance(v, list) else []
    def natural(p):
        return isinstance(p.get('behavior'), str) and p['behavior'] in NATURAL
    def obj(v, label):
        need(isinstance(v, dict), label + '须对象')
        return v if isinstance(v, dict) else {}
    def rows(v, label):
        need(isinstance(v, list) and all(isinstance(x, dict) for x in v), label + '须对象数组')
        return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []
    def strings(v, label):
        need(isinstance(v, list) and all(text(x) for x in v), label + '须文本数组')
        return [x for x in v if text(x)] if isinstance(v, list) else []
    def fields(r, names, label):
        for key in names.split():
            need(text(r.get(key)), label + '缺文本 ' + key)
    def choice(r, key, options, label):
        need(isinstance(r.get(key), str) and r.get(key) in options, label + '.' + key + '无效')
    def indexed(rs, label):
        ids = [x.get('id') for x in rs]
        valid = [x for x in ids if text(x)]
        need(len(valid) == len(ids) and len(set(valid)) == len(valid), label + ' ID缺失或重复')
        return {x['id']: x for x in rs if text(x.get('id'))}
    sources = {s['id']: s for s in rows(d.get('sources'), 'sources') if text(s.get('id'))}
    verified = {sid for sid, s in sources.items() if s.get('status') == 'verified'}
    def refs(r, required=False, checked=False):
        values = strings(r.get('source_ids'), 'source_ids')
        need(set(values).issubset(sources), '引用不存在的来源')
        if required:
            need(bool(values), '已陈述的事实/核验结果缺来源')
        if checked:
            need(set(values).issubset(verified), '已核实内容引用未核实来源')
    def links(r, key, universe):
        values = strings(r.get(key), key)
        need(len(values) == len(set(values)), key + '重复')
        need(set(values).issubset(universe), key + '引用不存在的对象')
        return values
    def day(v, label):
        if v is None:
            return
        try:
            date.fromisoformat(v)
        except (ValueError, TypeError):
            need(False, label + '须YYYY-MM-DD或null')

    sr = obj(d.get('social_research'), 'social_research')
    fields(sr, 'summary', 'social_research')
    platforms = rows(sr.get('platforms'), 'platforms')
    posts = rows(sr.get('posts'), 'posts')
    pains = rows(sr.get('pains'), 'pains')
    platform_map, post_map, pain_map = indexed(platforms, 'platforms'), indexed(posts, 'posts'), indexed(pains, 'pains')
    comps = rows(d.get('competitors'), 'competitors')
    comp_map = indexed(comps, 'competitors')
    for p in platforms:
        fields(p, 'name query_scope time_range discussion assessment limitation', 'platform')
        choice(p, 'status', {'available', 'partial', 'blocked', 'not_run'}, 'platform')
        refs(p)
    for p in posts:
        fields(p, 'author_key region context', 'post')
        need(p.get('platform_id') in platform_map if text(p.get('platform_id')) else False, 'post平台不存在')
        choice(p, 'state', {'verified', 'unverified'}, 'post')
        choice(p, 'query_origin', {'need', 'brand', 'other'}, 'post')
        choice(p, 'behavior', BEHAVIORS, 'post')
        day(p.get('published_at'), 'post日期')
        links(p, 'brand_mentions', comp_map)
        refs(p, True, p.get('state') == 'verified')
        if p.get('quote') is not None:
            need(text(p['quote']) and p.get('state') == 'verified', '只有已核实原帖可引用原话')
    for p in pains:
        fields(p, 'name audience situation current_workaround problem consequence recurrence counterevidence', 'pain')
        choice(p, 'status', {'recurring', 'signal', 'unknown'}, 'pain')
        ids = links(p, 'post_ids', post_map)
        refs(p)
        authors = {post_map[x]['author_key'] for x in ids if x in post_map and post_map[x].get('state') == 'verified' and natural(post_map[x]) and text(post_map[x].get('author_key'))}
        if p.get('status') == 'recurring':
            need(len(authors) >= 2, 'recurring痛点须至少两位已核实独立用户')
        if p.get('status') == 'signal':
            need(bool(ids), 'signal痛点须关联帖子')

    na = obj(d.get('need_assessment'), 'need_assessment')
    choice(na, 'classification', set(NOVELTY), 'need_assessment')
    fields(na, 'novelty_reason demand_summary existing_solutions satisfaction remaining_gap original_action', 'need_assessment')
    refs(na, na.get('classification') not in (None, 'unknown'))
    ca = obj(d.get('competitive_analysis'), 'competitive_analysis')
    cats = rows(ca.get('categories'), 'categories')
    cat_map = indexed(cats, 'categories')
    for c in cats:
        fields(c, 'name description', 'category')
        links(c, 'competitor_ids', comp_map)
        refs(c)
    for c in comps:
        fields(c, 'positioning audience', 'competitor')
        links(c, 'category_ids', cat_map)
        for key in ('official_keywords', 'user_keywords', 'strengths', 'weaknesses'):
            strings(c.get(key), 'competitor.' + key)
        for cid in c.get('category_ids', []) if isinstance(c.get('category_ids'), list) else []:
            if isinstance(cid, str) and cid in cat_map:
                need(c.get('id') in list_value(cat_map[cid].get('competitor_ids')), '竞品分类须双向一致')
    for c in cats:
        for cid in c.get('competitor_ids', []) if isinstance(c.get('competitor_ids'), list) else []:
            if isinstance(cid, str) and cid in comp_map:
                need(c.get('id') in list_value(comp_map[cid].get('category_ids')), '分类竞品须双向一致')
    selected = links(ca, 'feature_competitor_ids', comp_map)
    features = rows(ca.get('features'), 'features')
    indexed(features, 'features')
    for f in features:
        fields(f, 'name', 'feature')
        cells = rows(f.get('cells'), 'feature.cells')
        cids = [c.get('competitor_id') for c in cells]
        need(len(cids) == len(selected) and all(isinstance(x, str) for x in cids) and set(x for x in cids if isinstance(x, str)) == set(selected), '功能行须恰好覆盖重点对手且不重复')
        for c in cells:
            choice(c, 'state', set(FEATURE_NAMES), 'feature.cell')
            fields(c, 'basis', 'feature.cell')
            refs(c, c.get('state') != 'unknown', c.get('state') != 'unknown')
    reviews = rows(ca.get('reviews'), 'reviews')
    review_map = indexed(reviews, 'reviews')
    for r in reviews:
        need(isinstance(r.get('competitor_id'), str) and r.get('competitor_id') in comp_map, 'review竞品不存在')
        need(type(r.get('rating')) is int and 1 <= r['rating'] <= 5, 'review.rating须1–5整数')
        day(r.get('published_at'), 'review日期')
        need(r.get('version') is None or text(r.get('version')), 'review.version须文本或null')
        fields(r, 'summary', 'review')
        need(r.get('quote') is None or text(r.get('quote')), 'review.quote须文本或null')
        refs(r, True, True)
    coverage = rows(ca.get('review_coverage'), 'review_coverage')
    cov_ids = [r.get('competitor_id') for r in coverage]
    need(len(cov_ids) == len(set(x for x in cov_ids if isinstance(x, str))), 'review_coverage产品重复')
    for r in coverage:
        need(isinstance(r.get('competitor_id'), str) and r['competitor_id'] in comp_map, 'review_coverage竞品不存在')
        fields(r, 'scope time_range limitation', 'review_coverage')
        refs(r)
    themes = rows(ca.get('review_themes'), 'review_themes')
    indexed(themes, 'review_themes')
    for t in themes:
        choice(t, 'sentiment', {'positive', 'negative'}, 'review_theme')
        choice(t, 'current_status', {'unresolved', 'resolved', 'unknown'}, 'review_theme')
        fields(t, 'theme task impact assessment', 'review_theme')
        cids = links(t, 'competitor_ids', comp_map)
        rids = links(t, 'review_ids', review_map)
        need(bool(rids), '评价主题须关联实际评论')
        refs(t, True, True)
        for rid in rids:
            if rid in review_map:
                r = review_map[rid]
                need(r.get('competitor_id') in cids, '评价主题与评论的产品不匹配')
                rating = r.get('rating')
                if type(rating) is int:
                    need(rating >= 4 if t.get('sentiment') == 'positive' else rating <= 3, '好差评主题与星级不匹配')
    ms = obj(ca.get('mindshare'), 'mindshare')
    choice(ms, 'status', {'measured', 'insufficient'}, 'mindshare')
    fields(ms, 'summary limitation', 'mindshare')
    eligible = links(ms, 'eligible_post_ids', post_map)
    if ms.get('status') == 'insufficient':
        need(not eligible, '心智证据不足时不得携带计数样本')
    if ms.get('status') == 'measured':
        need(bool(eligible), '心智计算缺合格样本')
        for pid in eligible:
            if pid in post_map:
                p = post_map[pid]
                need(p.get('state') == 'verified' and p.get('query_origin') == 'need' and natural(p) and text(p.get('author_key')), '品牌提及分母只能含已核实自然需求用户，不能含品牌检索/广告/创作者')
    directions = rows(d.get('directions'), 'directions')
    if not directions:
        need(text(d.get('no_directions_reason')), '无方向须说明no_directions_reason')
    for dr in directions:
        pids = links(dr, 'pain_ids', pain_map)
        cids = links(dr, 'competitor_ids', comp_map)
        fields(dr, 'existing_alternatives remaining_gap', 'direction')
        if dr.get('stance') == 'recommended':
            actual = any(any(post_map[x].get('state') == 'verified' and natural(post_map[x]) for x in list_value(pain_map[pid].get('post_ids')) if isinstance(x, str) and x in post_map) for pid in pids if pid in pain_map)
            need(actual, '推荐方向须关联真实已核实用户痛点')
            need(bool(cids) and any({x for x in list_value(comp_map[cid].get('source_ids')) if isinstance(x, str)} & verified for cid in cids if cid in comp_map), '推荐方向须关联已核实替代/竞品')
    return errors


def mindshare_counts(d):
    ms = d['competitive_analysis']['mindshare']
    if ms['status'] != 'measured':
        return None
    posts = {p['id']: p for p in d['social_research']['posts']}
    eligible = [posts[pid] for pid in ms['eligible_post_ids']]
    denominator = len({p['author_key'] for p in eligible})
    rows = []
    for comp in d['competitors']:
        matching = [p for p in eligible if comp['id'] in p['brand_mentions']]
        if matching:
            rows.append(dict(competitor_id=comp['id'], count=len({p['author_key'] for p in matching}), denominator=denominator, post_ids=[p['id'] for p in matching], source_ids=list(dict.fromkeys(s for p in matching for s in p['source_ids']))))
    return dict(denominator=denominator, rows=rows)


def detail_blocks(d, section_id):
    sr, na, ca = d['social_research'], d['need_assessment'], d['competitive_analysis']
    comps = {c['id']: c for c in d['competitors']}
    def names(ids):
        return '、'.join(comps[i]['name'] for i in ids) or '尚未核实'
    def paragraph(title, text, refs=(), collapsed=False):
        return dict(type='paragraph', title=title, text=text, source_ids=list(refs), collapsed=collapsed)
    def table(title, headers, rows, refs=None, collapsed=False):
        return dict(type='table', title=title, headers=headers, rows=rows, row_source_ids=refs or [[] for _ in rows], source_ids=[], collapsed=collapsed)
    def joined(values):
        return '；'.join(values) or '尚未核实'
    if section_id == 'signals':
        out = [paragraph('跨平台需求结论', sr['summary'])]
        ps = sr['platforms']
        out.append(table('不同平台在讨论什么', ['平台与覆盖', '检索范围与时间', '用户在讨论什么', '判断与限制'], [[p['name'] + ' / ' + PLATFORM_NAMES[p['status']], p['query_scope'] + '；' + p['time_range'], p['discussion'], p['assessment'] + '；' + p['limitation']] for p in ps], [p['source_ids'] for p in ps]))
        for p in sr['pains']:
            label = dict(recurring='多位用户线索', signal='单例/有限线索', unknown='待核实')[p['status']]
            items = [
                '谁在什么情况下需要：' + p['audience'].rstrip('。') + '；' + p['situation'],
                '现在怎么做：' + p['current_workaround'],
                '卡在哪里：' + p['problem'].rstrip('。') + '；' + p['consequence'],
                '证据有多强：' + p['recurrence'],
                '反面情况：' + p['counterevidence'],
            ]
            out.append(dict(type='list', title='痛点：' + p['name'] + '（' + label + '）', items=items, source_ids=p['source_ids']))
        out.append(table('新旧需求与满足程度', ['判断', '结论'], [['需求性质', NOVELTY[na['classification']] + '。' + na['novelty_reason']], ['需求是否成立', na['demand_summary']], ['谁已经做过', na['existing_solutions']], ['目前做得怎样', na['satisfaction']], ['还剩什么缺口', na['remaining_gap']]], [na['source_ids']] * 5))
        rows = [['原始 idea', na['original_action'], na['remaining_gap'], d['decision']['mvp_focus']]]
        refs = [na['source_ids']]
        for dr in d['directions']:
            rows.append([dr['name'], dict(recommended='优先验证', explore='待验证', avoid='不建议')[dr['stance']], dr['remaining_gap'] + '；已有替代：' + dr['existing_alternatives'] + '；理由：' + dr['why'], dr['mvp_focus']])
            refs.append(dr['source_ids'])
        out.append(table('哪些方向值得试，哪些不建议', ['方向', '建议', '剩余缺口与取舍理由', 'MVP主攻点'], rows, refs))
        posts = sr['posts']
        platforms = {p['id']: p['name'] for p in ps}
        out.append(table('代表讨论与取证边界', ['平台 / 日期', '用户表达或行为', '证据与地域'], [[platforms[p['platform_id']] + ' / ' + (p.get('published_at') or '日期未知'), p['context'] + ('；原话：' + p['quote'] if p.get('quote') else ''), ('原文已核实' if p['state'] == 'verified' else '仅有线索，未核实') + ' / ' + p['region'] + ' / ' + BEHAVIOR_NAMES[p['behavior']]] for p in posts], [p['source_ids'] for p in posts], True))
        return out
    if section_id != 'competition':
        return []
    out = [table('按任务划分的竞品', ['任务维度', '已有产品或替代', '解决什么'], [[c['name'], names(c['competitor_ids']), c['description']] for c in ca['categories']], [c['source_ids'] for c in ca['categories']])]
    out.append(table('定位、关键词与优势劣势', ['对手 / 人群', '定位与关键词', '优势', '劣势与边界'], [[c['name'] + ' / ' + c['audience'], c['positioning'] + '；官方词：' + joined(c['official_keywords']) + '；用户词：' + joined(c['user_keywords']), joined(c['strengths']), joined(c['weaknesses'])] for c in d['competitors']], [c['source_ids'] for c in d['competitors']]))
    selected = ca['feature_competitor_ids']
    rows, refs = [], []
    for f in ca['features']:
        cells = {c['competitor_id']: c for c in f['cells']}
        rows.append([f['name']] + [FEATURE_NAMES[cells[cid]['state']] + '：' + cells[cid]['basis'] for cid in selected])
        refs.append(list(dict.fromkeys(s for c in f['cells'] for s in c['source_ids'])))
    out.append(table('关键功能差异', ['功能'] + [comps[cid]['name'] for cid in selected], rows, refs))
    for sentiment, title in [('positive', '好评：用户为什么留下'), ('negative', '差评：用户遇到了什么问题')]:
        themes = [t for t in ca['review_themes'] if t['sentiment'] == sentiment]
        if not themes:
            out.append(paragraph(title, '本轮尚未取得可核验主题，不能据此判断没有好评或差评。'))
        else:
            out.append(table(title, ['主题 / 对手', '对应任务与影响', '当前状态及对我们的含义'], [[t['theme'] + ' / ' + names(t['competitor_ids']), t['task'] + '；' + t['impact'], dict(unresolved='尚未解决', resolved='已解决', unknown='现状待核验')[t['current_status']] + '；' + t['assessment']] for t in themes], [t['source_ids'] for t in themes]))
    ms = ca['mindshare']
    counts = mindshare_counts(d)
    out.append(paragraph('自然讨论中的品牌提及', ms['summary'] + '；' + ms['limitation']))
    if counts:
        out.append(table('本次样本品牌主动提及（不是市场份额）', ['品牌', '独立用户 n/N', '计数口径'], [[comps[r['competitor_id']]['name'], str(r['count']) + '/' + str(r['denominator']), '自然需求讨论；同作者去重；可提多个品牌'] for r in counts['rows']], [r['source_ids'] for r in counts['rows']]))
    coverage_rows, coverage_refs = [], []
    for cov in ca['review_coverage']:
        rs = [r for r in ca['reviews'] if r['competitor_id'] == cov['competitor_id']]
        coverage_rows.append([comps[cov['competitor_id']]['name'], str(len(rs)) + '条 / 好评' + str(sum(r['rating'] >= 4 for r in rs)) + ' / 低星' + str(sum(r['rating'] <= 3 for r in rs)), cov['scope'] + '；' + cov['time_range'], cov['limitation']])
        coverage_refs.append(cov['source_ids'])
    out.append(table('评价样本覆盖', ['对手', '实际取得', '范围和时间', '限制'], coverage_rows, coverage_refs, True))
    rs = ca['reviews']
    out.append(table('评论明细', ['产品 / 日期 / 星级', '具体评价', '版本及原始ID'], [[comps[r['competitor_id']]['name'] + ' / ' + (r.get('published_at') or '日期未知') + ' / ' + str(r['rating']) + '星', r['summary'] + ('；原话：' + r['quote'] if r.get('quote') else ''), (r.get('version') or '版本未知') + ' / ' + r['id']] for r in rs], [r['source_ids'] for r in rs], True))
    return out


def expanded_sections(d):
    sections = deepcopy(d['sections'])
    if d.get('schema_version') == V3:
        for s in sections:
            s['blocks'] = detail_blocks(d, s['id']) + s.get('blocks', [])
    return sections
