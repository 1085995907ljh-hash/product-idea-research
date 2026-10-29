(()=>{
'use strict';
const data=JSON.parse(document.getElementById('report-data').textContent),brief=data.briefing;
const $=s=>document.querySelector(s),make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const sourceMap=new Map(data.sources.map(s=>[s.id,s])),compMap=new Map(data.competitors.map(c=>[c.id,c])),ca=data.competitive_analysis;
const isV5=data.schema_version==='product-idea-research/v5',depth=brief.depth;
const stateNames={available:'已取得材料',verified:'已核实',partial:'部分覆盖',blocked:'访问受限',unavailable:'未取得',not_run:'未开展',unknown:'未知'},roleNames={leader:'头部',similar:'最相似',new:'新进入者',adjacent:'相邻替代'};
const short=c=>c.short_name||c.name;
function link(text,url){const a=make('a',text);try{const u=new URL(url);if(['http:','https:'].includes(u.protocol)&&!u.username&&!u.password){a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';}}catch{}return a;}
function refs(parent,ids=[]){if(!ids.length)return;const row=make('div',undefined,'citations');for(const id of [...new Set(ids)].slice(0,3)){const s=sourceMap.get(id);if(s){const a=link(s.display_title||s.title,s.url);a.title=s.title+' · '+s.accessed_at+(s.status==='verified'?'':' · 未核实');row.append(a);}}if(row.childElementCount)parent.append(row);}
function icon(c){if(!c.icon)return make('span',short(c).slice(0,1),'app-icon app-fallback');const img=make('img',undefined,'app-icon');img.src=c.icon;img.alt='';img.width=35;img.height=35;return img;}
function compLink(c){const source=(c.store?.source_ids||c.source_ids||[]).map(id=>sourceMap.get(id)).find(Boolean);return c.primary_url||source?.url;}
function table(headers,rows,rowRefs=[],cls=''){const wrap=make('div',undefined,'table-scroll');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',headers.join('、')+'对比表，可左右滑动');const t=make('table',undefined,cls),head=make('tr'),thead=make('thead'),body=make('tbody');headers.forEach(h=>{const th=make('th',h);th.scope='col';head.append(th);});thead.append(head);rows.forEach((r,i)=>{const tr=make('tr');r.forEach((v,j)=>{const td=make('td',String(v));if(j===r.length-1)refs(td,rowRefs[i]||[]);tr.append(td);});body.append(tr);});t.append(thead,body);wrap.append(t);return wrap;}
const navigation=[];
function chapter(id,title,index){const s=make('section',undefined,'chapter');s.id=id;const head=make('div',undefined,'chapter-head');head.append(make('span',index,'index'),make('h2',title));s.append(head);$('#report').append(s);navigation.push({id,title,index,children:[]});return s;}
function sub(parent,id,title){const s=make('section',undefined,'subsection');s.id=id;s.append(make('h3',title));parent.append(s);navigation.find(g=>g.id===parent.id)?.children.push({id,title});return s;}
function block(parent,b){const target=sub(parent,b.id,b.title);if(b.type==='paragraph')target.append(make('p',b.text));else if(b.type==='list'){const ul=make('ul');b.items.forEach(t=>ul.append(make('li',t)));target.append(ul);}else target.append(table(b.headers,b.rows,b.row_source_ids||[]));refs(target,b.source_ids);}
function fold(parent,title){const d=make('details',undefined,'evidence-fold');d.append(make('summary',title));parent.append(d);return d;}
function labeled(parent,label,text,cls=''){const p=make('p',undefined,cls);p.append(make('strong',label+'：'),document.createTextNode(text));parent.append(p);}
function bullets(parent,values,empty){if(!values.length){parent.append(make('p',empty,'note'));return;}const ul=make('ul');values.forEach(v=>ul.append(make('li',v)));parent.append(ul);}
function evidence(parent,ids){if(ids?.length){const d=fold(parent,'查阅依据');refs(d,ids);}}
$('#meta').textContent=data.date+' · 美国市场 · '+(isV5?'摘要 + 深度研究':'约 5 分钟');$('#fixture').hidden=!data.fixture;$('#original-idea').textContent='原始想法：'+data.idea;
const overview=chapter('overview','研究概览','01');
overview.append(make('p','30–60 秒，先看判断','eyebrow'),make('h1',data.title));
const top=make('div',undefined,'overview-top'),summary=make('div'),score=make('div',undefined,'score-total');
summary.append(make('p',{go:'值得做',conditional:'观望，收窄后再考虑',no_go:'不建议按原案做'}[data.conclusion.verdict],'verdict'),make('p',data.conclusion.summary,'chapter-summary'));
score.append(make('span','总监评分'),make('strong',Number(data.computed_score.value).toFixed(1)));score.querySelector('strong').append(make('small',' / 5'));
score.append(make('p',(data.computed_score.provisional?'暂定 · ':'')+'证据把握'+({high:'高',medium:'中',low:'低'}[data.computed_score.confidence]||'未知')));top.append(summary,score);overview.append(top);
const notes=make('div',undefined,'exec-notes');
for(const [key,label]of [['recommendation','我的建议'],['alternative','更好的方向'],['mvp_focus','MVP 主攻']]){const p=make('p');p.append(make('strong',label+'：'),document.createTextNode(brief.executive[key]));notes.append(p);}overview.append(notes);
const scoreGrid=make('div',undefined,'score-grid'),names={attention:'近期热度 · 20%',competition:'竞争空间 · 20%',gap:'差异化机会 · 25%',timing:'入场时机 · 10%',validation:'验证便利 · 15%',solo_cost:'个人投入 · 10%'};
for(const r of data.scorecard){const item=make('div',undefined,'score-item'),row=make('div',undefined,'score-row'),meter=make('span',undefined,'score-meter');row.append(make('span',names[r.dimension]),make('strong',r.value===null?'未知':r.value+' / 5'));const fill=make('span');fill.style.width=r.value===null?'0':r.value/5*100+'%';meter.append(fill);item.append(row,meter,make('p',r.reason));scoreGrid.append(item);}overview.append(scoreGrid,make('p','总分按所列权重相加，四舍五入到一位小数。未知项暂按中性 2.5 计算，不代表需求中等；评分不是成功概率。','score-footnote'));

for(const [i,s]of data.sections.entries()){
  const parent=chapter(s.id,s.title,String(i+2).padStart(2,'0'));parent.append(make('p',s.summary,'chapter-summary'));
  for(const b of s.blocks){block(parent,b);if(isV5&&s.id==='market'&&b.id==='market-social')renderSocial(parent);if(isV5&&s.id==='product'&&b.id==='product-potential')renderDirections(parent);}
  if(s.id==='market')renderTrends(parent);
  if(s.id==='competition')renderCompetition(parent);
}
function renderCompetition(parent){
  if(isV5)renderCatalog(parent);
  const land=brief.landscape,landSection=sub(parent,'competition-landscape','竞品四象限');
  const wrap=make('div',undefined,'quadrant-wrap');wrap.append(make('span',land.y_high+' ↑','quadrant-y'));const grid=make('div',undefined,'quadrants');grid.setAttribute('role','group');grid.setAttribute('aria-label','竞品定性四象限');
  for(const [q,label]of [['top-left',land.y_high+' × '+land.x_low],['top-right',land.y_high+' × '+land.x_high],['bottom-left',land.y_low+' × '+land.x_low],['bottom-right',land.y_low+' × '+land.x_high]]){
    const cell=make('div',undefined,'quadrant');cell.dataset.quadrant=q;cell.append(make('div',label,'quadrant-label'));const chips=make('div',undefined,'app-chips');
    for(const e of land.entries.filter(e=>e.quadrant===q)){const c=compMap.get(e.competitor_id),a=link('',compLink(c));a.className='app-chip';a.append(icon(c),document.createTextNode(short(c)));chips.append(a);}
    if(!chips.childElementCount)chips.append(make('p','本轮未归入样本','note'));cell.append(chips);grid.append(cell);
  }
  const axis=make('div',undefined,'quadrant-axis');axis.append(make('span','← '+land.x_low),make('span',land.x_high+' →'));wrap.append(grid,axis);landSection.append(wrap,make('p',land.y_low+'在下方。'+land.note,'quadrant-note'));
  const selected=sub(parent,'competition-selected','重点竞品');selected.append(make('p',brief.selection_reason,'note'));const cards=make('div',undefined,'competitor-grid');
  for(const cid of brief.selected_competitor_ids){const c=compMap.get(cid),a=make('article',undefined,'competitor'),head=make('div',undefined,'competitor-heading'),text=make('div'),h=make('h4');h.append(link(short(c),compLink(c)));text.append(h);const meta=c.store||{};text.append(make('div',meta.rating!==null&&meta.rating!==undefined&&meta.rating_count?Number(meta.rating).toFixed(1)+' / 5 · '+meta.rating_count.toLocaleString()+' 份评分':'评分样本不足 / 未核实','store-rating'));head.append(icon(c),text);a.append(head,make('p',c.brief||c.positioning),make('p',c.pricing||'收费未核实','pricing'));if(isV5){const why=depth.competition.selection.find(r=>r.competitor_id===cid);a.append(make('p',why.roles.map(r=>roleNames[r]).join(' · '),'role-label'));labeled(a,'入选理由',why.reason);evidence(a,why.source_ids);}cards.append(a);}selected.append(cards,make('p','评分来自本轮美国商店；评分数不是用户数。价格为公开目录，促销、旧 SKU 与实际购买页可能不同。','note'));
  if(isV5){renderFeatureGroups(parent);renderProductReviews(parent);}else{
  const experience=sub(parent,'competition-experience','功能与口碑'),selectedIds=brief.selected_competitor_ids;
  const featureRows=ca.features.filter(f=>brief.feature_ids.includes(f.id));
  const scroll=make('div',undefined,'table-scroll');scroll.tabIndex=0;scroll.setAttribute('role','region');scroll.setAttribute('aria-label','重点竞品功能矩阵，可左右滑动');
  const t=make('table',undefined,'feature-table'),thead=make('thead'),tr=make('tr'),tbody=make('tbody');['关键功能',...selectedIds.map(id=>short(compMap.get(id)))].forEach(title=>{const th=make('th',title);th.scope='col';tr.append(th);});thead.append(tr);
  for(const f of featureRows){const row=make('tr');row.append(make('td',f.short_name||f.name));for(const id of selectedIds){const c=f.cells.find(c=>c.competitor_id===id),td=make('td',undefined,c.state),label={yes:'支持',partial:'部分',no:'不支持',unknown:'未核实'}[c.state];td.append(make('span',label));td.title=c.basis;const source=sourceMap.get(c.source_ids?.[0]);if(source){const a=link('依据',source.url);a.className='cell-source';a.title=c.basis;td.append(a);}row.append(td);}tbody.append(row);}t.append(thead,tbody);scroll.append(t);experience.append(scroll,make('p','“支持”指官方明确列出，不代表效果经实测；“部分”只覆盖子集；“未核实”不等于没有。','note'),make('p',brief.review_note,'note'));
  const reviews=make('div',undefined,'reviews');for(const r of ca.reviews.filter(r=>brief.review_ids.includes(r.id))){const a=make('article',undefined,'review'),meta=make('div',undefined,'review-meta');meta.append(make('span',short(compMap.get(r.competitor_id))),make('span',r.rating+' / 5'),make('span',r.published_at));a.append(meta,make('h4',r.rating>=4?'好评 / 保留理由':'差评 / 不满'),make('p',r.summary));const source=sourceMap.get(r.source_ids?.[0]);if(source)a.append(link('查看原评价',r.original_url||source.url));reviews.append(a);}if(!reviews.childElementCount)reviews.append(make('p','未取得可引用的文字评价，不作口碑优劣判断。','note'));experience.append(reviews);
  }
  const j=brief.competition_judgment,judgment=sub(parent,'competition-judgment','竞争判断'),box=make('div',undefined,'competition-judgment');box.append(make('h3',{yes:'能形成有依据的差异',conditional:'可以做出区别，价值仍有条件',no:'原案目前做不出有说服力的差异',unknown:'尚不能判断差异化机会'}[j.verdict]),make('p',j.summary));for(const [key,label]of [['our_advantage','我们的优势'],['our_disadvantage','我们的劣势']]){const p=make('p');p.append(make('strong',label+'：'),document.createTextNode(j[key]));box.append(p);}refs(box,j.source_ids);judgment.append(box);
}
function renderSocial(parent){
  const section=sub(parent,'market-platforms','各平台在讨论什么'),posts=new Map(data.social_research.posts.map(p=>[p.id,p])),platforms=new Map(data.social_research.platforms.map(p=>[p.id,p]));
  if(!depth.market.social_platforms.length)section.append(make('p','尚未取得平台材料；缺失不等于没有需求。','note'));
  const grid=make('div',undefined,'depth-grid');
  for(const r of depth.market.social_platforms){const card=make('article',undefined,'depth-card');card.append(make('div',r.label+' · '+stateNames[r.state],'card-kicker'),make('p',r.summary));labeled(card,'痛点',r.pain);labeled(card,'机会判断',r.opportunity);const d=fold(card,'查阅原帖与覆盖限制'),p=platforms.get(r.id);d.append(make('p',p.query_scope+'；'+p.time_range+'；'+p.limitation,'note'));for(const pid of r.post_ids){const post=posts.get(pid),a=make('article',undefined,'source-record');a.append(make('p',(post.published_at||'日期未知')+' · '+post.region+' · '+(post.state==='verified'?'原文已核实':'仅有线索'),'note'),make('p',post.context));if(post.quote)a.append(make('blockquote',post.quote));refs(a,post.source_ids);d.append(a);}refs(d,r.source_ids);grid.append(card);}section.append(grid);
  const findings=sub(parent,'market-findings','需求、新变化与机会');
  if(!depth.market.social_findings.length)findings.append(make('p','尚无足够材料形成跨平台观察。','note'));
  for(const r of depth.market.social_findings){const article=make('article',undefined,'finding');article.append(make('h4',r.title));for(const [key,label]of [['need','需求'],['newness','新旧性质'],['opportunity','可做的机会'],['avoid','不宜进入的部分']])labeled(article,label,r[key]);evidence(article,r.source_ids);findings.append(article);}
}
function renderCatalog(parent){
  const section=sub(parent,'competition-catalog','分类竞品全量目录');section.append(make('p','按用户任务整理本轮发现的产品与人工替代；同一产品可出现于多个任务分类。目录覆盖本轮样本，不代表市场穷尽。','note'));
  if(!depth.competition.catalog_groups.length)section.append(make('p','尚未取得可核验目录。','note'));
  for(const r of depth.competition.catalog_groups){const article=make('article',undefined,'catalog-group');article.append(make('h4',r.title+' · '+r.competitor_ids.length+' 款'),make('p',r.description));const d=fold(article,'查看本类全部产品');for(const cid of r.competitor_ids){const c=compMap.get(cid),item=make('article',undefined,'catalog-item'),h=make('h4');h.append(icon(c),link(short(c),compLink(c)));item.append(h,make('p',c.positioning+'；'+c.audience));labeled(item,'公开收费',c.pricing||'未核实','note');labeled(item,'研究边界',c.limitation||'尚未说明','note');refs(item,c.source_ids);d.append(item);}refs(d,r.source_ids);section.append(article);}
}
function featureMatrix(features,ids){
  const scroll=make('div',undefined,'table-scroll');scroll.tabIndex=0;scroll.setAttribute('role','region');scroll.setAttribute('aria-label','按用户任务分组的功能对比，可左右滑动');const t=make('table',undefined,'feature-table'),thead=make('thead'),tr=make('tr'),tbody=make('tbody');['功能',...ids.map(id=>short(compMap.get(id)))].forEach(title=>{const th=make('th',title);th.scope='col';tr.append(th);});thead.append(tr);
  for(const f of features){const row=make('tr');row.append(make('td',f.short_name||f.name));for(const id of ids){const c=f.cells.find(c=>c.competitor_id===id),td=make('td',{yes:'支持',partial:'部分',no:'不支持',unknown:'未核实'}[c.state],c.state);td.title=c.basis;row.append(td);}tbody.append(row);}t.append(thead,tbody);scroll.append(t);return scroll;
}
function renderFeatureGroups(parent){
  const section=sub(parent,'competition-features','按用户任务分组的功能对比');section.append(make('p','“支持”指官方明确列出，不代表效果实测；“部分”覆盖子集；“未核实”不等于没有。按任务链比较，不作缺少用户调查的 Kano 定量分类。','note'));
  if(!depth.competition.feature_groups.length)section.append(make('p','尚未完成关键任务功能核验。','note'));
  for(const r of depth.competition.feature_groups){const group=make('article',undefined,'feature-group');group.append(make('h4',r.title));labeled(group,'用户任务',r.job);labeled(group,'差异结论',r.takeaway);const features=r.feature_ids.map(id=>ca.features.find(f=>f.id===id));group.append(featureMatrix(features,brief.selected_competitor_ids));const d=fold(group,'查阅逐功能核验依据');for(const f of features){const a=make('div',undefined,'source-record');a.append(make('h4',f.name));for(const cid of brief.selected_competitor_ids){const c=f.cells.find(c=>c.competitor_id===cid);a.append(make('p',short(compMap.get(cid))+'：'+c.basis));refs(a,c.source_ids);}d.append(a);}refs(d,r.source_ids);section.append(group);}
}
function renderProductReviews(parent){
  const section=sub(parent,'competition-reviews','逐产品口碑与样本限制');section.append(make('p',brief.review_note,'note'));
  if(!brief.selected_competitor_ids.length)section.append(make('p','尚未选定重点产品，暂不判断口碑。','note'));
  for(const cid of brief.selected_competitor_ids){const r=depth.competition.product_reviews.find(r=>r.competitor_id===cid),c=compMap.get(cid),article=make('article',undefined,'product-review'),h=make('h4');h.append(icon(c),document.createTextNode(short(c)));article.append(h,make('p',stateNames[r.state],'card-kicker'));const meta=c.store||{},rating=meta.rating===null||meta.rating===undefined?'未核实':Number(meta.rating).toFixed(1)+' / 5',count=meta.rating_count===null||meta.rating_count===undefined?'未知':meta.rating_count.toLocaleString();article.append(make('p','美国商店评分 '+rating+' · 评分数 '+count+' · 本轮引用文字评价 '+r.review_ids.length+' 条。评分数不是用户数。','note'),make('p',r.summary));for(const [key,label]of [['positive','好评'],['negative','差评']]){const box=make('div');box.append(make('strong',label));bullets(box,r[key],'本轮未取得足够材料，不作结论。');article.append(box);}labeled(article,'研究判断',r.judgment);const coverage=ca.review_coverage.find(r=>r.competitor_id===cid);labeled(article,'样本限制',coverage?coverage.scope+'；'+coverage.time_range+'；'+coverage.limitation:'本轮未取得可说明范围的评价样本，不代表没有用户或口碑。','note');const d=fold(article,'查阅本产品原始评价与依据');for(const rid of r.review_ids){const review=ca.reviews.find(r=>r.id===rid),a=make('div',undefined,'source-record');a.append(make('p',review.rating+' / 5 · '+(review.published_at||'日期未知')+' · '+(review.version||'版本未知'),'note'),make('p',review.summary));if(review.quote)a.append(make('blockquote',review.quote));refs(a,review.source_ids);d.append(a);}refs(d,r.source_ids);refs(d,meta.source_ids);if(coverage)refs(d,coverage.source_ids);section.append(article);}
}
function renderDirections(parent){
  const section=sub(parent,'product-directions','可考虑的产品方向');if(!depth.directions.length)section.append(make('p',data.no_directions_reason||'尚无足够依据提出方向。','note'));
  const scoreMap=new Map(data.computed_directions.map(r=>[r.id,r.score]));
  for(const r of depth.directions){const dr=data.directions.find(d=>d.id===r.direction_id),card=make('article',undefined,'direction-card'),sc=scoreMap.get(dr.id);card.append(make('p',{recommended:'优先考虑',explore:'备选方向',avoid:'暂不建议'}[dr.stance]+' · '+sc.value.toFixed(1)+' / 5'+(sc.provisional?'（暂定）':''),'card-kicker'),make('h4',dr.name),make('p',r.description));for(const [label,text]of [['服务谁',dr.target_user],['痛点',r.pain],['为什么更值得做',r.better_because],['已有替代与剩余缺口',dr.existing_alternatives+'；'+dr.remaining_gap],['MVP 主攻',dr.mvp_focus],['主要风险',dr.main_risk]])labeled(card,label,text);const costs=make('div',undefined,'direction-costs'),cost=make('div'),feasibility=make('div');cost.append(make('h5','投入 · '+{low:'低',medium:'中',high:'高',unknown:'未知'}[r.cost.level]));labeled(cost,'搭建',r.cost.build);labeled(cost,'持续',r.cost.ongoing);feasibility.append(make('h5','技术 · '+{feasible:'可实现',conditional:'有条件可实现',not_feasible:'当前不可实现',unknown:'尚未核实'}[r.feasibility.verdict]),make('p',r.feasibility.summary));bullets(feasibility,r.feasibility.dependencies,'依赖条件尚未核实。');costs.append(cost,feasibility);card.append(costs);const d=fold(card,'查阅方向依据与评分');refs(d,r.source_ids);refs(d,dr.source_ids);d.append(table(['评分维度','分数 / 5','依据'],dr.scorecard.map(row=>[names[row.dimension],row.value===null?'未知':row.value,row.reason]),dr.scorecard.map(row=>row.source_ids)));section.append(card);}
}
function renderTrends(parent){
  const section=sub(parent,'market-trends',isV5?'多组关键词与搜索兴趣走势':'搜索兴趣走势');section.append(make('p',brief.trend_summary));
  const all=data.trends||[],keywordGroups=isV5?depth.market.keyword_groups:[];if(!all.length&&!keywordGroups.length){section.append(make('p','没有原始序列，暂不绘图；缺数据不等于没有需求。','note'));return;}
  const controls=make('div',undefined,'trend-controls'),label=make('label','时间窗口'),select=make('select');select.id='trends-window';select.setAttribute('aria-label','搜索趋势时间窗口');const windows=[...new Set(all.map(t=>t.window))];windows.forEach(w=>{const option=make('option',w);option.value=w;select.append(option);});select.value=windows.find(w=>w.includes('12'))||windows[0];label.append(select);controls.append(label);section.append(controls);const chartArea=make('div');chartArea.id='trends';section.append(chartArea);
  const groupSelect=make('select');if(isV5){const groupLabel=make('label','关键词组');groupSelect.id='trends-group';groupSelect.setAttribute('aria-label','搜索趋势关键词组');keywordGroups.forEach(r=>{const option=make('option',r.title);option.value=r.id;groupSelect.append(option);});groupLabel.append(groupSelect);controls.prepend(groupLabel);groupSelect.addEventListener('change',draw);}
  const NS='http://www.w3.org/2000/svg',svg=(tag,attrs,text)=>{const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));if(text!==undefined)n.textContent=text;return n;};
  const colors=['#2d5b82','#5c8374','#a08a68','#7d7897'];
  function draw(){
    chartArea.replaceChildren();
    if(isV5){const selected=keywordGroups.find(r=>r.id===groupSelect.value);if(selected){const intro=make('div',undefined,'keyword-intro');intro.append(make('h4',selected.title),make('p',selected.intent),make('p',selected.summary));labeled(intro,'检索词',selected.keywords.join('、'),'note');evidence(intro,selected.source_ids);chartArea.append(intro);}}
    const filtered=all.filter(t=>t.window===select.value&&(!isV5||t.group===groupSelect.value)),groups=[...new Set(filtered.map(t=>[t.group,t.geo,t.category,t.search_type,t.granularity].join('|')))];
    if(!filtered.length)chartArea.append(make('p','本关键词组在此窗口没有原始序列，暂不绘图；缺数据不等于没有需求。','trend-empty'));
    for(const key of groups){
      const group=filtered.filter(t=>[t.group,t.geo,t.category,t.search_type,t.granularity].join('|')===key),legend=make('div',undefined,'trend-legend'),box=make('div',undefined,'trend-chart'),plot=make('div'),checks=[];
      group.forEach((t,i)=>{const label=make('label'),check=make('input');check.type='checkbox';check.checked=!t.exclude_by_default;check.setAttribute('aria-label',t.keyword+'趋势');const swatch=make('i');swatch.style.background=colors[i%colors.length];label.append(check,swatch,document.createTextNode(t.keyword));legend.append(label);checks.push(check);check.addEventListener('change',paint);});box.append(legend,plot);chartArea.append(box);
      function paint(){
        plot.replaceChildren();const active=group.filter((t,i)=>checks[i].checked);if(!active.length){plot.append(make('p','勾选关键词查看走势。','trend-empty'));return;}
        const dates=[...new Set(group.flatMap(t=>t.points.map(p=>p.date)))].sort();if(!dates.length||!active.some(t=>t.points.some(p=>p.value!==null))){plot.append(make('p','尚无可绘制的原始数据点。','trend-empty'));return;}
        const graph=svg('svg',{viewBox:'0 0 740 250',role:'img','aria-label':group[0].geo+' '+select.value+' Google Trends相对搜索兴趣，0至100'});graph.append(svg('desc',{},'只比较同一查询组同一时间窗；缺失不补零，未完成周期不连线。'));const x=date=>45+dates.indexOf(date)/Math.max(dates.length-1,1)*665,y=value=>205-value*1.7;
        for(const v of [0,25,50,75,100])graph.append(svg('line',{x1:45,x2:710,y1:y(v),y2:y(v),stroke:'#e0e5e9'}),svg('text',{x:34,y:y(v)+4,'text-anchor':'end',fill:'#65717c','font-size':11},v));
        for(const trend of active){const color=colors[group.indexOf(trend)%colors.length];let path='',connected=false;const dots=[];trend.points.forEach(p=>{if(p.value===null){connected=false;return;}if(p.partial)connected=false;else{path+=(connected?'L':'M')+x(p.date)+','+y(p.value)+' ';connected=true;}const dot=svg('circle',{cx:x(p.date),cy:y(p.value),r:p.partial?3:2,fill:p.partial?'white':color,stroke:color});dot.append(svg('title',{},trend.keyword+' '+p.date+'：'+p.value+(p.partial?'（未完成周期）':'')));dots.push(dot);});graph.append(svg('path',{d:path,stroke:color,'stroke-width':2,fill:'none'}),...dots);}
        for(const i of new Set([0,Math.floor((dates.length-1)/2),dates.length-1]))graph.append(svg('text',{x:x(dates[i]),y:232,'text-anchor':'middle',fill:'#65717c','font-size':10},dates[i]));plot.append(graph);
      }
      paint();const ambiguity=group.filter(t=>t.exclude_by_default).map(t=>t.keyword);if(ambiguity.length)box.append(make('p',ambiguity.join('、')+' 意图混杂，默认隐藏；可勾选查看。','note'));refs(box,group.flatMap(t=>t.source_ids));
    }
    chartArea.append(make('p','Google Trends 相对指数，非搜索次数；只有同一查询组、地区、搜索类型和时间窗口内的词可比较。各组、各窗口独立归一化，不可跨组或跨窗口比较绝对大小。空心点为未完成周期；缺失值不补零。','note'));
  }
  select.addEventListener('change',draw);draw();
}
for(const group of navigation){const div=make('div',undefined,'toc-group'),a=make('a');a.href='#'+group.id;a.append(make('span',group.index),document.createTextNode(group.title));div.append(a);const option=make('option',group.index+' '+group.title);option.value=group.id;$('#mobile-toc').append(option);if(group.children.length){const sub=make('div',undefined,'toc-sub');group.children.forEach(child=>{const a=make('a',child.title);a.href='#'+child.id;sub.append(a);const option=make('option','　'+child.title);option.value=child.id;$('#mobile-toc').append(option);});div.append(sub);}$('#toc').append(div);}
$('#mobile-toc').addEventListener('change',()=>{location.hash=$('#mobile-toc').value;});
const anchors=[...document.querySelectorAll('#toc a')],targets=anchors.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean);let ticking=false;
function active(){let id='overview';for(const target of targets)if(target.getBoundingClientRect().top<=100)id=target.id;anchors.forEach(a=>a.setAttribute('aria-current',String(a.hash==='#'+id)));$('#mobile-toc').value=id;ticking=false;}
addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(active);ticking=true;}},{passive:true});active();
data.sources.forEach(s=>{const item=make('div');item.append(link(s.id+' · '+s.title,s.url),make('p',s.accessed_at+' · '+(s.status==='verified'?'已查阅':'未核实')));$('#all-sources').append(item);});
function download(name,blob){const a=make('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('#download-md').onclick=()=>download('research.md',new Blob([data.markdown],{type:'text/markdown;charset=utf-8'}));
$('#download-zip').onclick=()=>{const bytes=Uint8Array.from(atob(data.zip_base64),c=>c.charCodeAt(0));download('research.zip',new Blob([bytes],{type:'application/zip'}));};
$('#print').onclick=()=>print();
})();
