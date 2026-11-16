"""Shared loader, gallery controls and existing responsive journeys on one frozen build."""
import functools,hashlib,http.server,json,os,pathlib,subprocess,threading
root=pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
def serve(directory):
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(directory)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_address[1]}/'
def hashes():
    return {str(p.relative_to(root/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'dist').rglob('*') if p.is_file()}
site,url=serve(root/'dist');gallery,gallery_url=serve(root/'artifacts/preloader-options');before=hashes();results=[]
env={**os.environ,'QA_URL':url,'SWIPE_TEST_URL':url,'QA_GALLERY_URL':gallery_url,'QA_REPORT_PREFIX':'iteration47','SWIPE_TEST_REPORT':'tmp/planning/iteration47-swipes.json','QA_BASELINE':'tmp/baseline47/dist','QA_DESKTOP_HOME_ONLY':'1'}
commands=[['node','tests/iteration47-loading.mjs'],['node','tests/iteration47-gallery.mjs'],['node','tests/iteration46-startup.mjs'],['node','tests/iteration46-editorial.mjs'],['node','tests/iteration45-ui.mjs'],['node','tests/iteration39-layout.mjs'],['node','tests/iteration39-journeys.mjs'],['node','tests/iteration37-swipes.mjs'],['python','tests/iteration39-desktop.py']]
try:
    for command in commands:
        result=subprocess.run(command,cwd=root,env=env,timeout=600)
        results.append({'command':command,'exit':result.returncode})
        if result.returncode:raise SystemExit(result.returncode)
    if hashes()!=before:raise SystemExit('Built artifact changed during verification')
finally:
    (root/'tmp/planning/iteration47-verification.json').write_text(json.dumps({'commands':results,'artifactUnchanged':hashes()==before,'indexSha256':before['index.html'],'published':False},indent=2),encoding='utf-8')
    site.shutdown();site.server_close();gallery.shutdown();gallery.server_close()
