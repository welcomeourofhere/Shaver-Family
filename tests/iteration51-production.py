"""Serve the unchanged build and baseline locally; never publish or submit forms."""
import functools,hashlib,http.server,json,os,socketserver,subprocess,sys,threading
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=root/'tmp/planning/iteration51';out.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):
    daemon_threads=True
def serve(folder):
    server=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}/'
def digest(folder):
    h=hashlib.sha256()
    for file in sorted(folder.rglob('*')):
        if file.is_file():h.update(str(file.relative_to(folder)).replace('\\','/').encode());h.update(hashlib.sha256(file.read_bytes()).digest())
    return h.hexdigest()
current,url=serve(root/'dist');baseline,baseline_url=serve(root/'tmp/baseline51/dist')
env={**os.environ,'QA_BROWSER_SESSION':'soyuz49-touch','QA_BROWSER_SOCKET_DIR':'.local/browser-qa49','QA_URL':url+'previews/contacts/','QA_BASELINE_URL':baseline_url}
capture='--captures' in sys.argv
commands=[['node','tests/iteration51-captures.mjs']] if capture else [['node','tests/iteration51-contacts.mjs'],['node','tests/iteration51-desktop.mjs']]
before=digest(root/'dist');results=[]
try:
    for command in commands:
        local_env={**env}
        if 'desktop' in command[-1]:local_env['QA_URL']=url
        run=subprocess.run(command,cwd=root,env=local_env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=out/(Path(command[-1]).stem+'.log');log.write_text(run.stdout+run.stderr,encoding='utf-8')
        print(run.stdout,flush=True)
        if run.returncode:print(run.stderr,flush=True)
        results.append({'command':command,'exitCode':run.returncode,'log':str(log.relative_to(root))})
        if run.returncode:break
    after=digest(root/'dist')
    sources=json.loads((out/'main-source-baseline.json').read_text(encoding='utf-8'))
    source_check={name:hashlib.sha256((root/name).read_bytes()).hexdigest()==expected for name,expected in sources.items()}
    result={'url':url,'baseline':baseline_url,'before':before,'after':after,'unchanged':before==after,'sourcesUnchanged':source_check,'commands':results,'published':False}
    (out/('capture-verification.json' if capture else 'verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==after and all(source_check.values()) and all(row['exitCode']==0 for row in results)
finally:
    current.shutdown();baseline.shutdown();current.server_close();baseline.server_close()
