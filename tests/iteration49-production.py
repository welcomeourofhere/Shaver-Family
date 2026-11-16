"""Exercise the current contract on a frozen build. External forms are never submitted."""
import argparse, functools, hashlib, http.server, json, os, pathlib, subprocess, threading
ROOT = pathlib.Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def copyfile(self, source, output):
        try: super().copyfile(source, output)
        except (ConnectionResetError, BrokenPipeError): pass
def serve(directory):
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(directory)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_address[1]}/'
def hashes():
    return {str(p.relative_to(ROOT/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'dist').rglob('*') if p.is_file()}
site,url=serve(ROOT/'dist')
baseline,baseline_url=serve(ROOT/'tmp/baseline48/dist')
gallery,gallery_url=serve(ROOT/'artifacts/preloader-options')
before=hashes(); results=[]
env={**os.environ,'QA_BROWSER_SESSION':'soyuz49-touch','QA_BROWSER_SOCKET_DIR':str(ROOT/'.local/browser-qa49'),'QA_URL':url,'SWIPE_TEST_URL':url,'QA_BASELINE_URL':baseline_url,'QA_GALLERY_URL':gallery_url,'QA_REPORT_PREFIX':'iteration49','SWIPE_TEST_REPORT':'tmp/planning/iteration49-swipes.json'}
commands=[['node',f'tests/{name}.mjs'] for name in ['iteration49-ui','iteration49-stress','iteration46-editorial','iteration39-layout','iteration39-journeys','iteration45-ui','iteration46-startup','iteration44-motion','iteration45-dock-motion','iteration37-swipes','iteration47-loading','iteration49-desktop']]
parser=argparse.ArgumentParser()
parser.add_argument('--resume-from',choices=[pathlib.Path(command[1]).stem for command in commands])
args=parser.parse_args()
if args.resume_from:
    previous_path=ROOT/'tmp/planning/iteration49-verification.json'
    previous=json.loads(previous_path.read_text(encoding='utf-8'))
    assert previous['artifactUnchanged'] and previous['indexSha256']==before['index.html'],'Rebuild requires a full new run'
    start=next(i for i,command in enumerate(commands) if pathlib.Path(command[1]).stem==args.resume_from)
    results=previous['commands'][:start]
    assert len(results)==start and all(result['exit']==0 and result['command']==commands[i] for i,result in enumerate(results))
    previous_path.with_name('iteration49-verification-before-resume.json').write_bytes(previous_path.read_bytes())
    log=ROOT/f'tmp/planning/iteration49/{args.resume_from}.log'
    if log.exists():log.with_name(log.stem+'-before-resume.log').write_bytes(log.read_bytes())
    commands=commands[start:]
try:
    for command in commands:
        name=pathlib.Path(command[1]).stem
        print('RUN '+name,flush=True)
        result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        (ROOT/f'tmp/planning/iteration49/{name}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        results.append({'command':command,'exit':result.returncode})
        print('\n'.join((result.stdout+result.stderr).splitlines()[-6:]),flush=True)
        if result.returncode:raise SystemExit(result.returncode)
    if hashes()!=before:raise SystemExit('Built artifact changed during verification')
finally:
    (ROOT/'tmp/planning/iteration49-verification.json').write_text(json.dumps({'commands':results,'artifactUnchanged':hashes()==before,'indexSha256':before['index.html'],'artifactSha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'resumedFrom':args.resume_from,'published':False},indent=2),encoding='utf-8')
    for server in [site,baseline,gallery]:server.shutdown();server.server_close()
