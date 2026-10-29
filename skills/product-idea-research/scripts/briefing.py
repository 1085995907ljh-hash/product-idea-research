"""v4 five-minute presentation contract; detailed evidence stays in research.json."""
from html import escape
import re

SCRIPT_INTERFACE = 'internal-module'
SCRIPT_INTERFACE_REASON = 'Imported by report.py for v4 validation and Markdown presentation.'
V4 = 'product-idea-research/v4'
CHAPTERS = [('market', '市场调研'), ('competition', '竞品'), ('product', '产品研究')]
BLOCKS = {
    'market': [('market-overview', '市场全貌'), ('market-social', '社交平台讨论'), ('market-scale', '市场规模与走势'), ('market-users', '美国目标用户')],
    'competition': [],
    'product': [('product-potential', '潜力与切入建议'), ('product-cost', '投入成本'), ('product-cautions', '平台与技术')],
}
QUADRANTS = ('top-left', 'top-right', 'bottom-left', 'bottom-right')
SHORT_NAMES = dict(attention='近期热度', competition='竞争空间', gap='差异化机会', timing='入场时机', validation='验证便利', solo_cost='个人投入')
WEIGHT_PERCENT = dict(attention=20, competition=20, gap=25, timing=10, validation=15, solo_cost=10)


def initial_briefing():
    return dict(executive=dict(recommendation='尚未研究，不作入场建议。', alternative='尚无依据推荐更好的方向。', mvp_focus='尚未确定。'), landscape=dict(x_low='记录与整理', x_high='分析与建议', y_low='单次使用', y_high='持续跟踪', entries=[], note='定性定位，不代表市场份额或产品效果。'), selected_competitor_ids=[], selection_reason='尚未确定重点竞品。', feature_ids=[], review_ids=[], review_note='尚未取得评价；缺失不等于没有用户。', trend_summary='尚未取得搜索趋势；不据此判断需求。', competition_judgment=dict(verdict='unknown', summary='尚未研究，不能判断能否差异化。', our_advantage='尚未确定。', our_disadvantage='尚未确定。', source_ids=[]))


