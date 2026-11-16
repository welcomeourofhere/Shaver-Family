"""Join whole-site and focused evidence only when they describe the same build."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
subprocess.run([sys.executable,'-X','utf8','tests/device-acceptance.py','--phase','61'],cwd=ROOT,check=True)
out=ROOT/'tmp/planning/iteration61'
read=lambda path:json.loads((ROOT/path).read_text(encoding='utf-8'))
summary=read('tmp/planning/iteration61/acceptance-summary.json')
sha=reg.digest(ROOT/'dist');sources=reg.sources()
targeted=read('tmp/planning/iteration61/targeted/verification.json')
assert targeted['before']==targeted['after']==sha and targeted['unchanged']
assert targeted['sourcesUnchanged'] and targeted['sourceDigests']==sources
assert len(targeted['commands'])==7 and all(row['exitCode']==0 for row in targeted['commands'])
masters=read('artifacts/iteration61/masters.json');interruptions=read('artifacts/iteration61/interruptions.json')
for evidence,key,count in [(masters,'buildHash',9),(interruptions,'hash',18)]:
    assert evidence[key]==sha and evidence['unchanged'] and evidence['sourcesUnchanged']
    assert len(evidence['rows'])==count
assert all(row['freshClickAfterOutsideRelease']for row in interruptions['rows']if 'delayedCancelledRelease'in row)
offers=read('artifacts/iteration61/offer-performance.json')
assert offers['hashes']['candidate']==sha and offers['unchanged'] and len(offers['rows'])==6
for run in range(1,4):
    baseline=next(row for row in offers['rows']if row['label']=='baseline'and row['run']==run)
    candidate=next(row for row in offers['rows']if row['label']=='candidate'and row['run']==run)
    assert baseline['poses']==candidate['poses']
    assert baseline['rootReads']>1000 and candidate['rootReads']<20
summary.update(targetedCommands=7,masterEngineViewports=9,masterKeyboardLabelCases=54,
               masterDockCases=36,railKeyboardCases=15,interruptionEngineCases=3,
               offerPerformanceSamples=6,offerHeldPosesUnchanged=True)
(out/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS iteration61 focused and whole-site evidence share build '+sha)
