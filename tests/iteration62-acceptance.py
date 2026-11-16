"""Collect owner corrections and whole-site evidence for one frozen local build."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
subprocess.run([sys.executable,'-X','utf8','tests/device-acceptance.py','--phase','62'],cwd=ROOT,check=True)
out=ROOT/'tmp/planning/iteration62'
read=lambda path:json.loads((ROOT/path).read_text(encoding='utf-8'))
summary=read('tmp/planning/iteration62/acceptance-summary.json')
sha=reg.digest(ROOT/'dist');sources=reg.sources()

for path in ['targeted/verification.json','owner-corrections.json','additions.json','interviews.json','news-attention.json']:
    evidence=read('tmp/planning/iteration62/'+path)
    assert evidence['before']==evidence['after']==sha and evidence['unchanged']
    assert evidence['sourcesUnchanged'] and evidence['sourceDigests']==sources
    if 'commands'in evidence:
        assert len(evidence['commands'])==7 and all(row['exitCode']==0 for row in evidence['commands'])
    elif path=='owner-corrections.json':
        cases=evidence['cases']
        assert len(cases)==131
        assert {row['engine']for row in cases}=={'chromium','firefox','webkit'}
        assert sum('ticketWidth'in row for row in cases)==108
        assert sum(row.get('nativeReaderTouch',False)for row in cases)==2
    elif path=='additions.json':
        assert len(evidence['cases'])==48 and evidence['providerFixture'] and not evidence['purchaseSubmitted']
    elif path=='interviews.json':
        assert len(evidence['cases'])==72 and not evidence['bookingSubmitted']
    else:
        assert len(evidence['cases'])==9

masters=read('artifacts/iteration62/masters.json');interruptions=read('artifacts/iteration62/interruptions.json')
for evidence,key,count in [(masters,'buildHash',9),(interruptions,'hash',18)]:
    assert evidence[key]==sha and evidence['unchanged'] and evidence['sourcesUnchanged']
    assert len(evidence['rows'])==count
assert all(row['freshClickAfterOutsideRelease']for row in interruptions['rows']if 'delayedCancelledRelease'in row)

maps=read('tmp/planning/iteration62/map-performance.json')
assert maps['buildHashes']['candidate']==sha and maps['unchanged'] and len(maps['rows'])==8
assert maps['buildHashes']['baseline']==reg.digest(ROOT/'tmp/baseline62/dist')
for row in maps['rows']:
    assert row['geometryBefore']==row['geometryAfter']
    if row['label']=='candidate':
        assert row['contactTransform']=='none' and row['mapRequests'][0]['time']>=row['lastScroll']+120

summary.update(targetedCommands=7,ownerCorrectionCases=131,fairPriceEngineThemeTextCases=108,
               latestOwnerAdditionCases=48,newInterviewCases=72,newInterviewQuestions=71,newInterviewPhotos=63,newsAttentionCases=9,
               nativeReaderBoundaryTouchCases=2,masterEngineViewports=9,masterKeyboardLabelCases=54,
               masterDockCases=36,railKeyboardCases=15,interruptionEngineCases=3,mapApproachSamples=8,
               mapConditions=maps['conditions'])
(out/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS iteration62 focused and whole-site evidence share build '+sha)