def validate_briefing(d, *, limits=(7, 6, 4), prefix='v4'):
    errors = []
    def need(ok, msg):
        if not ok:
            errors.append(prefix + ': ' + msg)
    def text(v):
        return isinstance(v, str) and bool(v.strip())
    def obj(v):
        need(isinstance(v, dict), '须为对象')
        return v if isinstance(v, dict) else {}
    def rows(v):
        need(isinstance(v, list) and all(isinstance(r, dict) for r in v), '须为对象数组')
        return [r for r in v if isinstance(r, dict)] if isinstance(v, list) else []
    def fields(r, keys):
        for k in keys.split():
            need(text(r.get(k)), '缺少文本 ' + k)
    source_ids = {s.get('id') for s in rows(d.get('sources')) if isinstance(s.get('id'), str)}
    def refs(r, required=False):
        ids = r.get('source_ids', [])
        valid = isinstance(ids, list) and all(isinstance(x, str) for x in ids)
        need(valid and set(ids).issubset(source_ids) if valid else False, '无效来源引用')
        if required:
            need(bool(ids), '定位或判断须有可追溯来源')
    b = obj(d.get('briefing'))
    ex = obj(b.get('executive'))
    fields(ex, 'recommendation alternative mvp_focus')
    overview = [d.get('conclusion', {}).get('summary', ''), *d.get('conclusion', {}).get('reasons', []), *ex.values(), *[r.get('reason', '') for r in d.get('scorecard', [])]]
    need(all(isinstance(v, str) and not re.search(r'https?://|\[[^\]]+\]\(|<a\b', v, re.I) for v in overview), '研究概览禁止链接')
    need(sum(len(v) for v in overview if isinstance(v, str)) <= 900, '研究概览过长，含评分理由最多900字符')
    for r in d.get('scorecard', []):
        need(len(r.get('reason', '')) <= 90, '子项评分理由最多90字符')
    sections = rows(d.get('sections'))
    need([(s.get('id'), s.get('title')) for s in sections] == CHAPTERS, '正文须按市场调研、竞品、产品研究排列')
    seen = set()
    for s in sections:
        blocks = rows(s.get('blocks', []))
        need([x.get('id') for x in blocks] == [x for x, _ in BLOCKS.get(s.get('id'), [])], '章节子目录须按约定排列')
        for block in blocks:
            bid = block.get('id')
            need(isinstance(bid, str) and bid not in seen, '子目录ID无效或重复')
            if isinstance(bid, str):
                seen.add(bid)
    comps = {c['id']: c for c in rows(d.get('competitors')) if isinstance(c.get('id'), str)}
    ca = obj(d.get('competitive_analysis'))
    def linked(key, universe, maximum):
        values = b.get(key)
        valid = isinstance(values, list) and all(isinstance(x, str) for x in values)
        need(valid and len(values) <= maximum and len(values) == len(set(values)) and set(values).issubset(universe) if valid else False, key + '无效或过多')
        return values if valid else []
    selected = linked('selected_competitor_ids', comps, limits[0])
    linked('feature_ids', {f['id'] for f in rows(ca.get('features')) if isinstance(f.get('id'), str)}, limits[1])
    linked('review_ids', {r['id'] for r in rows(ca.get('reviews')) if isinstance(r.get('id'), str)}, limits[2])
    for cid in selected:
        need(cid in ca.get('feature_competitor_ids', []), '重点竞品必须在已核验功能表中')
    fields(b, 'selection_reason review_note trend_summary')
    landscape = obj(b.get('landscape'))
    fields(landscape, 'x_low x_high y_low y_high note')
    entries = rows(landscape.get('entries'))
    need(len(entries) <= 12, '四象限最多12款，避免拥挤')
    ids = [r.get('competitor_id') for r in entries]
    need(all(isinstance(x, str) for x in ids) and len(ids) == len(set(x for x in ids if isinstance(x, str))), '四象限竞品重复或无效')
    for r in entries:
        need(r.get('competitor_id') in comps if isinstance(r.get('competitor_id'), str) else False, '四象限竞品不存在')
        need(r.get('quadrant') in QUADRANTS if isinstance(r.get('quadrant'), str) else False, '无效象限')
        refs(r, True)
    judgment = obj(b.get('competition_judgment'))
    fields(judgment, 'summary our_advantage our_disadvantage')
    need(judgment.get('verdict') in ('yes', 'conditional', 'no', 'unknown') if isinstance(judgment.get('verdict'), str) else False, '差异化判断无效')
    refs(judgment, judgment.get('verdict') != 'unknown')
    for c in comps.values():
        icon = c.get('icon')
        if icon:
            need(isinstance(icon, str) and bool(re.fullmatch(r'data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=]+', icon)), '图标须内嵌PNG/JPEG/WebP，禁止脚本或远程依赖')
        meta = c.get('store', {})
        if meta:
            meta = obj(meta)
            rating = meta.get('rating')
            count = meta.get('rating_count')
            need(rating is None or type(rating) in (int, float) and 0 <= rating <= 5, '商店评分无效')
            need(count is None or type(count) is int and count >= 0, '商店评分数无效')
            refs(meta, rating is not None or count is not None)
    return errors


