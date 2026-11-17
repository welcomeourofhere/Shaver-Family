"""Trusted CDP gestures, frame/index/pulse traces and real Hero video cycles; no physical-device claim."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',required=True);parser.add_argument('--label',required=True);args=parser.parse_args()
OUT=ROOT/'artifacts/iteration67/slide-feedback-hero'/args.label;OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['feedback.ts','rail-selection.ts','native-rail-drag.ts','horizontal-swipe.ts','works.ts','offers.ts','service-deck.ts','hero-news.ts','hero-video-playback.ts']
hashes=lambda:{name:hashlib.sha256((ROOT/'src/scripts'/name).read_bytes()).hexdigest()for name in SOURCES}
before=hashes();results=[];errors=[];failure=None
INIT="""(()=>{
 window.__trace=[];window.__activeRail='';window.__phase='idle';
 const index=()=>{const e=document.querySelector(__activeRail);if(!e)return null;if(__activeRail==='.works-fan')return e.dataset.workIndex;if(__activeRail==='[data-offers]')return e.dataset.offerIndex;if(__activeRail==='[data-service-deck]')return e.querySelector('[data-sd-tab][aria-selected=true]')?.id;return e.dataset.railIndex;};
 const record=(kind,data={})=>__trace.push({kind,at:performance.now(),index:index(),phase:__phase,...data});
 const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/')){record('sound',{src:this.src});return Promise.resolve();}return play.call(this)};
 navigator.vibrate=pattern=>{if(Array.isArray(pattern)&&pattern.some(value=>value>0))record('haptic',{pattern});return true};
 for(const type of['pointerdown','pointermove','pointerup','pointercancel','touchstart','touchmove','touchend','touchcancel'])document.addEventListener(type,e=>{if(__activeRail)record('input',{type,trusted:e.isTrusted,pointerType:e.pointerType||'',touches:e.touches?.length??null})},{capture:true,passive:true});
 let previous=null;window.__resetTrace=selector=>{__activeRail=selector;__phase='held';__trace=[];previous=index();record('index',{initial:true})};
 const frame=()=>{if(__activeRail){const next=index();if(next!==previous){previous=next;record('index')}}requestAnimationFrame(frame)};requestAnimationFrame(frame);
})();"""

def trace(page):return page.evaluate('window.__trace')
def touch(cdp,kind,points):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':points})
def point(page,selector,right=False):
    page.locator(selector).scroll_into_view_if_needed();page.wait_for_timeout(200)
    return page.locator(selector).evaluate("""(e,right)=>{const b=e.getBoundingClientRect();return{x:right?Math.min(innerWidth-32,b.right-32):Math.max(40,Math.min(innerWidth-40,b.left+b.width/2)),y:Math.max(130,Math.min(innerHeight-180,b.top+Math.min(150,b.height/3)))}}""",right)
def begin(page,selector):page.evaluate('(selector)=>__resetTrace(selector)',selector)
def end_touch(page,cdp):page.evaluate("__phase='released'");touch(cdp,'touchEnd',[]);page.wait_for_timeout(700)
def stable_tail(page):
    first=[row for row in trace(page)if row['kind']in['sound','haptic']];page.wait_for_timeout(180)
    assert [row for row in trace(page)if row['kind']in['sound','haptic']]==first,'Delayed feedback replay after the gesture stopped'
def verify_crossings(rows,expect_haptic=True):
    indices=[row for row in rows if row['kind']=='index'and not row.get('initial')]
    pulses=[row for row in rows if row['kind']=='haptic'];sounds=[row for row in rows if row['kind']=='sound']
    assert indices,rows
    if expect_haptic:
        assert [row['index']for row in pulses]==[row['index']for row in indices],{'indices':indices,'pulses':pulses}
        assert all(sum(row['pattern'])<=12 for row in pulses)
    else:assert not pulses,rows
    assert sounds,rows
    assert all(b['at']-a['at']>=47 for a,b in zip(sounds,sounds[1:])),sounds
    latency=[min(abs(pulse['at']-index['at'])for index in indices if index['index']==pulse['index'])for pulse in pulses]
    held_latency=[]
    for pulse in pulses:
        if pulse['phase']!='held':continue
        inputs=[row for row in rows if row['kind']=='input'and row.get('type')in['pointermove','touchmove']and row['at']<=pulse['at']]
        if inputs:held_latency.append(pulse['at']-inputs[-1]['at'])
    assert not latency or max(latency)<35,{'indexToPulse':latency,'trace':rows}
    return {'renderedChanges':len(indices),'haptics':len(pulses),'sounds':len(sounds),'maxIndexToPulseMs':max(latency,default=None),'maxHeldInputToPulseMs':max(held_latency,default=None),'trace':rows}

with sync_playwright()as p:
    browser=p.chromium.launch(channel='chrome')
    def run(name,callback,width=960,motion='no-preference',muted=False):
        global failure
        context=browser.new_context(viewport={'width':width,'height':900 if width>600 else 844},is_mobile=width<=960,has_touch=True,reduced_motion=motion)
        context.add_init_script(INIT)
        if muted:context.add_init_script("if(top===window&&location.origin!=='null')localStorage.setItem('soyuz_feedback_enabled','false')")
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        try:
            page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_timeout(250)
            prompt=page.locator('[data-analytics-prompt]')
            if prompt.is_visible():prompt.locator('.analytics-choice-close').click();prompt.wait_for(state='hidden')
            result=callback(page,context.new_cdp_session(page));results.append({'case':name,**(result or{})})
        except Exception as error:
            failure={'case':name,'message':str(error),'trace':trace(page)}
            page.screenshot(path=str(OUT/'failure-viewport.png'));raise
        finally:context.close()
    try:
        for selector in['#masters-rail','#about-rail','#reviews-rail','#offers-rail']:
            def native(page,cdp,selector=selector):
                q=point(page,selector,True);begin(page,selector);touch(cdp,'touchStart',[{**q,'id':1}])
                for step in range(1,25):touch(cdp,'touchMove',[{'x':q['x']-(q['x']-32)*step/24,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
                held=trace(page);assert any(row['kind']=='haptic'and row['phase']=='held'for row in held),held
                end_touch(page,cdp);stable_tail(page);rows=trace(page)
                assert any(row['kind']=='input'and row.get('type')=='pointercancel'for row in rows),'Native-pan pointercancel was not exercised'
                return verify_crossings(rows)
            run('native held/inertia '+selector,native)
        def works(page,cdp):
            q=point(page,'.works-fan');begin(page,'.works-fan');touch(cdp,'touchStart',[{**q,'id':1}])
            for step in range(1,21):touch(cdp,'touchMove',[{'x':q['x']-170*step/20,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
            held=trace(page);assert any(row['kind']=='haptic'and row['phase']=='held'for row in held),held
            page.screenshot(path=str(OUT/'works-held-viewport.png'));end_touch(page,cdp);stable_tail(page);return verify_crossings(trace(page))
        run('Works actual held crossings',works,width=390)
        for selector,observed in[('.works-fan','.works-fan'),('#offers-rail','[data-offers]')]:
            def mouse(page,cdp,selector=selector,observed=observed):
                q=point(page,selector,True);begin(page,observed);page.mouse.move(q['x'],q['y']);page.mouse.down()
                travel=min(520,q['x']-32)
                for step in range(1,31):page.mouse.move(q['x']-travel*step/30,q['y']);page.wait_for_timeout(24)
                held=trace(page);assert any(row['kind']=='sound'and row['phase']=='held'for row in held),held
                page.evaluate("__phase='released'");page.mouse.up();page.wait_for_timeout(700);stable_tail(page)
                return verify_crossings(trace(page),expect_haptic=False)
            run('desktop held '+selector,mouse,width=1440)
        def wide_touch_offer(page,cdp):
            q=point(page,'#offers-rail',True);begin(page,'[data-offers]');touch(cdp,'touchStart',[{**q,'id':1}]);travel=min(550,q['x']-32)
            for step in range(1,31):touch(cdp,'touchMove',[{'x':q['x']-travel*step/30,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
            assert any(row['kind']=='haptic'and row['phase']=='held'for row in trace(page)),trace(page)
            end_touch(page,cdp);stable_tail(page);return verify_crossings(trace(page))
        run('desktop touch offer has only the custom gesture owner',wide_touch_offer,width=1440)
        def quiet(page,cdp):
            q=point(page,'#masters-rail');begin(page,'#masters-rail');touch(cdp,'touchStart',[{**q,'id':1}])
            for step in range(1,11):touch(cdp,'touchMove',[{'x':q['x'],'y':q['y']-150*step/10,'id':1}]);page.wait_for_timeout(24)
            end_touch(page,cdp);assert not [row for row in trace(page)if row['kind']in['sound','haptic']];return {'trace':trace(page)}
        run('native vertical pan remains quiet',quiet,width=390)
        def reduced(page,cdp):
            q=point(page,'.works-fan');begin(page,'.works-fan');touch(cdp,'touchStart',[{**q,'id':1}])
            for step in range(1,16):touch(cdp,'touchMove',[{'x':q['x']-110*step/15,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
            end_touch(page,cdp);stable_tail(page);return verify_crossings(trace(page),expect_haptic=False)
        run('reduced motion keeps audio but no haptics',reduced,width=390,motion='reduce')
        def muted(page,cdp):
            q=point(page,'.works-fan');begin(page,'.works-fan');touch(cdp,'touchStart',[{**q,'id':1}])
            for step in range(1,16):touch(cdp,'touchMove',[{'x':q['x']-110*step/15,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
            end_touch(page,cdp);assert not [row for row in trace(page)if row['kind']in['sound','haptic']];return {'trace':trace(page)}
        run('mute keeps selection silent',muted,width=390,muted=True)
        def service(page,cdp):
            q=point(page,'.sd-stack');begin(page,'[data-service-deck]');touch(cdp,'touchStart',[{**q,'id':1}])
            for step in range(1,11):touch(cdp,'touchMove',[{'x':q['x']-120*step/10,'y':q['y'],'id':1}]);page.wait_for_timeout(24)
            end_touch(page,cdp);stable_tail(page);return verify_crossings(trace(page))
        run('service card accepted crossing',service,width=390)
        def hero(page,cdp):
            video=page.locator('.hero-video');page.wait_for_function('document.querySelector(".hero-video").dataset.heroVideoPlayback==="playing"',timeout=12000)
            box=video.bounding_box();q={'x':box['x']+box['width']/2,'y':max(90,min(350,box['y']+box['height']/3))}
            def tap():touch(cdp,'touchStart',[{**q,'id':1}]);touch(cdp,'touchEnd',[]);page.wait_for_timeout(120)
            tap();assert video.evaluate('v=>v.paused&&v.dataset.heroVideoPlayback==="paused"'),'First tap did not pause'
            page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(150);video.scroll_into_view_if_needed();page.wait_for_timeout(150);assert video.evaluate('v=>v.paused'),'Paused intent was lost on visibility change'
            tap();page.wait_for_function('!document.querySelector(".hero-video").paused');
            for step in range(6):tap();assert video.evaluate('v=>v.paused')==(step%2==0),step
            page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(180);assert video.evaluate('v=>v.paused');video.scroll_into_view_if_needed();page.wait_for_function('!document.querySelector(".hero-video").paused');
            page.screenshot(path=str(OUT/'hero-playing-viewport.png'));return {'paused':video.evaluate('v=>v.paused'),'state':video.get_attribute('data-hero-video-playback'),'time':video.evaluate('v=>v.currentTime')}
        run('Hero real first/rapid tap and visibility intent cycles',hero,width=390)
        def reduced_hero(page,cdp):
            video=page.locator('.hero-video');page.wait_for_timeout(200);assert video.evaluate('v=>v.paused&&!v.getAttribute("src")');q=point(page,'.hero-rail');touch(cdp,'touchStart',[{**q,'id':1}]);touch(cdp,'touchEnd',[]);page.wait_for_function('document.querySelector(".hero-video").dataset.heroVideoPlayback==="playing"',timeout=12000);return {'state':video.get_attribute('data-hero-video-playback')}
        run('Hero reduced autoplay stays off, explicit tap can play',reduced_hero,width=390,motion='reduce')
    finally:
        browser.close()
        (OUT/'report.json').write_text(json.dumps({'origin':args.origin,'cases':results,'failure':failure,'pageerrors':errors,'sourceHashes':before,'sourceUnchanged':hashes()==before,'instrumentation':'Audio play calls and Vibration API calls are recorded; real Hero video delegates to native play. No physical audio/haptic claim.'},ensure_ascii=False,indent=2),encoding='utf8')

assert not errors,errors
assert hashes()==before,'Source changed during frozen gesture verification'
print('PASS',len(results),'trusted gesture/Hero groups; 0 pageerrors; source unchanged; browsers closed')
