"""Local browser-engine/device-profile checks; no publication or real submissions.

python -X utf8 tests/device-compatibility.py [--root dist] [--label candidate]
Requires the separately installed Python Playwright and its Firefox/WebKit binaries.
Chromium uses the installed Chrome/Edge, never a personal profile.
"""
import argparse, functools, hashlib, http.server, json, socketserver, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def copyfile(self,source,output):
        try: super().copyfile(source,output)
        except (ConnectionResetError,BrokenPipeError): pass
class Server(socketserver.ThreadingMixIn,http.server.HTTPServer): daemon_threads=True
def digest(folder):
    h=hashlib.sha256()
    for path in sorted(folder.rglob('*'),key=lambda p:tuple(part.lower()for part in p.relative_to(folder).parts)):
        if path.is_file():h.update(path.relative_to(folder).as_posix().encode());h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()

def settle(page):
    page.evaluate("document.fonts.ready")
    page.wait_for_function("!document.querySelector('[data-review-bento]') || document.querySelector('[data-review-bento]').dataset.bentoReady==='true'")
    page.wait_for_timeout(80)

def run(page,width,height):
    page.wait_for_function("!!document.querySelector('.of-rail[data-loop-ready]')")
    settle(page)
    geometry=page.evaluate("""() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,
      logo:document.querySelector('.hero-brand').getBoundingClientRect().toJSON(),
      hero:document.querySelector('.hero-scene').getBoundingClientRect().toJSON(),
      dock:document.querySelector('.mobile-nav').getBoundingClientRect().toJSON(),
      sections:document.querySelectorAll('main>section').length})""")
    assert geometry['scroll']<=width+1,geometry
    assert geometry['sections']>=10,geometry
    if width<=960:
        assert geometry['hero']['height']>=height-1,geometry
        assert abs(geometry['logo']['x']+geometry['logo']['width']/2-width/2)<1,geometry
        assert geometry['logo']['y']>=31,geometry
        assert geometry['dock']['x']>=0 and geometry['dock']['right']<=width+1,geometry
        page.locator('[data-open-menu]').click()
        page.wait_for_function("document.querySelector('#mobile-menu').open")
        trigger=page.locator('#mobile-menu .choice-trigger')
        trigger.click(); page.wait_for_function("!!document.querySelector('.choice-list:popover-open')")
        trigger.click(); page.wait_for_function("!document.querySelector('.choice-list:popover-open')")
        trigger.click(); page.locator('.choice-list:popover-open [data-value="dark"]').click()
        assert page.locator('html').get_attribute('data-theme')=='dark'
        page.keyboard.press('Escape'); page.wait_for_function("!document.querySelector('#mobile-menu').open")
        for selector in ['.of-rail','.team-grid','.about-stack','.gifts-grid','.reviews-rail']:
            page.eval_on_selector(selector,"e=>{e.scrollLeft=0;e.scrollIntoView({block:'center',behavior:'instant'})}")
            page.wait_for_timeout(100)
            p=page.eval_on_selector(selector,"""e=>{const r=e.getBoundingClientRect();return{x:Math.min(innerWidth-25,r.right-25),y:Math.max(90,Math.min(innerHeight-130,r.top+100))}}""")
            page.mouse.move(p['x'],p['y']); page.mouse.down()
            page.mouse.move(p['x']-220,p['y'],steps=10)
            held=page.eval_on_selector(selector,"e=>({left:e.scrollLeft,index:e.dataset.railIndex})")
            assert held['left']>90,(selector,held)
            assert int(held['index'])>=1,(selector,held)
            page.mouse.up()
            page.wait_for_function("s=>document.querySelector(s).dataset.railSettling==='false'",arg=selector)
    page.locator('[data-sd-tab="1"]').click()
    assert page.locator('[data-sd-tab="1"]').get_attribute('aria-selected')=='true'
    page.locator('.faq-item summary').first.click()
    assert page.locator('.faq-item').first.get_attribute('open') is not None
    page.locator('.faq-item summary').first.click()
    return geometry

