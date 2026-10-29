"""Synthetic v2 reading specimen. No network or claims about a real market."""
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / 'skills/product-idea-research/scripts'))
from report import initial, render

root = repo / 'examples/reading-demo'
root.mkdir(exist_ok=True)
d = initial('出发前，少漏带一件东西', '根据行程、活动和同行人，帮助美国用户准备行李。', 'v3')
d.update(date='2026-10-28', fixture=True)
d['conclusion'].update(summary='这是展示阅读与下载的合成样例，未进行真实市场研究。先比较临出发的真实任务，再决定要不要做新工具。', reasons=['现有清单可能已足够。','需要查清谁会因协作或装备遗漏受影响。','所有分项未知；2.5占位暂分不代表有中等机会。'])
d['decision'].update(recommendation='先研究，不推荐据此开发。', mvp_focus='假设切口：同行人的关键物品交接。尚未证明比共享备忘录更好。', main_risk='需求、热度、竞品缺口和付费均未核实。', next_step='让用户回顾最近一次出行并演示旧清单，观察遗漏与协调代价，不只问是否喜欢这个想法。')
summaries = {
 'signals':'未取得近期社交讨论和真实行为；不能声称话题很火。',
 'market':'可服务人群与市场走势未知，不用旅行总人数代替这个细分市场。',
 'competition':'未检索；研究时清单直接放在这里，并核对现有产品是否已解决。',
 'environment':'平台和数据约束待查；只研究会改变入场判断的内容。',
 'validation':'先观察现有准备过程，再用同一份真实行程做轻量对照。',
 'limitations':'阅读样例，非真实市场调研。没有访谈、竞品实测、付款和趋势采集。'
}
for s in d['sections']:
 s.update(status='partial',summary=summaries[s['id']],blocks=[dict(type='paragraph',text=summaries[s['id']],source_ids=[])])
d['directions'][0].update(id='shared-packing',name='同行人的物品交接（待研究）',target_user='一起旅行、分工打包的人，情境待核实。',change='假设从个人清单缩小到同行协作，不代表市场更好。',mvp_focus='只验证关键物品由谁准备、是否已经带上。',why='假设协调可能比清单生成更有代价；目前没有证据。',first_test='观察一次真实交接，与共享备忘录比较。',main_risk='现有共享清单可能完全足够。')
d['glossary']=[dict(term='暂定分',meaning='未知项临时按2.5占位，不代表机会已得到验证。')]
(root/'research.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(render(root))
