'use strict';
const data=JSON.parse(document.getElementById('report-data').textContent);
const $=s=>document.querySelector(s);
const isV2=['product-idea-research/v2','product-idea-research/v3'].includes(data.schema_version);
document.body.classList.toggle('report-v2',isV2);
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const sources=data.sources||[],evidence=data.evidence||[],competitors=data.competitors||[],directions=data.directions||[];
const sourceById=new Map(sources.map(s=>[s.id,s]));
const directionScores=new Map((data.computed_directions||[]).map(d=>[d.id,d.score]));
const states={fact:'已核实事实',estimate:'估算',hypothesis:'假设',unverified:'未核实',inference:'研究推断'};
const status={complete:'已研究',partial:'部分覆盖',not_run:'未开展'};
const certaintyNames={supported:'直接证据',inferred:'有限推断',unknown:'未知'};
const confidenceNames={high:'高',medium:'中',low:'低'};
const dimensionNames=isV2?{attention:'近期需求与话题热度',competition:'入场拥挤程度',gap:'可抓住的具体缺口',timing:'现在入场的时机',validation:'低成本验证难度',solo_cost:'独立开发投入'}:{demand:'需求依据',jobs:'结果机会',competition:'竞争缺口',market:'市场与趋势',business:'付费与商业',buildability:'小团队可做性',risk:'风险可控程度'};
const weights={attention:20,competition:20,gap:25,timing:10,validation:15,solo_cost:10};
const stanceNames={recommended:'推荐先验证',explore:'可以探索',avoid:'暂不建议'};
const tocEntries=[];
function addToc(id,title){tocEntries.push({id,title});}
function safeLink(label,url){
  const a=node('a',label);
  try{const u=new URL(url);if(['https:','http:'].includes(u.protocol)&&!u.username&&!u.password){a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';}}catch{}
  return a;
}
function refs(parent,ids=[],compact=false){
  if(!ids.length)return;
  const p=node('div',undefined,'sources-inline');
  for(const id of ids){
    const source=sourceById.get(id);if(!source)continue;
    const title=id+' · '+source.title+(source.status==='verified'?'':'（未核实）');
    const link=safeLink(compact?id:title,source.url);if(compact){link.title=title;link.setAttribute('aria-label',title);}
    p.append(link);
  }
  if(p.childElementCount)parent.append(p);
}
function unknownDimensions(score,rows=[]){
  const ids=new Set([...(score?.unknown_dimensions||[]),...rows.filter(r=>r.value===null||r.certainty==='unknown').map(r=>r.dimension)]);
  return [...ids].map(id=>dimensionNames[id]||id);
}
function scoreSummary(parent,score,rows=[],compact=false){
  if(!score){parent.append(node('p','尚未生成评分。','help'));return;}
  if(!isV2){
    parent.append(node('p',(score.value===null?'综合分暂不计算。':`综合分 ${score.value}/5${score.stars===null||score.stars===undefined?'':`，${score.stars} 星`}。`)+(score.reason||''),'legacy-score'));
    return;
  }
  const unknown=unknownDimensions(score,rows),provisional=score.provisional||unknown.length>0;
  const headline=node('div',undefined,'score-headline');
  headline.append(node('span',compact?'综合判断':'原始 idea','score-label'),node('strong',score.value===null?'未评分':Number(score.value).toFixed(1)+' / 5','score-value'));
  if(provisional)headline.append(node('span','暂定','provisional'));
  parent.append(headline);
  if(score.label)parent.append(node('p',score.label,'score-label-text'));
  const confidence=confidenceNames[score.confidence]||'未知';
  parent.append(node('p','证据把握：'+confidence+'。描述证据覆盖，不是统计置信度。','confidence'));
  if(unknown.length)parent.append(node('p','未知维度：'+unknown.join('、')+'。总分中暂按 2.5 占位，不代表已有中等需求。','unknown-note'));
  if(score.reason&&parent.id!=='score-summary')parent.append(node('p',score.reason,'score-explanation'));
}
function labeledText(parent,label,text){
  const p=node('p');p.append(node('strong',label+'：'),document.createTextNode(text||'尚未明确'));
  parent.append(p);
}
function tableWrap(headers,rows,label,cls='',rowSources=[]){
  const wrap=node('div',undefined,'table-scroll '+cls);wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',label);
  const table=node('table'),thead=node('thead'),head=node('tr');
  for(const text of headers){const th=node('th',text);th.scope='col';head.append(th);}thead.append(head);
  const tbody=node('tbody');
  rows.forEach((values,rowIndex)=>{const row=node('tr');values.forEach((value,i)=>{const cell=node(i===0&&cls==='direction-comparison'?'th':'td',String(value));if(cell.tagName==='TH')cell.scope='row';if(i===values.length-1)refs(cell,rowSources[rowIndex]||[],true);row.append(cell);});tbody.append(row);});
  if(!rows.length){const row=node('tr'),cell=node('td','本轮尚未取得可核验记录。','empty');cell.colSpan=headers.length;row.append(cell);tbody.append(row);}
  table.append(thead,tbody);wrap.append(table);return wrap;
}

$('#evidence-filter').setAttribute('aria-label','证据类型');
$('#competitor-filter').setAttribute('aria-label','范围');
$('#title').textContent=data.title;$('#idea').textContent=data.idea;$('#scope').textContent=data.scope;$('#date').textContent='研究日期 '+data.date;
$('#fixture').hidden=!data.fixture;$('#coverage-label').textContent=data.status==='complete'?'本轮研究完成':'覆盖尚不完整';
const verdictText=(isV2?{go:'建议继续验证',conditional:'先验证，再决定是否投入',no_go:'不建议按原方案入场'}:{go:'行',conditional:'有条件行',no_go:'不行'})[data.conclusion.verdict];
$('#verdict').textContent=verdictText;
$('#conclusion').textContent=data.conclusion.summary;
for(const reason of (data.conclusion.reasons||[]).slice(0,isV2?3:undefined))$('#reasons').append(node('li',reason));
scoreSummary($('#score-summary'),data.computed_score,data.scorecard);
if(isV2&&data.decision){
  const target=$('#decision-summary');target.hidden=false;
  labeledText(target,'推荐方向',data.decision.recommendation);
  labeledText(target,'MVP 主攻点',data.decision.mvp_focus);
  labeledText(target,'主要风险',data.decision.main_risk);
  labeledText(target,'先验证什么',data.decision.next_step);
  refs(target,data.decision.source_ids,true);
}
addToc('overview','研究概览');
if(isV2&&directions.length){
  $('#directions-section').hidden=false;
  const candidates=[{name:'原始 idea',stance:verdictText,score:data.computed_score,scorecard:data.scorecard},...directions.map(direction=>({...direction,stance:stanceNames[direction.stance]||direction.stance,score:directionScores.get(direction.id)}))];
  const headers=['比较维度',...candidates.map(candidate=>candidate.name)];
  const rows=[['方向建议',...candidates.map(candidate=>candidate.stance)],['综合判断',...candidates.map(candidate=>{const score=candidate.score;if(!score)return '尚未生成评分';return (score.value===null?'未评分':Number(score.value).toFixed(1)+' / 5')+(score.provisional||unknownDimensions(score,candidate.scorecard).length?' · 暂定':'')+(score.label?' · '+score.label:'');})],['证据把握',...candidates.map(candidate=>confidenceNames[candidate.score?.confidence]||'未知')]];
  for(const [dimension,title]of Object.entries(dimensionNames))rows.push([title+' · '+weights[dimension]+'%',...candidates.map(candidate=>{const row=(candidate.scorecard||[]).find(row=>row.dimension===dimension);return !row||row.value===null?'未知':row.value+' / 5 · '+(certaintyNames[row.certainty]||'未知');})]);
  $('#directions').append(node('p','各维均为高分更有利；未知项保持未知。缩小范围能降低验证与投入成本，市场需求仍需独立证据。','help'),tableWrap(headers,rows,'方向的同维度评分比较','direction-comparison'));
  for(const direction of directions){
    const article=node('article',undefined,'direction-item');
    const heading=node('h3',direction.name);heading.append(node('span',stanceNames[direction.stance]||direction.stance,'state'));article.append(heading);
    labeledText(article,'优先服务',direction.target_user);labeledText(article,'与原想法相比',direction.change);
    labeledText(article,'MVP 主攻点',direction.mvp_focus);labeledText(article,'推荐理由',direction.why);
    labeledText(article,'第一个验证',direction.first_test);labeledText(article,'主要风险',direction.main_risk);
    const unknown=unknownDimensions(directionScores.get(direction.id),direction.scorecard);
    if(unknown.length)article.append(node('p','暂定：'+unknown.join('、')+'仍未知，总分中仅按中性 2.5 占位。','unknown-note'));
    refs(article,direction.source_ids);$('#directions').append(article);
  }
  addToc('directions-section','方向建议与 MVP');
}
if(isV2&&!directions.length&&data.no_directions_reason){
  $('#decision-summary').append(node('p',data.no_directions_reason,'unknown-note'));
}

for(const s of data.sections||[]){
  const section=node('section',undefined,'section');section.id=s.id;
  const head=node('div',undefined,'section-head'),heading=node('h2',s.title);heading.append(node('span',status[s.status]||s.status,'state'));head.append(heading);
  section.append(head,node('p',s.summary,'section-summary'));refs(section,s.source_ids);
  for(const block of s.blocks||[]){
    let target=section;
    if(block.collapsed){const details=node('details',undefined,'research-detail'),summary=node('summary');summary.append(node('h3',block.title));details.append(summary);section.append(details);target=details;}
    else if(block.title)target.append(node('h3',block.title));
    if(block.type==='paragraph')target.append(node('p',block.text||''));
    if(block.type==='list'){const list=node('ul');for(const text of block.items||[])list.append(node('li',text));target.append(list);}
    if(block.type==='table')target.append(node('div','宽表可左右滑动查看','table-note'),tableWrap(block.headers,block.rows||[],block.title||s.title+'表格','',block.row_source_ids||[]));
    refs(target,block.source_ids);
  }
  $('#sections').append(section);addToc(s.id,s.title);
}
const competitionChapter=(data.sections||[]).some(s=>s.id==='competition')?document.getElementById('competition'):null;
if(isV2&&competitionChapter){
  const section=$('#competitor-section');section.classList.add('embedded-section');
  const heading=node('h3','竞品与替代完整清单');heading.id='competitor-heading';$('#competitor-heading').replaceWith(heading);
  competitionChapter.append(section);
}else addToc('competitor-section','竞品清单');
$('#competitor-total').textContent='本轮纳入 '+competitors.length+' 项';
for(const c of competitors){
  const item=node('article',undefined,'competitor-item');item.dataset.kind=c.kind;
  item.append(node(isV2?'h4':'h3',c.name),node('p',{direct:'直接竞品',indirect:'间接替代',manual:'人工办法'}[c.kind],'help'),node('p',c.summary||''),node('p','收费：'+(c.pricing||'未核实')),node('p','研究边界：'+(c.limitation||'未说明')));
  refs(item,c.source_ids);$('#competitor-list').append(item);
}
if(!competitors.length)$('#competitor-list').append(node('p','本轮尚未取得可核验的竞品清单。','empty'));
$('#competitor-filter').onchange=()=>document.querySelectorAll('.competitor-item').forEach(item=>item.hidden=$('#competitor-filter').value!=='all'&&item.dataset.kind!==$('#competitor-filter').value);

const marketChapter=(data.sections||[]).some(s=>s.id==='market')?document.getElementById('market'):null;
if(marketChapter)marketChapter.after($('#trends-section'));
addToc('trends-section','搜索兴趣走势');
const NS='http://www.w3.org/2000/svg';
function svg(tag,attrs,text){const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;}
if(!(data.trends||[]).length)$('#trends').append(node('p','尚未取得原始时间序列，因此不显示趋势线。缺数据不等于没有需求。','empty'));
for(const trend of data.trends||[]){
  const box=node('div',undefined,'chart'),points=trend.points||[];
  box.dataset.window=trend.window;
  box.append(node('h3',trend.keyword+' · '+trend.window),node('p',[trend.geo,trend.group,trend.category,trend.search_type,trend.granularity].filter(Boolean).join(' / ')));
  box.append(node('p','本次序列 '+points.length+' 个点；空心点为未完成周期，不参与连线；缺失值不补零。','help'));
  if(points.length){
    const chart=svg('svg',{viewBox:'0 0 720 260',role:'img','aria-label':trend.keyword+'相对搜索兴趣'});
    chart.append(svg('desc',{},trend.geo+'，'+trend.window+'。空心点为未完成周期；缺失值不补零。'));
    const x=i=>45+i/Math.max(points.length-1,1)*640,y=value=>215-value*1.8;
    for(const value of[0,25,50,75,100])chart.append(svg('line',{x1:45,x2:685,y1:y(value),y2:y(value),stroke:'#dce1e7'}),svg('text',{x:34,y:y(value)+4,'text-anchor':'end',fill:'#526171','font-size':11},value));
    let path='',active=false;const dots=[];
    points.forEach((point,i)=>{
      if(point.value===null){active=false;return;}
      if(point.partial)active=false;else{path+=(active?'L':'M')+x(i)+','+y(point.value)+' ';active=true;}
      const dot=svg('circle',{cx:x(i),cy:y(point.value),r:3,fill:point.partial?'#fff':'#2257a0',stroke:'#2257a0',tabindex:0});
      dot.append(svg('title',{},point.date+'：'+point.value+(point.partial?'（未完成周期）':'')));dots.push(dot);
    });
    chart.append(svg('path',{d:path,fill:'none',stroke:'#2257a0','stroke-width':2}),...dots);
    for(const i of new Set([0,Math.floor((points.length-1)/2),points.length-1]))chart.append(svg('text',{x:x(i),y:242,'text-anchor':'middle',fill:'#526171','font-size':10},points[i].date));
    box.append(chart);
  }
  box.append(node('p',trend.reason));refs(box,trend.source_ids);$('#trends').append(box);
}
function filterTrendWindow(){
  const selected=$('#trends-window').value,charts=[...document.querySelectorAll('#trends .chart')];
  for(const chart of charts)chart.hidden=chart.dataset.window!==selected;
  $('#trends-total').textContent='显示 '+charts.filter(chart=>!chart.hidden).length+' / '+charts.length+' 条序列；切换窗口查看其余数据。';
}
if(isV2&&(data.trends||[]).length){
  const windows=[...new Set(data.trends.map(trend=>trend.window))],select=$('#trends-window');
  for(const window of windows){const option=node('option',window);option.value=window;select.append(option);}
  select.value=windows.find(window=>window.replace(/\s/g,'')==='过去30天')||windows[0];
  $('#trends-controls').hidden=false;select.onchange=filterTrendWindow;filterTrendWindow();
}

addToc('evidence-section','证据清单');
const typeNames={A:'市场',B:'行为',C:'相邻变化',D:'原话',E:'推断'};
for(const [type,label]of Object.entries(typeNames)){const count=node('div',undefined,'count');count.append(node('b',evidence.filter(e=>e.type===type).length),node('span',type+' '+label));$('#evidence-counts').append(count);}
for(const e of evidence){
  const item=node('article',undefined,'evidence-item');item.dataset.type=e.type;
  const top=node('div',undefined,'evidence-top');top.append(node('span',e.id+' / '+e.type+'类'),node('span',states[e.state]||e.state,'tag'));
  item.append(top,node('p',e.claim));if(e.quote)item.append(node('blockquote',e.quote));if(e.limitation)item.append(node('p',e.limitation,'help'));
  refs(item,e.source_ids);$('#evidence-list').append(item);
}
if(!evidence.length)$('#evidence-list').append(node('p','本轮尚未取得证据条目，不能据此判断没有需求。','empty'));
function filterEvidence(){const value=$('#evidence-filter').value;let count=0;document.querySelectorAll('.evidence-item').forEach(item=>{item.hidden=value!=='all'&&item.dataset.type!==value;if(!item.hidden)count++;});$('#evidence-total').textContent='显示 '+count+' 条';}
$('#evidence-filter').onchange=filterEvidence;filterEvidence();

addToc('score-section','评分依据');
$('#score-help').textContent=isV2?'六维均为高分更有利。未知项以 2.5 临时占位，原始维度仍为未知；证据把握按直接证据、有限推断和未知分别加权，不是成功概率。':'本报告沿用 v1 的七维评分与原有星级规则，没有用新版权重重新解释旧分数。';
function scoreRows(parent,rows){
  for(const rowData of rows||[]){
    const row=node('div',undefined,'score-row'),track=node('div',undefined,'score-track'),fill=node('i');
    fill.style.width=rowData.value===null?'0':rowData.value/5*100+'%';track.append(fill);
    const title=(dimensionNames[rowData.dimension]||rowData.dimension)+(isV2?' · '+weights[rowData.dimension]+'%':'');
    row.append(node('span',title),track,node('span',rowData.value===null?'未知':rowData.value+' / 5'));
    const reason=node('div',undefined,'score-reason');
    if(isV2)reason.append(node('span',certaintyNames[rowData.certainty]||'未知','certainty'));
    reason.append(document.createTextNode(rowData.reason||''));refs(reason,rowData.source_ids);parent.append(row,reason);
  }
}
if(isV2){$('#score-list').append(node('h3','原始 idea'));scoreSummary($('#score-list'),data.computed_score,data.scorecard,true);}
scoreRows($('#score-list'),data.scorecard);
if(isV2)for(const direction of directions){
  const group=node('div',undefined,'direction-score');group.append(node('h3',direction.name));
  scoreSummary(group,directionScores.get(direction.id),direction.scorecard,true);scoreRows(group,direction.scorecard);$('#score-list').append(group);
}
addToc('glossary-section','名词解释');
for(const g of data.glossary||[]){const item=node('details');item.append(node('summary',g.term),node('p',g.meaning));$('#glossary').append(item);}
if(!(data.glossary||[]).length)$('#glossary').append(node('p','本报告没有需要额外解释的术语。','empty'));
addToc('sources-section','来源');
for(const source of sources){
  const item=node('div',undefined,'source');item.id='source-'+source.id;
  item.append(safeLink(source.id+' · '+source.title,source.url),node('p',(source.status==='verified'?'已查阅':'未核实线索')+'；访问时间 '+source.accessed_at+(source.published_at?'；发布时间 '+source.published_at:'')));$('#sources').append(item);
}
if(!sources.length)$('#sources').append(node('p','本轮尚未记录来源。','empty'));

const tocGroups=isV2?[
  {title:'研究概览',ids:['overview','directions-section']},
  {title:'研究正文',ids:['signals','market','trends-section','competition','environment','validation','limitations']},
  {title:'研究附录',ids:['evidence-section','score-section','glossary-section','sources-section']}
]:[
  {title:'研究概览',ids:['overview','decomposition']},
  {title:'需求与市场',ids:['demand','jobs','market','trends-section','environment','competition']},
  {title:'产品与商业',ids:['segments','business','risks']},
  {title:'结论与方向',ids:['decision','alternatives','discarded']},
  {title:'研究资料',ids:['limitations','evidence-section','competitor-section','score-section','glossary-section','sources-section']}
];
const assignedIds=new Set(tocGroups.flatMap(group=>group.ids));
tocGroups.at(-1).ids.push(...tocEntries.filter(entry=>!assignedIds.has(entry.id)).map(entry=>entry.id));
const tocLinks=new Map();
function tocLink(id,title,item,group,list,mobileGroup,isSubsection=false){
  const anchor=node('a',title,isSubsection?'toc-subsection-link':'toc-section-link');anchor.href='#'+id;
  const li=isSubsection?node('li'):item;li.append(anchor);list.append(li);
  const option=node('option',(isSubsection?'　　':'')+title);option.value=id;mobileGroup.append(option);
  tocLinks.set(id,{anchor,item,group});
}
for(const spec of tocGroups){
  const entries=spec.ids.map(id=>tocEntries.find(entry=>entry.id===id)).filter(Boolean);if(!entries.length)continue;
  const group=node('details',undefined,'toc-group');group.append(node('summary',spec.title));
  const list=node('ul',undefined,'toc-section-list'),mobileGroup=node('optgroup');mobileGroup.label=spec.title;
  for(const entry of entries){
    const item=node('li',undefined,'toc-item');tocLink(entry.id,entry.title,item,group,list,mobileGroup);
    const subsections=node('ul',undefined,'toc-subsections');
    document.getElementById(entry.id).querySelectorAll('h3').forEach((heading,index)=>{
      if(!heading.id)heading.id=entry.id+'-detail-'+(index+1);
      const title=heading.cloneNode(true);title.querySelectorAll('.state').forEach(state=>state.remove());
      tocLink(heading.id,title.textContent,item,group,subsections,mobileGroup,true);
    });
    if(subsections.childElementCount)item.append(subsections);
  }
  group.append(list);$('#toc').append(group);$('#mobile-toc').append(mobileGroup);
}
let currentTocId;
function setActiveToc(id){
  const current=tocLinks.get(id);if(!current||currentTocId===id)return;
  for(const {anchor,item,group}of tocLinks.values()){anchor.classList.remove('active');anchor.removeAttribute('aria-current');item.classList.remove('is-current');group.classList.remove('is-current');}
  current.anchor.classList.add('active');current.anchor.setAttribute('aria-current','location');current.item.classList.add('is-current');current.group.classList.add('is-current');current.group.open=true;
  $('#mobile-toc').value=id;currentTocId=id;
}
function revealTarget(id){
  const target=document.getElementById(id);if(!target)return null;
  const chart=target.closest('#trends .chart');
  if(isV2&&chart){$('#trends-window').value=chart.dataset.window;filterTrendWindow();}
  for(let ancestor=target;ancestor;ancestor=ancestor.parentElement)if(ancestor.tagName==='DETAILS')ancestor.open=true;
  return target;
}
function navigateTo(id){const target=revealTarget(id);if(!target)return;setActiveToc(id);requestAnimationFrame(()=>target.scrollIntoView());}
const tocTargets=[...tocLinks.keys()].map(id=>document.getElementById(id)).filter(Boolean).sort((a,b)=>a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING?-1:1);
function updateActiveToc(){let current=tocTargets[0];for(const target of tocTargets){if(!target.getClientRects().length)continue;if(target.getBoundingClientRect().top<=110)current=target;else break;}if(current)setActiveToc(current.id);}
let scrollPending=false;
addEventListener('scroll',()=>{if(scrollPending)return;scrollPending=true;requestAnimationFrame(()=>{updateActiveToc();scrollPending=false;});},{passive:true});
$('#mobile-toc').onchange=event=>{const id=event.target.value;history.replaceState(null,'','#'+id);navigateTo(id);};
$('#toc').addEventListener('click',event=>{const anchor=event.target.closest('a');if(!anchor)return;event.preventDefault();const id=anchor.hash.slice(1);history.replaceState(null,'','#'+id);navigateTo(id);});
addEventListener('hashchange',()=>navigateTo(location.hash.slice(1)));
if(location.hash)navigateTo(location.hash.slice(1));else{setActiveToc('overview');requestAnimationFrame(updateActiveToc);}

function download(name,content,type){const url=URL.createObjectURL(new Blob([content],{type})),anchor=node('a');anchor.href=url;anchor.download=name;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('#download-md').onclick=()=>download('research.md',data.markdown,'text/markdown;charset=utf-8');
$('#download-zip').onclick=()=>download('research.zip',Uint8Array.from(atob(data.zip_base64),c=>c.charCodeAt(0)),'application/zip');
const printState=[];
addEventListener('beforeprint',()=>{printState.length=0;document.querySelectorAll('main details').forEach(detail=>{printState.push([detail,detail.open]);detail.open=true;});});
addEventListener('afterprint',()=>{for(const[detail,open]of printState)detail.open=open;});
$('#print').onclick=()=>window.print();
