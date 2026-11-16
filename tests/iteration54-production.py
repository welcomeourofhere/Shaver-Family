"""Run current acceptance against an unchanged local build; no publication or submission."""
import functools,hashlib,http.server,json,os,socketserver,subprocess,sys,threading
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=root/'tmp/planning/iteration54';out.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def copyfile(self,source,outputfile):
        try:super().copyfile(source,outputfile)
        except (ConnectionResetError,BrokenPipeError):pass  # CDP deliberately aborts intercepted fixture requests.
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):
    daemon_threads=True
def serve(folder):
    server=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}/'
def digest(folder):
    h=hashlib.sha256()
    for file in sorted(folder.rglob('*')):
        relative=file.relative_to(folder).as_posix()
        # Live VK delivery updates independently. The tested dist still includes and hashes its frozen copy.
        if folder==root/'public' and (relative in ['data/news.json','data/news.json.tmp'] or relative.startswith('media/news/')):continue
        if file.is_file():h.update(relative.encode());h.update(hashlib.sha256(file.read_bytes()).digest())
    return h.hexdigest()
current,url=serve(root/'dist');baseline,baseline_url=serve(root/'tmp/baseline54/dist')
env={**os.environ,'QA_BROWSER_SESSION':'soyuz49-touch','QA_BROWSER_SOCKET_DIR':'.local/browser-qa49','QA_URL':url,'SWIPE_TEST_URL':url,'SWIPE_TEST_REPORT':'tmp/planning/iteration54/swipes.json','QA_REPORT_PREFIX':'iteration54','QA_BASELINE_URL':baseline_url}
capture='--captures' in sys.argv
names=['iteration54-rails','iteration54-features','iteration54-latest','iteration54-design','iteration54-feedback','iteration54-ui','iteration54-reading','iteration39-layout','iteration39-journeys','iteration46-startup','iteration45-dock-motion','iteration54-swipes','iteration54-loading','iteration54-desktop']
commands=[['node','tests/iteration54-captures.mjs']] if capture else [['node','tests/'+name+'.mjs']for name in names]
previous=json.loads((out/'verification.json').read_text(encoding='utf-8')) if '--resume' in sys.argv else None
if previous:
    (out/'verification-previous-attempt.json').write_text(json.dumps(previous,ensure_ascii=False,indent=2),encoding='utf-8')
    assert previous['before']==previous['after']==digest(root/'dist') and previous['sourcesUnchanged']
    if previous.get('sourceDigests'):assert previous['sourceDigests']=={folder:digest(root/folder)for folder in ['src','content','public']}
    accepted=[row for row in previous['commands'] if row['exitCode']==0]
    commands=commands[len(accepted):]
before=digest(root/'dist');source_before={folder:digest(root/folder) for folder in['src','content','public']};results=accepted[:] if previous else []
try:
    for command in commands:
        run=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        log=out/(Path(command[-1]).stem+'.log');log.write_text(run.stdout+run.stderr,encoding='utf-8')
        print(run.stdout,flush=True)
        if run.returncode:print(run.stderr,flush=True)
        results.append({'command':command,'exitCode':run.returncode,'log':str(log.relative_to(root))})
        if run.returncode:break
    after=digest(root/'dist');source_after={folder:digest(root/folder)for folder in source_before}
    result={'url':url,'baseline':baseline_url,'before':before,'after':after,'unchanged':before==after,'sourcesUnchanged':source_before==source_after,'sourceDigests':source_before,'mutableRuntimeData':['public/data/news.json','public/media/news/'],'commands':results,'published':False}
    (out/('capture-verification.json'if capture else'verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==after and source_before==source_after and all(row['exitCode']==0 for row in results)
finally:
    current.shutdown();baseline.shutdown();current.server_close();baseline.server_close()
