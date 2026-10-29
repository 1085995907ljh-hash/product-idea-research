"""V5 reading layer over the source-faithful V3 evidence records."""
import re
from briefing import markdown_briefing

SCRIPT_INTERFACE = 'internal-module'
SCRIPT_INTERFACE_REASON = 'Imported by report.py for V5 depth validation and Markdown.'
V5 = 'product-idea-research/v5'
STATES = {'available', 'verified', 'partial', 'blocked', 'unavailable', 'not_run', 'unknown'}
STATE_NAMES = dict(available='已取得材料', verified='已核实', partial='部分覆盖', blocked='访问受限', unavailable='未取得', not_run='未开展', unknown='未知')
ROLE_NAMES = dict(leader='头部', similar='最相似', new='新进入者', adjacent='相邻替代')


def initial_depth():
    return dict(market=dict(social_platforms=[], social_findings=[], keyword_groups=[]), competition=dict(catalog_groups=[], selection=[], feature_groups=[], product_reviews=[]), directions=[])


def validate_depth(d):
    errors = []
    def need(ok, message):
        if not ok:
            errors.append('v5 depth: ' + message)
    def text(v):
        return isinstance(v, str) and bool(v.strip())
    def obj(v, label):
        need(isinstance(v, dict), label + '须对象')
        return v if isinstance(v, dict) else {}
    def rows(v, label):
        need(isinstance(v, list) and all(isinstance(r, dict) for r in v), label + '须对象数组')
        return [r for r in v if isinstance(r, dict)] if isinstance(v, list) else []
    def strings(v, label):
        need(isinstance(v, list) and all(text(x) for x in v), label + '须文本数组')
        return [x for x in v if text(x)] if isinstance(v, list) else []
    def fields(r, keys, label):
        for key in keys.split():
            need(text(r.get(key)), label + '缺文本 ' + key)
    def indexed(rs, key, label):
        values = [r.get(key) for r in rs]
        valid = [x for x in values if text(x)]
        need(len(valid) == len(values) and len(valid) == len(set(valid)), label + ' ID缺失或重复')
        return {r[key]: r for r in rs if text(r.get(key))}
    def links(r, key, universe, label):
        values = strings(r.get(key), label + '.' + key)
        need(len(values) == len(set(values)), label + '.' + key + '重复')
        need(set(values).issubset(universe), label + '.' + key + '引用不存在的对象')
        return values
    def choice(r, key, options, label):
        need(isinstance(r.get(key), str) and r.get(key) in options, label + '.' + key + '无效')
    sources = {s.get('id'): s for s in rows(d.get('sources'), 'sources') if text(s.get('id'))}
    def refs(r, required=False):
        ids = links(r, 'source_ids', sources, '来源')
        if required:
            need(bool(ids), '必要事实或判断缺少来源')
    sr = obj(d.get('social_research'), 'social_research')
    ca = obj(d.get('competitive_analysis'), 'competitive_analysis')
    comps = {r.get('id'): r for r in rows(d.get('competitors'), 'competitors') if text(r.get('id'))}
    platforms = {r.get('id'): r for r in rows(sr.get('platforms'), 'platforms') if text(r.get('id'))}
    posts = {r.get('id'): r for r in rows(sr.get('posts'), 'posts') if text(r.get('id'))}
    features = {r.get('id'): r for r in rows(ca.get('features'), 'features') if text(r.get('id'))}
    reviews = {r.get('id'): r for r in rows(ca.get('reviews'), 'reviews') if text(r.get('id'))}
    directions = {r.get('id'): r for r in rows(d.get('directions'), 'directions') if text(r.get('id'))}
    b = obj(d.get('briefing'), 'briefing')
    depth = obj(b.get('depth'), 'depth')
    market = obj(depth.get('market'), 'depth.market')
    competition = obj(depth.get('competition'), 'depth.competition')
    complete = d.get('status') == 'complete' and not d.get('fixture')
    social = rows(market.get('social_platforms'), 'social_platforms')
    social_map = indexed(social, 'id', 'social_platforms')
    for r in social:
        fields(r, 'label summary pain opportunity', 'social_platform')
        choice(r, 'state', STATES, 'social_platform')
        need(r.get('id') in platforms if text(r.get('id')) else False, 'social_platform引用不存在的平台')
        ids = links(r, 'post_ids', posts, 'social_platform')
        for pid in ids:
            if pid in posts:
                need(posts[pid].get('platform_id') == r.get('id'), 'social_platform原帖与平台不匹配')
        refs(r, bool(ids) or r.get('state') in ('available', 'verified'))
    for r in rows(market.get('social_findings'), 'social_findings'):
        fields(r, 'title need newness opportunity avoid', 'social_finding')
        refs(r, True)
    keywords = rows(market.get('keyword_groups'), 'keyword_groups')
    keyword_map = indexed(keywords, 'id', 'keyword_groups')
    for r in keywords:
        fields(r, 'title intent summary', 'keyword_group')
        need(bool(strings(r.get('keywords'), 'keyword_group.keywords')), '关键词组不能没有关键词')
        refs(r, True)
    for t in rows(d.get('trends'), 'trends'):
        group = keyword_map.get(t.get('group')) if text(t.get('group')) else None
        need(group is not None, '趋势group须对应keyword_groups.id')
        if group:
            need(isinstance(group.get('keywords'), list) and t.get('keyword') in group['keywords'], '趋势keyword须在对应关键词组内')
    catalog = rows(competition.get('catalog_groups'), 'catalog_groups')
    indexed(catalog, 'id', 'catalog_groups')
    catalog_ids = set()
    for r in catalog:
        fields(r, 'title description', 'catalog_group')
        ids = links(r, 'competitor_ids', comps, 'catalog_group')
        catalog_ids.update(ids)
        refs(r, bool(ids))
    # The catalog is exhaustive for this run; a product may serve several jobs.
    need(catalog_ids == set(comps), '分类目录须覆盖本轮全部竞品')
    selected = b.get('selected_competitor_ids') if isinstance(b.get('selected_competitor_ids'), list) else []
    selected = [x for x in selected if text(x)]
    selection = rows(competition.get('selection'), 'selection')
    selection_map = indexed(selection, 'competitor_id', 'selection')
    need(set(selection_map) == set(selected), 'selection须逐一覆盖重点竞品')
    for r in selection:
        need(r.get('competitor_id') in comps if text(r.get('competitor_id')) else False, 'selection竞品不存在')
        roles = strings(r.get('roles'), 'selection.roles')
        need(bool(roles) and len(roles) == len(set(roles)) and set(roles).issubset(ROLE_NAMES), 'selection角色无效')
        fields(r, 'reason', 'selection')
        refs(r, True)
    groups = rows(competition.get('feature_groups'), 'feature_groups')
    indexed(groups, 'id', 'feature_groups')
    grouped_features = set()
    for r in groups:
        fields(r, 'title job takeaway', 'feature_group')
        grouped_features.update(links(r, 'feature_ids', features, 'feature_group'))
        refs(r, True)
    chosen_features = b.get('feature_ids') if isinstance(b.get('feature_ids'), list) else []
    need(grouped_features == set(x for x in chosen_features if text(x)), 'feature_groups须覆盖且只展示briefing.feature_ids')
    product_reviews = rows(competition.get('product_reviews'), 'product_reviews')
    review_map = indexed(product_reviews, 'competitor_id', 'product_reviews')
    need(set(review_map) == set(selected), 'product_reviews须逐一覆盖重点竞品，缺失评价须保留状态')
    chosen_reviews = b.get('review_ids') if isinstance(b.get('review_ids'), list) else []
    chosen_reviews = {x for x in chosen_reviews if text(x)}
    used_reviews = set()
    for r in product_reviews:
        fields(r, 'summary judgment', 'product_review')
        choice(r, 'state', STATES, 'product_review')
        strings(r.get('positive'), 'product_review.positive')
        strings(r.get('negative'), 'product_review.negative')
        ids = links(r, 'review_ids', reviews, 'product_review')
        used_reviews.update(ids)
        for rid in ids:
            if rid in reviews:
                need(reviews[rid].get('competitor_id') == r.get('competitor_id'), 'product_review评论与产品不匹配')
        if r.get('positive'):
            need(any(type(reviews[rid].get('rating')) is int and reviews[rid]['rating'] >= 4 for rid in ids if rid in reviews), '产品好评结论须关联本产品高星评论')
        if r.get('negative'):
            need(any(type(reviews[rid].get('rating')) is int and reviews[rid]['rating'] <= 3 for rid in ids if rid in reviews), '产品差评结论须关联本产品低星评论')
        refs(r, bool(ids) or r.get('state') in ('available', 'verified'))
        if r.get('state') in ('available', 'verified'):
            need(bool(ids), '已取得口碑须关联实际评论')
        if r.get('state') in ('blocked', 'unavailable', 'not_run', 'unknown'):
            need(not ids and not r.get('positive') and not r.get('negative'), '缺失口碑不能携带评论或正负结论')
    need(used_reviews == chosen_reviews, 'product_reviews须覆盖且只展示briefing.review_ids')
    drs = rows(depth.get('directions'), 'depth.directions')
    dr_map = indexed(drs, 'direction_id', 'depth.directions')
    need(set(dr_map) == set(directions), 'depth.directions须逐一覆盖详细directions')
    if complete:
        need(3 <= len(drs) <= 5, '真实完成报告须三至五个方向')
        need(set(social_map) == set(platforms), '真实完成报告须逐平台展示覆盖状态')
    for r in drs:
        fields(r, 'description pain better_because', 'depth.direction')
        cost = obj(r.get('cost'), 'direction.cost')
        choice(cost, 'level', {'low', 'medium', 'high', 'unknown'}, 'direction.cost')
        fields(cost, 'build ongoing', 'direction.cost')
        feasibility = obj(r.get('feasibility'), 'direction.feasibility')
        choice(feasibility, 'verdict', {'feasible', 'conditional', 'not_feasible', 'unknown'}, 'direction.feasibility')
        fields(feasibility, 'summary', 'direction.feasibility')
        strings(feasibility.get('dependencies'), 'direction.feasibility.dependencies')
        refs(r, True)
    return errors