def media_run(page,phone):
    settle(page)
    if phone:
        page.wait_for_function("document.querySelector('.hero-video').readyState>=2&&document.querySelector('.hero-video').currentTime>0")
        before=page.locator('.hero-video').evaluate('v=>v.currentTime');page.wait_for_timeout(500)
        after=page.locator('.hero-video').evaluate('v=>({time:v.currentTime,ready:v.readyState,src:v.getAttribute("src"),error:v.error?.code})')
        assert after['time']>before and not after.get('error'),after
        page.locator('#faq').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
        page.wait_for_function("document.querySelector('.hero-video').paused")
        return after
    page.wait_for_function("document.querySelector('.hero-slide[data-hero-active=true] .hero-photo').naturalWidth>1")
    assert page.locator('.hero-video').get_attribute('src') is None
    rail=page.locator('.hero-rail');rail.focus();before=page.locator('.hero-position').inner_text()
    page.keyboard.press('ArrowRight');page.wait_for_function("previous=>document.querySelector('.hero-position').textContent!==previous",arg=before)
    page.wait_for_function("document.querySelector('.hero-slide[data-hero-active=true] .hero-photo').naturalWidth>1")
    return {'before':before,'after':page.locator('.hero-position').inner_text()}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='dist');parser.add_argument('--label',default='candidate')
    parser.add_argument('--quick',action='store_true');parser.add_argument('--phase',type=int,default=56);args=parser.parse_args()
    folder=(ROOT/args.root).resolve();assert folder.is_dir();before=digest(folder)
    output=ROOT/f'tmp/planning/iteration{args.phase}';output.mkdir(parents=True,exist_ok=True)
    shots=ROOT/f'artifacts/iteration{args.phase}';shots.mkdir(parents=True,exist_ok=True)
    server=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
    results=[]
    profiles=[(280,653,1),(320,568,1),(390,844,1),(600,800,1),(768,1024,1),(844,390,1),(960,600,1),(1024,768,1),(1440,900,1),(1920,1080,1),(2560,1440,1),(390,844,3),(768,1024,2)]
    if args.quick:profiles=[(390,844,1),(1440,900,1)]
    try:
        with sync_playwright() as pw:
            for name in ['chrome','msedge','firefox','webkit']:
                browser=pw.chromium.launch(channel=name)if name in ['chrome','msedge']else getattr(pw,name).launch()
                try:
                    for width,height,dpr in profiles:
                        context=browser.new_context(viewport={'width':width,'height':height},has_touch=width<=960 and name!='firefox',
                            reduced_motion='reduce',device_scale_factor=dpr,**({'is_mobile':width<=960}if name!='firefox'else{}))
                        context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(base)or route.request.url.startswith('data:')else route.abort())
                        page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                        row={'browser':name,'version':browser.version,'width':width,'height':height,'dpr':dpr,'input':'trusted mouse; touch-capable context'if width<=960 and name!='firefox'else'trusted mouse','reduced':True}
                        try:
                            page.goto(base,wait_until='domcontentloaded');row['geometry']=run(page,width,height)
                            assert not errors,errors
                            row['passed']=True
                            if width in [390,1440]:
                                page.evaluate("scrollTo({top:0,behavior:'instant'})")
                                if width<=960:page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.section==='top'")
                                page.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                                page.screenshot(path=str(shots/f'{args.label}-{name}-{width}{"-dpr"+str(dpr)if dpr>1 else""}.png'))
                        except Exception as error:
                            row.update(passed=False,error=str(error),scriptErrors=errors)
                            page.screenshot(path=str(shots/f'{args.label}-{name}-{width}-dpr{dpr}-failure.png'))
                        finally:context.close()
                        results.append(row);print(('PASS 'if row['passed']else'FAIL ')+f'{name} {width}x{height} DPR{dpr} '+row.get('error','')[:350],flush=True)
                    for phone in [True,False]:
                        context=browser.new_context(viewport={'width':390 if phone else 1440,'height':844 if phone else 900},has_touch=phone and name!='firefox',reduced_motion='no-preference',**({'is_mobile':phone}if name!='firefox'else{}))
                        context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(base)or route.request.url.startswith('data:')else route.abort())
                        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));row={'browser':name,'version':browser.version,'normalMedia':True,'phone':phone}
                        try:
                            page.goto(base,wait_until='domcontentloaded');row['media']=media_run(page,phone);assert not errors,errors;row['passed']=True
                        except Exception as error:row.update(passed=False,error=str(error),scriptErrors=errors)
                        finally:context.close()
                        results.append(row);print(('PASS 'if row['passed']else'FAIL ')+f'{name} normal media phone={phone} '+row.get('error','')[:350],flush=True)
                finally:browser.close()
    finally:
        server.shutdown();server.server_close()
        after=digest(folder)
        (output/f'compatibility-{args.label}.json').write_text(json.dumps({'cases':results,'root':str(folder),'buildSha256':before,'unchanged':before==after,'externalRequestsBlocked':True,'physicalDevices':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==after and results and all(row['passed']for row in results),'Browser compatibility failures'
if __name__=='__main__':main()
