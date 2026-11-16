"""Collect only completed, matching-build local evidence; never invent checks.
python -X utf8 tests/device-acceptance.py --phase 57
"""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=int,default=57);args=parser.parse_args();out=ROOT/f'tmp/planning/iteration{args.phase}'
    read=lambda name:json.loads((out/name).read_text(encoding='utf-8'))
    sha=reg.digest(ROOT/'dist');checks=read('regression/verification.json');engines=read('compatibility-accepted.json');legacy=read('legacy.json');load=read('performance.json');dock=read('dock-performance.json')
    assert checks['before']==checks['after']==sha and checks['unchanged'] and checks['sourcesUnchanged'] and checks['sourceDigests']==reg.sources()
    assert len(checks['commands'])==16 and all(row['exitCode']==0 for row in checks['commands'])
    for result,count in [(engines,60),(legacy,8)]:
        assert result['buildSha256']==sha and result['unchanged'] and len(result['cases'])==count and all(row['passed']for row in result['cases'])
    assert load['buildHashes']['candidate']==dock['hashes']['candidate']==sha and load['unchanged']and dock['unchanged']
    assert len(load['rows'])==18 and len(dock['rows'])==6
    assert all(not row['scriptErrors']for row in load['rows'])and all(not row['errors']for row in dock['rows'])
    baseline=reg.digest(ROOT/f'tmp/baseline{args.phase}/dist');assert load['buildHashes']['baseline']==dock['hashes']['baseline']==baseline
    unit=(out/'unit.log').read_text(encoding='utf-8');python=(out/'python.log').read_text(encoding='utf-8');astro=(out/'check.log').read_text(encoding='utf-8');build=(out/'build.log').read_text(encoding='utf-8')
    node_count=int(re.search(r'tests\s+(\d+)',unit)[1]);assert re.search(r'fail\s+0\b',unit)
    python_count=int(re.search(r'Ran (\d+) tests',python)[1]);assert re.search(r'^OK$',python,re.M)
    astro_count=int(re.search(r'Result \((\d+) files\)',astro)[1]);assert '0 errors'in astro and '0 warnings'in astro and 'build] Complete!'in build
    screenshots=[]
    for path in sorted((ROOT/f'artifacts/iteration{args.phase}').glob('*.png')):
        if (path.name.startswith('accepted-')or path.name.startswith('legacy-'))and'failure'not in path.name:
            screenshots.append({'file':str(path.relative_to(ROOT).as_posix()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    summary={'localAcceptance':'passed','localPhase':args.phase,'buildSha256':sha,'sourceDigests':checks['sourceDigests'],'nodeTests':node_count,'pythonTests':python_count,'astroFiles':astro_count,'pages':int(re.search(r'(\d+) page\(s\) built',build)[1]),'regressionSuites':len(checks['commands']),'regressionScenarios':sum(row['passedScenarios']for row in checks['commands']),'engineCases':len(engines['cases']),'legacyCases':len(legacy['cases']),'loadSamples':len(load['rows']),'dockSamples':len(dock['rows']),'screenshots':screenshots,'physicalDevices':False,'physicalDeviceTestingSkippedByUser':True,'fieldData':False,'published':False}
    (out/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({key:value for key,value in summary.items()if key not in ['screenshots','sourceDigests']},ensure_ascii=False))
if __name__=='__main__':main()
