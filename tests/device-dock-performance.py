"""Paired local dock work samples; preserves motion, not a field INP/FPS claim.
python -X utf8 tests/device-dock-performance.py --phase 57 --runs 3
"""
import argparse,importlib.util,json,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('device_lab',ROOT/'tests/device-performance.py');lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
INSTRUMENT="""window.dockLab={rect:0,style:0,events:[]};
const rect=Element.prototype.getBoundingClientRect,style=window.getComputedStyle;
Element.prototype.getBoundingClientRect=function(...args){if(this.closest?.('[data-mobile-nav]'))dockLab.rect++;return rect.apply(this,args)};
window.getComputedStyle=function(element,...args){if(element.closest?.('[data-mobile-nav]'))dockLab.style++;return style.call(this,element,...args)};
if(PerformanceObserver.supportedEntryTypes.includes('event'))new PerformanceObserver(list=>dockLab.events.push(...list.getEntries().map(e=>({name:e.name,duration:e.duration,processing:e.processingEnd-e.processingStart,id:e.interactionId})))).observe({type:'event',buffered:true,durationThreshold:16});"""
def sample(browser,url):
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='no-preference')
    context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(url)else route.abort());context.add_init_script(INSTRUMENT)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');page.evaluate('document.fonts.ready')
    page.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'")
    page.locator('#faq').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})");page.wait_for_timeout(500)
    cdp=context.new_cdp_session(page);cdp.send('Performance.enable');cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    page.evaluate('dockLab.rect=0;dockLab.style=0;dockLab.events=[]');before={r['name']:r['value']for r in cdp.send('Performance.getMetrics')['metrics']}
    for _ in range(6):
        p=page.locator('[data-open-menu]').evaluate("e=>{const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}}")
        page.mouse.click(p['x'],p['y']);page.wait_for_function("document.querySelector('#mobile-menu').open");page.wait_for_timeout(420)
        page.keyboard.press('Escape');page.wait_for_function("!document.querySelector('#mobile-menu').open");page.wait_for_timeout(340)
    after={r['name']:r['value']for r in cdp.send('Performance.getMetrics')['metrics']};motion=page.evaluate('({...dockLab})')
    page.wait_for_timeout(300);page.evaluate('dockLab.rect=0;dockLab.style=0')
    # Same section, same actions: scrolling must not re-measure an unchanged toolbar.
    page.evaluate("new Promise(resolve=>{const start=scrollY;let i=0;function tick(){scrollTo({top:start+(i%2?5:0),behavior:'instant'});if(++i<24)requestAnimationFrame(tick);else setTimeout(resolve,100)}tick()})")
    scroll=page.evaluate('({rect:dockLab.rect,style:dockLab.style})');assert not errors,errors;context.close()
    return {'motion':motion,'sameContextScroll':scroll,'cpuSeconds':{key:after[key]-before[key]for key in ['ScriptDuration','LayoutDuration','TaskDuration']},'errors':errors}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=int,default=57);parser.add_argument('--runs',type=int,default=3);parser.add_argument('--baseline',type=Path);args=parser.parse_args()
    folders={'baseline':args.baseline.resolve()if args.baseline else ROOT/f'tmp/baseline{args.phase}/dist','candidate':ROOT/'dist'};before={k:lab.digest(v)for k,v in folders.items()};servers={k:lab.serve(v)for k,v in folders.items()};rows=[]
    try:
        with sync_playwright()as pw:
            browser=pw.chromium.launch(channel='chrome')
            try:
                for index in range(args.runs):
                    for label in (['baseline','candidate']if index%2==0 else ['candidate','baseline']):
                        row=sample(browser,servers[label][1]);row.update(label=label,run=index+1,version=browser.version);rows.append(row)
                        print(json.dumps({'label':label,'run':index+1,'motionRect':row['motion']['rect'],'motionStyle':row['motion']['style'],'scroll':row['sameContextScroll'],'cpu':row['cpuSeconds']}),flush=True)
            finally:browser.close()
    finally:
        for server,_ in servers.values():server.shutdown();server.server_close()
        after={k:lab.digest(v)for k,v in folders.items()};out=ROOT/f'tmp/planning/iteration{args.phase}';out.mkdir(parents=True,exist_ok=True)
        summary={label:{'menuRectReads':statistics.median(r['motion']['rect']for r in rows if r['label']==label),'menuStyleReads':statistics.median(r['motion']['style']for r in rows if r['label']==label),'sameContextStyleReads':statistics.median(r['sameContextScroll']['style']for r in rows if r['label']==label),'cpuSeconds':{key:statistics.median(r['cpuSeconds'][key]for r in rows if r['label']==label)for key in ['ScriptDuration','LayoutDuration','TaskDuration']}}for label in folders}if len(rows)==args.runs*2 else {}
        (out/'dock-performance.json').write_text(json.dumps({'rows':rows,'summary':summary,'hashes':before,'unchanged':before==after,'conditions':'Chrome 390x844 touch-capable context, CPU x4, six open/close cycles; no parallel browser jobs','fieldData':False,'physicalDevice':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==after and len(rows)==args.runs*2
if __name__=='__main__':main()
