"""Exercise the current contract on a frozen build. External forms are never submitted."""
import functools, hashlib, http.server, json, os, pathlib, subprocess, threading
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
baseline,baseline_url=serve(ROOT/'tmp/baseline47/dist')
gallery,gallery_url=serve(ROOT/'artifacts/preloader-options')
before=hashes(); results=[]
env={**os.environ,'QA_URL':url,'SWIPE_TEST_URL':url,'QA_BASELINE_URL':baseline_url,'QA_GALLERY_URL':gallery_url,'QA_REPORT_PREFIX':'iteration48','SWIPE_TEST_REPORT':'tmp/planning/iteration48-swipes.json'}
commands=[['node',f'tests/{name}.mjs'] for name in ['iteration48-ui','iteration46-editorial','iteration39-layout','iteration39-journeys','iteration45-ui','iteration46-startup','iteration44-motion','iteration45-dock-motion','iteration37-swipes','iteration47-loading','iteration48-desktop']]
try:
    for command in commands:
        name=pathlib.Path(command[1]).stem
        print('RUN '+name,flush=True)
        result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        (ROOT/f'tmp/planning/iteration48/{name}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        results.append({'command':command,'exit':result.returncode})
        print('\n'.join((result.stdout+result.stderr).splitlines()[-6:]),flush=True)
        if result.returncode:raise SystemExit(result.returncode)
    if hashes()!=before:raise SystemExit('Built artifact changed during verification')
finally:
    (ROOT/'tmp/planning/iteration48-verification.json').write_text(json.dumps({'commands':results,'artifactUnchanged':hashes()==before,'indexSha256':before['index.html'],'published':False},indent=2),encoding='utf-8')
    for server in [site,baseline,gallery]:server.shutdown();server.server_close()
