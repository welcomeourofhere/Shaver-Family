"""Verify the current build in three engines and keep older evidence untouched."""
import importlib.util
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--phase',type=int,default=60);phase=parser.parse_args().phase
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
regression=importlib.util.module_from_spec(spec);spec.loader.exec_module(regression)
out=ROOT/f'tmp/planning/iteration{phase}/targeted';out.mkdir(parents=True,exist_ok=True)
server,url=regression.serve(ROOT/'dist')
before=regression.digest(ROOT/'dist');source_before=regression.sources();results=[]
temporary=ROOT/'tests/.iteration60-prior.py';assert not temporary.exists()
try:
    # Mouse pointer IDs are assigned by each engine; historical 59 assumed Chromium's 1.
    source=(ROOT/'tests/iteration59-browser.py').read_text(encoding='utf-8')
    source=source.replace("artifacts/iteration59",f"artifacts/iteration{phase}/prior")
    source=source.replace("page.goto(","page.add_init_script(\"document.addEventListener('pointerdown',e=>window.__qaMouseId=e.pointerId,true)\");page.goto(",1)
    source=source.replace("dispatch_event('pointercancel',{'pointerId':1})","dispatch_event('pointercancel',{'pointerId':page.evaluate('window.__qaMouseId')})")
    temporary.write_text(source,encoding='utf-8')
    for engine in ['chromium','firefox','webkit']:
        for name,path in [('interactions','tests/iteration60-browser.py'),('previous','.iteration60-prior.py')]:
            command=[sys.executable,'-X','utf8',str(temporary) if name=='previous' else path]
            run=subprocess.run(command,cwd=ROOT,env={**os.environ,'QA_ENGINE':engine,'QA_URL':url,'QA_ARTIFACT_ROOT':f'artifacts/iteration{phase}'},capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
            (out/f'{engine}-{name}.log').write_text(run.stdout+run.stderr,encoding='utf-8')
            results.append({'engine':engine,'suite':name,'exitCode':run.returncode})
            print(engine,name,run.stdout.strip(),flush=True)
            if run.returncode:raise RuntimeError(run.stderr)
    # The existing responsive suite writes only the current iteration's evidence.
    source=(ROOT/'tests/iteration59-responsive.py').read_text(encoding='utf-8').replace('artifacts/iteration59',f'artifacts/iteration{phase}')
    source=source.replace("size=hours.evaluate(","bounds=hours.evaluate(\"e=>{const r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);const t=range.getBoundingClientRect();return{top:t.top-r.top,bottom:r.bottom-t.bottom}}\");assert bounds['top']>=-1 and bounds['bottom']>=-1,bounds;size=hours.evaluate(")
    temporary.write_text(source,encoding='utf-8')
    run=subprocess.run([sys.executable,'-X','utf8',str(temporary)],cwd=ROOT,env={**os.environ,'QA_URL':url},capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
    (out/'responsive.log').write_text(run.stdout+run.stderr,encoding='utf-8');results.append({'suite':'responsive','exitCode':run.returncode});print(run.stdout.strip(),flush=True)
    if run.returncode:raise RuntimeError(run.stderr)
finally:
    temporary.unlink(missing_ok=True);server.shutdown();server.server_close()
    after=regression.digest(ROOT/'dist');source_after=regression.sources()
    (out/'verification.json').write_text(json.dumps({'before':before,'after':after,'sourceDigests':source_before,'unchanged':before==after,'sourcesUnchanged':source_before==source_after,'commands':results,'published':False},indent=2),encoding='utf-8')
assert before==after and source_before==source_after and len(results)==7 and all(row['exitCode']==0 for row in results)
