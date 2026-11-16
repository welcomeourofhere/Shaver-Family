"""Verify mobile copy, service dragging, About and dock on a frozen local build."""
import functools,hashlib,http.server,json,os,pathlib,subprocess,threading
root=pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def hashes():return{str(p.relative_to(root/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'dist').rglob('*') if p.is_file()}
before=hashes();server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_address[1]}/'
env={**os.environ,'QA_URL':url,'QA_REPORT_PREFIX':'iteration42','QA_BASELINE':'tmp/baseline42/dist','SWIPE_TEST_URL':url,'SWIPE_TEST_ONLY':'about','SWIPE_TEST_REPORT':'tmp/planning/iteration42-touch.json'};results=[]
commands=[(['node','tests/iteration42-mobile.mjs'],{}),(['node','tests/iteration39-layout.mjs'],{}),(['node','tests/iteration39-journeys.mjs'],{}),(['node','tests/iteration39-motion.mjs'],{'QA_MOTION_ONLY':'stack'}),(['node','tests/iteration37-swipes.mjs'],{}),(['python','tests/iteration39-desktop.py'],{})]
try:
 for command,extra in commands:
  result=subprocess.run(command,cwd=root,env={**env,**extra},timeout=240);results.append({'command':command,**extra,'exit':result.returncode});assert result.returncode==0,command
 assert before==hashes(),'Built artifact changed during verification'
finally:
 (root/'tmp/planning/iteration42-verification.json').write_text(json.dumps({'commands':results,'files':len(before),'artifactUnchanged':before==hashes(),'indexSha256':before['index.html'],'published':False},indent=2),encoding='utf8');server.shutdown();server.server_close()
