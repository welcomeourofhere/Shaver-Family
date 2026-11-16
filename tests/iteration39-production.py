"""Exercise the frozen build over loopback; no publication or external form submission."""
import functools,hashlib,http.server,json,os,pathlib,subprocess,threading
root=pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def hashes():return{str(p.relative_to(root/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'dist').rglob('*') if p.is_file()}
before=hashes();server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_address[1]}/'
env={**os.environ,'QA_URL':url,'SWIPE_TEST_URL':url,'SWIPE_TEST_REPORT':'tmp/planning/iteration39-swipes.json'};results=[]
try:
 for command in [['node','tests/iteration39-layout.mjs'],['node','tests/iteration39-journeys.mjs'],['node','tests/iteration39-motion.mjs'],['node','tests/iteration37-swipes.mjs'],['python','tests/iteration39-artwork.py'],['python','tests/iteration39-desktop.py'],['python','tests/iteration39-captures.py']]:
  result=subprocess.run(command,cwd=root,env=env,timeout=600);results.append({'command':command,'exit':result.returncode});assert result.returncode==0,command
 assert before==hashes(),'Built artifact changed during verification'
finally:
 (root/'tmp/planning/iteration39-verification.json').write_text(json.dumps({'commands':results,'files':len(before),'artifactUnchanged':before==hashes(),'indexSha256':before['index.html'],'published':False},indent=2),encoding='utf8');server.shutdown();server.server_close()
