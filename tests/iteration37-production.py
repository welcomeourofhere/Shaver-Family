"""Serve the built artifact during native touch verification; never publishes."""
import functools, hashlib, http.server, os, pathlib, subprocess, threading

root=pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass

artifact=root/'dist/index.html'
before=hashlib.sha256(artifact.read_bytes()).hexdigest()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 result=subprocess.run(['node','tests/iteration37-swipes.mjs'],cwd=root,env={**os.environ,'SWIPE_TEST_URL':f'http://127.0.0.1:{server.server_address[1]}/'},timeout=600)
 assert before==hashlib.sha256(artifact.read_bytes()).hexdigest(),'Built artifact changed during verification'
 raise SystemExit(result.returncode)
finally:
 server.shutdown();server.server_close()
