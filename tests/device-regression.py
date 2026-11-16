"""Reuse accepted browser scenarios without rewriting historical reports/tests.

Compact news are deferred; rail observers are isolated per tested carousel.
python -X utf8 tests/device-regression.py [--resume]
"""
import argparse,functools,hashlib,http.server,json,os,socketserver,subprocess,sys,threading
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def copyfile(self,source,output):
        try:super().copyfile(source,output)
        except (ConnectionResetError,ConnectionAbortedError,BrokenPipeError):pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer):daemon_threads=True
def serve(folder):
    server=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}/'
def digest(folder):
    h=hashlib.sha256()
    for path in sorted(folder.rglob('*'),key=lambda p:tuple(part.lower()for part in p.relative_to(folder).parts)):
        relative=path.relative_to(folder).as_posix()
        if folder==ROOT/'public'and(relative in ['data/news.json','data/news.json.tmp']or relative.startswith('media/news/')):continue
        if path.is_file():h.update(relative.encode());h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()
def sources():return {name:digest(ROOT/name)for name in ['src','content','public']}

def main():
    available=['startup','live-rails','rails','features','latest','design','feedback','ui','reading','layout','journeys','dock-startup','dock-motion','swipes','loading','desktop']
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=int,default=56);parser.add_argument('--resume',action='store_true');parser.add_argument('--suites',nargs='+',choices=available);args=parser.parse_args()
    phase=args.phase;OUT=ROOT/f'tmp/planning/iteration{phase}/regression';OUT.mkdir(parents=True,exist_ok=True)
    names=args.suites or available
    before=digest(ROOT/'dist');source_before=sources();accepted=[]
    if args.resume:
        previous=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
        assert previous['before']==previous['after']==before and previous['sourceDigests']==source_before
        assert previous.get('suites',available)==names
        accepted=[row for row in previous['commands']if row['exitCode']==0]
    current,url=serve(ROOT/'dist');baseline,baseline_url=serve(ROOT/f'tmp/baseline{phase}/dist');gallery,gallery_url=serve(ROOT/'artifacts/preloader-options')
    env={**os.environ,'QA_BROWSER_SESSION':f'soyuz{phase}-regression','QA_BROWSER_SOCKET_DIR':f'.local/browser-qa{phase}','QA_URL':url,'SWIPE_TEST_URL':url,'SWIPE_TEST_REPORT':f'tmp/planning/iteration{phase}/regression/swipes.json','QA_REPORT_PREFIX':f'iteration{phase}/regression','QA_BASELINE_URL':baseline_url,'QA_GALLERY_URL':os.environ.get('QA_GALLERY_URL',gallery_url)}
    results=accepted[:]
    try:
        for name in names[len(accepted):]:
            original=ROOT/f'tests/iteration55-{name}.mjs'
            source=original.read_text(encoding='utf-8').replace('tmp/planning/iteration55',f'tmp/planning/iteration{phase}/regression')
            if name=='swipes' and phase>=60:
                # The accepted iteration-58 compact deck reveals the underlying card on both swipe directions.
                source=source.replace("scene.name==='services'&&width<=600", "scene.name==='services'&&width<=960")
            if phase>=62:
                if name=='startup':
                    # Without scripts the disclosure deliberately exposes every review, like FAQ.
                    # The separate deferred-script cases still require identical initial/final geometry.
                    source=source.replace("selector==='#faq'&&property==='height'||selector==='#contacts'&&property==='top'", "selector==='#faq'&&['height','top'].includes(property)||selector==='#contacts'&&property==='top'||selector==='.reviews-rail'&&property==='height'")
                if name in ['ui','reading']:
                    # These retained suites exercise the complete bento; additions.py owns the new four-card preview.
                    source=source.replace("await b.until(`document.querySelector('#reviews-rail').dataset.bentoReady==='true'`)","await b.until(`document.querySelector('#reviews-rail').dataset.bentoReady==='true'`);await b.evaluate(`document.querySelector('[data-review-more]')?.click()`);await b.settle()")
                if name=='ui':
                    count=len(json.loads((ROOT/'content/reviews.json').read_text(encoding='utf-8')))
                    source=source.replace('g.cards.length,7',f'g.cards.length,{count}')
                if name=='reading':
                    source=source.replace('Math.max(...Object.values(counts))<=4','Math.max(...Object.values(counts))<=Math.floor(2*state.cards.length/3)')
                if name=='journeys':
                    # Real desktop iframe/mobile popup clicks are exercised in all engines by additions.py.
                    # Keep the inherited menu/booking scenario without the obsolete contact-dialog purchase.
                    source=source.replace('certificate action and menu booking use their original dialogs','certificate link and menu booking use their current destinations')
                    source=source.replace("await click('[data-action=\"certificate-buy\"]');assert.equal(await b.evaluate(`document.querySelector('#contact-dialog').open`),true);await close();", "assert.deepEqual(await b.evaluate(`(()=>{const a=document.querySelector('.certificate-buy');return{href:a.href,target:a.target,dialog:document.querySelector('[data-action=\"certificate-buy\"]').getAttribute('aria-haspopup')}})()`),{href:'https://o16013.yclients.ru/certificates',target:'_blank',dialog:null});")
                if name=='latest':
                    # Refresh waits while the user points at or focuses the news. Isolate decode from that contract.
                    source=source.replace("await b.send('Fetch.enable',{patterns:[{urlPattern:'*/data/news.json*',requestStage:'Request'}]});", "await b.send('Fetch.enable',{patterns:[{urlPattern:'*/data/news.json*',requestStage:'Request'}]});await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:4,y:4});")
                    source=source.replace("await check('a news refresh received during image decoding commits after the current slide transition',async()=>{", "await check('a news refresh received during image decoding commits after the current slide transition',async()=>{await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:4,y:4});await b.evaluate(`document.activeElement?.blur?.()`);assert.ok(await b.evaluate(`!document.querySelector('.hero-scene').matches(':hover')&&!document.querySelector('.hero-scene').contains(document.activeElement)`));")
                    # The real public GitHub feed is cross-origin and supplies this CORS header.
                    source=source.replace("responseHeaders:[{name:'Content-Type',value:'application/json'}]","responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:'*'}]")
                    source=source.replace("await b.tap(await b.point('#review-03 [data-review-read]'));await b.evaluate", "await b.tap(await b.point('#review-03 [data-review-read]'));await b.settle();await b.evaluate")
                    source=source.replace("await b.until(`document.querySelector('.hero-scene').dataset.newsRevision==='2032-01-01T00:00:00+03:00'`)","await b.until(`document.querySelector('.hero-scene').dataset.newsRevision==='2032-01-01T00:00:00+03:00'`).catch(async error=>{throw new Error(JSON.stringify({error:String(error),state:await b.evaluate(`({hover:document.querySelector('.hero-scene').matches(':hover'),focus:document.activeElement.outerHTML.slice(0,300),current:[...document.querySelectorAll('.hero-slide')].findIndex(e=>e.dataset.heroActive==='true'),revision:document.querySelector('.hero-scene').dataset.newsRevision})`)}))})")
            if name=='loading' and phase>=60:
                # Approved reused posters may already be decoded. Exercise pending with distinct local fixtures.
                source=source.replace(" await b.center('.sd-card[aria-hidden=\"false\"]');holdImages=true;", """ await b.evaluate(`(()=>{for(const [id,name]of [['main-15270008','one'],['main-267630','two']]){const row=document.querySelector('.sd-card[aria-hidden="false"] .sd-service[data-service-id="'+id+'"]');row.dataset.photoSrc=new URL('__loading_probe__/service-'+name+'.webp',location.href).href;row.dataset.photoSrcset=''}})()`);
 await b.center('.sd-card[aria-hidden="false"]');holdImages=true;""")
            if name=='rails':
                # Trust a press only when its coordinates actually hit that control.
                source=source.replace('const p=await b.point(selector);await mouse(','''const p=await b.point(selector);assert.ok(await b.evaluate(`(()=>{const button=document.querySelector(${JSON.stringify(selector)});return button?.contains(document.elementFromPoint(${p.x},${p.y}))})()`),'Stress press must hit its control: '+selector);await mouse(''')
                # A delayed event from the previous rail must not enter the next rail's trace.
                source=source.replace('window.__railIndices=[];const rail=', 'window.__railIndexObserver?.disconnect();window.__railIndices=[];const rail=')
                source=source.replace('new MutationObserver(records=>{const i=Number(rail.dataset.railIndex);if(__railIndices.at(-1)!==i)__railIndices.push(i)}).observe(rail', '(window.__railIndexObserver=new MutationObserver(records=>{const i=Number(rail.dataset.railIndex);if(__railIndices.at(-1)!==i)__railIndices.push(i)})).observe(rail')
            if name=='latest':
                start=source.index(" await check('news refresh leaves compact hero on its single video'")
                end=source.index('\n await b.send(\'Fetch.disable\')',start)
                source=source[:start]+''' await check('compact Hero defers hidden news until returning to desktop',async()=>{
  feed={...feed,generatedAt:'2031-01-01T00:00:00+03:00'};const before=requests;
  await b.viewport(390,900,true);await b.open(base);await b.pause(150);assert.equal(requests,before);
  const state=await b.evaluate(`({active:[...document.querySelectorAll('.hero-slide')].filter(e=>e.offsetWidth&&e.getAttribute('aria-hidden')==='false').length,video:!!document.querySelector('.hero-slide[data-hero-active="true"] video'),dots:document.querySelector('.hero-controls').offsetHeight,errors:__touchErrors})`);
  assert.equal(state.active,1);assert.ok(state.video);assert.equal(state.dots,0);assert.deepEqual(state.errors,[]);
  await b.viewport(1440,900,true);await b.until(`document.querySelector('.hero-scene').dataset.newsRevision==='2031-01-01T00:00:00+03:00'`);assert.ok(requests>before);return state;
 });\n'''+source[end:]
            temporary=ROOT/f'tests/.device{phase}-{name}.mjs';assert not temporary.exists();temporary.write_text(source,encoding='utf-8')
            try:
                run=subprocess.run(['node',str(temporary)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
            finally:temporary.unlink(missing_ok=True)
            log=OUT/f'{name}.log';log.write_text(run.stdout+run.stderr,encoding='utf-8')
            passed=sum(line.startswith('PASS ')for line in run.stdout.splitlines())
            results.append({'suite':name,'source':str(original.relative_to(ROOT)),'passedScenarios':passed,'exitCode':run.returncode,'log':str(log.relative_to(ROOT))})
            print(f'{name}: exit={run.returncode}, passed={passed}',flush=True)
            if run.returncode:print((run.stdout+run.stderr)[-5500:],flush=True);break
    finally:
        after=digest(ROOT/'dist');source_after=sources()
        (OUT/'verification.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'sourceDigests':source_before,'sourcesUnchanged':source_before==source_after,'suites':names,'commands':results,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
        for server in [current,baseline,gallery]:server.shutdown();server.server_close()
    assert len(results)==len(names) and before==after and source_before==source_after and all(row['exitCode']==0 for row in results)
if __name__=='__main__':main()
