"""Check the full-width dock on the frozen local build, without sending forms."""
import functools,hashlib,http.server,json,os,pathlib,subprocess,threading
root=pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def hashes():return{str(p.relative_to(root/'dist')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'dist').rglob('*') if p.is_file()}
before=hashes();server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();env={**os.environ,'QA_URL':f'http://127.0.0.1:{server.server_address[1]}/','QA_REPORT_PREFIX':'iteration40'};results=[]
try:
 for script,extra in [('iteration39-layout.mjs',{}),('iteration39-journeys.mjs',{}),('iteration39-motion.mjs',{'QA_MOTION_ONLY':'dock'})]:
  result=subprocess.run(['node','tests/'+script],cwd=root,env={**env,**extra},timeout=180);results.append({'script':script,**extra,'exit':result.returncode});assert result.returncode==0,script
 assert before==hashes(),'Built artifact changed during verification'
finally:
 (root/'tmp/planning/iteration40-verification.json').write_text(json.dumps({'commands':results,'files':len(before),'artifactUnchanged':before==hashes(),'indexSha256':before['index.html'],'published':False},indent=2),encoding='utf8');server.shutdown();server.server_close()