def markdown_briefing(d, computed_score, md_text):
    """Same four chapters as HTML; full evidence remains downloadable as JSON."""
    b = d['briefing']
    source_map = {s['id']: s for s in d['sources']}
    comps = {c['id']: c for c in d['competitors']}
    ca = d['competitive_analysis']
    out = ['# ' + md_text(d['title']), '', md_text(d['date'] + '｜' + d['scope']), '']
    def refs(record):
        ids = list(dict.fromkeys(record.get('source_ids', [])))
        if ids:
            out.extend([' '.join('[' + md_text(i) + '](' + source_map[i]['url'].replace('(', '%28').replace(')', '%29') + ')' for i in ids), ''])
    def table(headers, rows):
        out.extend(['| ' + ' | '.join(md_text(x).replace('\n', ' ') for x in headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'])
        out.extend('| ' + ' | '.join(md_text(str(x)).replace('\n', ' ') for x in row) + ' |' for row in rows)
        out.append('')
    if d['fixture']:
        out.extend(['> 阅读样例，非真实市场调研。', ''])
    out.extend(['## 一、研究概览', '', md_text(d['conclusion']['summary']), ''])
    out.extend('- ' + md_text(x) for x in d['conclusion'].get('reasons', []))
    ex = b['executive']
    for k, label in [('recommendation', '总监建议'), ('alternative', '更好的方向'), ('mvp_focus', 'MVP主攻')]:
        out.extend(['', '**' + label + '：**' + md_text(ex[k])])
    out.extend(['', f"总监评分：{computed_score['value']:.1f}/5" + ('（暂定）' if computed_score['provisional'] else ''), ''])
    table(['维度', '权重', '分数 / 5', '简短理由'], [[SHORT_NAMES[r['dimension']], str(WEIGHT_PERCENT[r['dimension']])+'%', r['value'] if r['value'] is not None else '未知', r['reason']] for r in d['scorecard']])
    out.extend(['总分按所列权重相加，四舍五入到一位小数；评分是研究判断，不是成功概率；未知项仅以中性2.5计算暂定总分。', ''])
    for s in d['sections']:
        prefix = {'market': '二', 'competition': '三', 'product': '四'}[s['id']]
        out.extend(['## ' + prefix + '、' + s['title'], '', md_text(s['summary']), ''])
        refs(s)
        for block in s['blocks']:
            out.extend(['### ' + md_text(block['title']), ''])
            if block['type'] == 'paragraph':
                out.extend([md_text(block['text']), ''])
            elif block['type'] == 'list':
                out.extend(['- ' + md_text(x) for x in block['items']]+[''])
            else:
                table(block['headers'], block['rows'])
                for ids in block.get('row_source_ids', []):
                    refs(dict(source_ids=ids))
            refs(block)
        if s['id'] == 'market':
            out.extend(['### 搜索兴趣走势', '', md_text(b['trend_summary']), ''])
            windows = {}
            for t in d['trends']:
                key = (t['window'], t['geo'], t['group'])
                windows.setdefault(key, []).append(t)
            for key, trends in windows.items():
                reasons = list(dict.fromkeys(t['reason'] for t in trends))
                out.append('- ' + md_text(key[0] + '｜' + key[1] + '：' + ' '.join(reasons)))
                refs(dict(source_ids=[sid for t in trends for sid in t['source_ids']]))
            out.extend(['完整逐期数据保留在研究包research.json中；网页可切换窗口查看真实序列。', ''])
        if s['id'] == 'competition':
            land = b['landscape']
            out.extend(['### 竞品四象限', '', md_text(land['note']), ''])
            table(['象限', '竞品'], [[{'top-left': land['y_high'] + ' / ' + land['x_low'], 'top-right': land['y_high'] + ' / ' + land['x_high'], 'bottom-left': land['y_low'] + ' / ' + land['x_low'], 'bottom-right': land['y_low'] + ' / ' + land['x_high']}[q], '、'.join(comps[e['competitor_id']].get('short_name', comps[e['competitor_id']]['name']) for e in land['entries'] if e['quadrant'] == q) or '本轮未归入样本（不代表没有产品）'] for q in QUADRANTS])
            for e in land['entries']:
                refs(e)
            out.extend(['### 重点竞品', '', md_text(b['selection_reason']), ''])
            for cid in b['selected_competitor_ids']:
                c = comps[cid]
                meta = c.get('store', {})
                rating = f"{meta['rating']:.1f}/5，{meta['rating_count']}份评分" if meta.get('rating') is not None and meta.get('rating_count') else '商店评分未知/不足'
                out.extend(['- **' + md_text(c.get('short_name', c['name'])) + '**：' + md_text(c.get('brief', c.get('positioning', '')) + '。' + rating + '。' + c.get('pricing', '收费未核实')), ''])
                refs(c)
            out.extend(['### 功能与口碑', ''])
            selected = b['selected_competitor_ids']
            names = dict(yes='支持', partial='部分', no='不支持', unknown='未核实')
            selected_features = [f for f in ca['features'] if f['id'] in b['feature_ids']]
            feature_rows = []
            for f in selected_features:
                cells = {c['competitor_id']: c for c in f['cells']}
                feature_rows.append([f['name']] + [names[cells[cid]['state']] for cid in selected])
            table(['关键功能'] + [comps[cid].get('short_name', comps[cid]['name']) for cid in selected], feature_rows)
            out.extend(['<details>', '<summary>查阅功能核验来源</summary>', ''])
            for f in selected_features:
                cells = {c['competitor_id']: c for c in f['cells']}
                for cid in selected:
                    out.append(md_text(f['name'] + ' / ' + comps[cid].get('short_name', comps[cid]['name'])))
                    refs(cells[cid])
            out.extend(['</details>', ''])
            out.extend([md_text(b['review_note']), ''])
            for r in ca['reviews']:
                if r['id'] in b['review_ids']:
                    out.extend(['- ' + md_text(comps[r['competitor_id']].get('short_name', comps[r['competitor_id']]['name']) + f"｜{r['rating']}/5｜{r['published_at']}：" + r['summary']), ''])
                    refs(r)
            j = b['competition_judgment']
            out.extend(['### 竞争判断', '', md_text(j['summary']), '', '**我们的优势：**' + md_text(j['our_advantage']), '', '**我们的劣势：**' + md_text(j['our_disadvantage']), ''])
            refs(j)
    out.extend(['<details>', '<summary>查阅全部来源</summary>', ''])
    for source in d['sources']:
        out.append('- ' + md_text(source['title'] + '｜' + source['accessed_at']))
        refs(dict(source_ids=[source['id']]))
    out.extend(['</details>', ''])
    return '\n'.join(out)