def markdown_depth(d, computed_score, md_text, direction_scores):
    """Keep the four V4 chapters, replace compressed comparisons with V5 depth."""
    base = markdown_briefing(d, computed_score, md_text)
    b, depth = d['briefing'], d['briefing']['depth']
    comps = {c['id']: c for c in d['competitors']}
    source_map = {s['id']: s for s in d['sources']}
    ca = d['competitive_analysis']
    def name(cid):
        return comps[cid].get('short_name', comps[cid]['name'])
    def refs(r):
        def url(s):
            return re.sub(r'[<>()|]', lambda m: {'<': '%3C', '>': '%3E', '(': '%28', ')': '%29', '|': '%7C'}[m[0]], s)
        ids = list(dict.fromkeys(r.get('source_ids', [])))
        return [' '.join('[' + md_text(i) + '](' + url(source_map[i]['url']) + ')' for i in ids), ''] if ids else []
    def paragraph(label, value):
        return ['**' + label + '：**' + md_text(value), '']
    def table(headers, rows):
        return ['| ' + ' | '.join(md_text(str(x)).replace('\n', ' ') for x in headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |', *['| ' + ' | '.join(md_text(str(x)).replace('\n', ' ') for x in r) + ' |' for r in rows], '']
    market = ['### 跨平台讨论与痛点', '']
    post_map = {p['id']: p for p in d['social_research']['posts']}
    for r in depth['market']['social_platforms']:
        market += ['#### ' + md_text(r['label'] + ' · ' + STATE_NAMES[r['state']]), '', md_text(r['summary']), '']
        market += paragraph('痛点', r['pain']) + paragraph('机会判断', r['opportunity'])
        market += ['<details>', '<summary>查阅平台证据与覆盖限制</summary>', '']
        original = next(p for p in d['social_research']['platforms'] if p['id'] == r['id'])
        market += [md_text(original['query_scope'] + '；' + original['time_range'] + '；' + original['limitation']), '']
        for pid in r['post_ids']:
            p = post_map[pid]
            market += ['- ' + md_text((p.get('published_at') or '日期未知') + '｜' + p['region'] + '｜' + p['context'] + ('；原话：' + p['quote'] if p.get('quote') else '')), ''] + refs(p)
        market += refs(r) + ['</details>', '']
    for r in depth['market']['social_findings']:
        market += ['#### ' + md_text(r['title']), '']
        for key, label in [('need', '需求判断'), ('newness', '新旧性质'), ('opportunity', '可做的机会'), ('avoid', '不宜进入的部分')]:
            market += paragraph(label, r[key])
        market += refs(r)
    market += ['### 多组关键词与搜索意图', '']
    for r in depth['market']['keyword_groups']:
        market += ['#### ' + md_text(r['title']), '', md_text(r['intent']), '', md_text('关键词：' + '、'.join(r['keywords'])), '', md_text(r['summary']), ''] + refs(r)
    base = base.replace('### 搜索兴趣走势\n', '\n'.join(market) + '\n### 搜索兴趣走势\n', 1)
    catalog = ['### 分类竞品全量目录', '']
    for r in depth['competition']['catalog_groups']:
        catalog += ['#### ' + md_text(r['title']), '', md_text(r['description']), '']
        catalog += ['<details>', '<summary>查看本类全部产品</summary>', '']
        catalog += table(['产品 / 替代', '定位与人群', '公开收费与边界'], [[name(cid), comps[cid]['positioning'] + '；' + comps[cid]['audience'], comps[cid].get('pricing', '未核实') + '；' + comps[cid].get('limitation', '未说明')] for cid in r['competitor_ids']]) + refs(r)
        for cid in r['competitor_ids']:
            catalog += [md_text(name(cid)), ''] + refs(comps[cid])
        catalog += ['</details>', '']
    base = base.replace('### 竞品四象限\n', '\n'.join(catalog) + '\n### 竞品四象限\n', 1)
    selection = ['### 重点对手为什么选它', '']
    for r in depth['competition']['selection']:
        selection += ['- **' + md_text(name(r['competitor_id'])) + '**（' + md_text('、'.join(ROLE_NAMES[x] for x in r['roles'])) + '）：' + md_text(r['reason']), ''] + refs(r)
    experience = selection + ['### 按用户任务分组的功能对比', '', '支持表示有官方依据，不代表效果实测；部分只覆盖子集；未核实不等于没有。任务链分组用于比较，不作未经调查的 Kano 定量分类。', '']
    fs = {f['id']: f for f in ca['features']}
    for r in depth['competition']['feature_groups']:
        experience += ['#### ' + md_text(r['title']), ''] + paragraph('用户任务', r['job']) + paragraph('差异结论', r['takeaway'])
        rs = []
        for fid in r['feature_ids']:
            f = fs[fid]
            cells = {c['competitor_id']: c for c in f['cells']}
            rs.append([f['name']] + [dict(yes='支持', partial='部分', no='不支持', unknown='未核实')[cells[cid]['state']] for cid in b['selected_competitor_ids']])
        experience += table(['功能'] + [name(cid) for cid in b['selected_competitor_ids']], rs) + refs(r)
        experience += ['<details>', '<summary>查阅功能核验依据</summary>', '']
        for fid in r['feature_ids']:
            for c in fs[fid]['cells']:
                if c['competitor_id'] in b['selected_competitor_ids']:
                    experience += [md_text(fs[fid]['name'] + ' / ' + name(c['competitor_id']) + '：' + c['basis']), ''] + refs(c)
        experience += ['</details>', '']
    experience += ['### 逐产品口碑与样本限制', '', md_text(b['review_note']), '']
    rms = {r['id']: r for r in ca['reviews']}
    for r in depth['competition']['product_reviews']:
        cid = r['competitor_id']
        meta = comps[cid].get('store', {})
        rating = str(meta.get('rating')) + '/5' if meta.get('rating') is not None else '未核实'
        count = str(meta.get('rating_count')) if meta.get('rating_count') is not None else '未知'
        experience += ['#### ' + md_text(name(cid) + ' · ' + STATE_NAMES[r['state']]), '', md_text('美国商店评分：' + rating + '；评分数：' + count + '；本轮引用文字评价：' + str(len(r['review_ids'])) + '条。评分数不是用户数。'), '', md_text(r['summary']), '']
        for key, label in [('positive', '好评'), ('negative', '差评')]:
            experience += paragraph(label, '；'.join(r[key]) if r[key] else '本轮未取得足够材料，不作结论。')
        experience += paragraph('研究判断', r['judgment'])
        coverage = next((x for x in ca['review_coverage'] if x['competitor_id'] == cid), None)
        experience += paragraph('样本限制', coverage['scope'] + '；' + coverage['time_range'] + '；' + coverage['limitation'] if coverage else '本轮未取得可说明范围的评价样本，不代表没有用户或口碑。') + refs(r) + refs(meta)
        experience += ['<details>', '<summary>查阅本产品原始评价</summary>', '']
        for rid in r['review_ids']:
            review = rms[rid]
            experience += ['- ' + md_text(str(review['rating']) + '/5｜' + (review['published_at'] or '日期未知') + '｜' + review['summary']), ''] + refs(review)
        experience += ['</details>', '']
    start = base.index('### 功能与口碑\n')
    end = base.index('### 竞争判断\n', start)
    base = base[:start] + '\n'.join(experience) + '\n' + base[end:]
    directions = ['### 可考虑的产品方向', '']
    detailed = {x['id']: x for x in d['directions']}
    if not depth['directions']:
        directions += [md_text(d.get('no_directions_reason', '尚无足够依据提出方向。')), '']
    for r in depth['directions']:
        dr = detailed[r['direction_id']]
        sc = next(row['score'] for row in direction_scores if row['id'] == dr['id'])
        directions += ['#### ' + md_text(dr['name']), '', md_text(dict(recommended='优先考虑', explore='备选方向', avoid='暂不建议')[dr['stance']] + f" · {sc['value']:.1f}/5" + ('（暂定）' if sc['provisional'] else '')), '', md_text(r['description']), '']
        for label, value in [('服务谁', dr['target_user']), ('痛点', r['pain']), ('为什么更值得做', r['better_because']), ('已有替代与剩余缺口', dr['existing_alternatives'] + '；' + dr['remaining_gap']), ('MVP主攻', dr['mvp_focus']), ('主要风险', dr['main_risk'])]:
            directions += paragraph(label, value)
        cost, feasibility = r['cost'], r['feasibility']
        directions += paragraph('相对投入', dict(low='低', medium='中', high='高', unknown='未知')[cost['level']]) + paragraph('搭建成本', cost['build']) + paragraph('持续成本', cost['ongoing'])
        directions += paragraph('技术可行性', dict(feasible='可实现', conditional='有条件可实现', not_feasible='当前不可实现', unknown='尚未核实')[feasibility['verdict']] + '；' + feasibility['summary'])
        directions += paragraph('依赖与平台边界', '；'.join(feasibility['dependencies']) or '尚未核实。')
        directions += ['<details>', '<summary>查阅方向依据与评分</summary>', ''] + refs(r) + refs(dr)
        directions += table(['评分维度', '分数 / 5', '依据'], [[row['dimension'], row['value'] if row['value'] is not None else '未知', row['reason']] for row in dr['scorecard']])
        for row in dr['scorecard']:
            directions += refs(row)
        directions += ['</details>', '']
    cost_block = next(block for section in d['sections'] if section['id'] == 'product' for block in section['blocks'] if block['id'] == 'product-cost')
    product_marker = '### ' + md_text(cost_block['title']) + '\n'
    if product_marker in base:
        base = base.replace(product_marker, '\n'.join(directions) + '\n' + product_marker, 1)
    else:
        base = base.replace('<details>\n<summary>查阅全部来源</summary>', '\n'.join(directions) + '\n<details>\n<summary>查阅全部来源</summary>', 1)
    return base
