"""Compute explicit FCP-to-10s timespan TBT from saved public navigation probes."""
import argparse,json,statistics
from pathlib import Path

def blocking(tasks,fcp,end=10000):
 return sum(max(0,min(end,t['time']+t['duration'])-max(fcp,t['time']+50))for t in tasks)
assert blocking([{'time':100,'duration':51}],0)==1
assert blocking([{'time':0,'duration':100}],80)==20
assert blocking([{'time':9900,'duration':150}],0)==50
assert blocking([{'time':9990,'duration':70}],0)==0
p=argparse.ArgumentParser();p.add_argument('--before',required=True,type=Path);p.add_argument('--after',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
report={'definition':'sum(max(0,min(10000,taskEnd)-max(FCP,taskStart+50ms))); explicit FCP-to-10000ms timespan, not Lighthouse navigation/TTI TBT and not field INP','reference':'https://web.dev/articles/tbt','selfChecks':4,'series':[]}
for path in [a.before]+([a.after]if a.after else[]):
 raw=json.loads(path.read_text(encoding='utf-8'));rows=[];assert len(raw['rows'])==9
 for row in raw['rows']:
  assert not row.get('failure')and not row.get('traceFailure')and not row['ownErrors']
  assert row['state']['now']>=10000 and row['deliveryStubbed']is False
  fcp=next(v['time']for v in row['state']['paints']if v['name']=='first-contentful-paint');tasks=row['state']['probe']['long']
  rows.append({'profile':row['profile'],'run':row['run'],'browser':row['browser'],'fcpMs':fcp,'lcpMs':row['lcpMs'],'cls':row['cls'],'timespanTbtMs':blocking(tasks,fcp),'longTaskCount':len(tasks)})
 groups={r['profile']['name']for r in rows};assert len(groups)==3
 medians={name:{key:statistics.median(r[key]for r in rows if r['profile']['name']==name)for key in ['fcpMs','lcpMs','cls','timespanTbtMs']}for name in sorted(groups)}
 report['series'].append({'build':raw['build'],'source':str(path),'rows':rows,'medians':medians})
if len(report['series'])==2:
 before,after=report['series'];assert [(r['profile'],r['run'],r['browser'])for r in before['rows']]==[(r['profile'],r['run'],r['browser'])for r in after['rows']]
 report['matchedConditions']=True;report['delta']={name:{key:after['medians'][name][key]-before['medians'][name][key]for key in ['fcpMs','lcpMs','cls','timespanTbtMs']}for name in before['medians']}
a.output.parent.mkdir(parents=True,exist_ok=True);assert not a.output.exists();a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({s['build']:s['medians']for s in report['series']},ensure_ascii=False))
