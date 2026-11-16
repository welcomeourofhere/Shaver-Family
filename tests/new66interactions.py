"""Trusted Chromium input + observable audio/vibration API calls. No physical-device claim."""
import argparse
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--origin', default='http://127.0.0.1:4321/')
parser.add_argument('--label', required=True)
args = parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label),'Use a new simple evidence label'
assert urlsplit(args.origin).scheme in ['http','https'] and urlsplit(args.origin).netloc and not urlsplit(args.origin).query
OUT = ROOT / 'tmp/planning/iteration66/interactions' / args.label
OUT.mkdir(parents=True, exist_ok=False)
origin_host = urlsplit(args.origin).netloc
feed = json.loads((ROOT / 'public/data/news.json').read_text(encoding='utf-8'))
feed['generatedAt'] = datetime.now(timezone.utc).isoformat()
for i, item in enumerate(feed['items']):
    item['id'] = str(9000 + i)
    item['url'] = 'https://vk.ru/wall-210007626_' + item['id']
report = {'origin': args.origin, 'engine': 'chromium-channel-chrome', 'cases': [], 'pageErrors': [],
          'boundary': 'Trusted CDP input; instrumented audio/vibration API requests. Fixture controls and held decode are explicit. Not hardware sound/haptics, real Safari, real booking, benchmark or publication.'}
SPY = """(() => {
  if(window.top!==window)return;
  if(localStorage.getItem('soyuz_feedback_enabled')===null)localStorage.setItem('soyuz_feedback_enabled','true');
  window.__qaAudio=[];window.__qaVibrate=[];window.__qaInput=[];
  const record=e=>{const item={type:e.type,trusted:e.isTrusted,pointer:e.pointerType||'',detail:e.detail,
    target:e.target?.id||e.target?.className||e.target?.tagName,defaultPrevented:e.defaultPrevented,deltaX:e.deltaX,deltaY:e.deltaY};
    __qaInput.push(item);setTimeout(()=>item.defaultPrevented=e.defaultPrevented,0);};
  for(const type of ['pointerdown','pointerup','pointercancel','touchstart','touchend','touchcancel','click','keydown','wheel'])
    addEventListener(type,record,{capture:true,passive:true});
  HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/'))__qaAudio.push({src:new URL(this.src).pathname,volume:this.volume,at:performance.now()});return Promise.resolve()};
  Object.defineProperty(navigator,'vibrate',{configurable:true,value:pattern=>{__qaVibrate.push({pattern,at:performance.now()});return true}});
  const decode=HTMLImageElement.prototype.decode;
  window.__holdHeroDecode=false;window.__pendingHeroDecode=[];
  HTMLImageElement.prototype.decode=function(){
    const real=decode.call(this);
    if(!__holdHeroDecode||!this.matches('.hero-photo'))return real;
    const image=this;
    return real.then(()=>new Promise(resolve=>__pendingHeroDecode.push({src:image.currentSrc,release:resolve})));
  };
})()"""


def save():
    (OUT / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def local_route(route):
    url = urlsplit(route.request.url)
    if url.netloc != origin_host:
        route.abort()
    elif url.path.endswith('/data/news.json'):
        route.fulfill(json=feed, headers={'Access-Control-Allow-Origin': '*'})
    else:
        route.continue_()


def reset(page):
    page.wait_for_timeout(90)
    page.evaluate('window.__qaAudio=[];window.__qaVibrate=[];window.__qaInput=[]')


def evidence(page):
    return page.evaluate("""({audio:__qaAudio,haptics:__qaVibrate.filter(x=>JSON.stringify(x.pattern)!=='0'),
      stops:__qaVibrate.filter(x=>JSON.stringify(x.pattern)==='0').length,input:__qaInput})""")


def expect(page, tone=None, haptic=None):
    page.wait_for_timeout(90)
    value = evidence(page)
    assert [x['src'] for x in value['audio']] == ([f'/audio/{tone}.wav'] if tone else []), value
    assert [x['pattern'] for x in value['haptics']] == ([haptic] if haptic else []), value
    assert all(x['volume'] == .18 for x in value['audio']), value
    return value


def case(page, name, run):
    try:
        value = run()
        report['cases'].append({'name': name, 'pass': True, 'evidence': value})
        print('PASS ' + name, flush=True)
    except Exception as error:
        value = {'name': name, 'pass': False, 'error': str(error), 'trace': traceback.format_exc()}
        try:
            value['evidence'] = evidence(page)
            page.screenshot(path=str(OUT / (name.replace(' ', '-') + '.png')))
        except Exception:
            pass
        report['cases'].append(value)
        print('FAIL ' + name + ': ' + str(error)[:400], flush=True)
    save()


def point(page, selector, x=.5, y=.5):
    locator = page.locator(selector).first
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(80)
    rect = locator.bounding_box()
    assert rect, selector
    px = rect['x'] + rect['width'] * x
    py = max(8, min(page.viewport_size['height'] - 8, rect['y'] + rect['height'] * y))
    assert rect['y'] <= py <= rect['y'] + rect['height'], (selector, rect, py)
    assert locator.evaluate('(el,p)=>el.contains(document.elementFromPoint(p.x,p.y))',{'x':px,'y':py}),(selector,rect,px,py,'covered target')
    return {'x': px, 'y': py}


def touch(cdp, p, end='touchEnd', dx=0, dy=0):
    points = lambda x, y: [{'x': x, 'y': y, 'id': 1, 'radiusX': 4, 'radiusY': 4, 'force': 1}]
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': points(p['x'], p['y'])})
    if dx or dy:
        for i in range(1, 13):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': points(p['x'] + dx*i/12, p['y'] + dy*i/12)})
            page_for_touch.wait_for_timeout(17)
    cdp.send('Input.dispatchTouchEvent', {'type': end, 'touchPoints': []})


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='chrome', headless=True)

    def boot(width=800, motion='no-preference'):
        context = browser.new_context(viewport={'width': width, 'height': 1000}, has_touch=True, reduced_motion=motion)
        context.add_init_script(SPY)
        context.route('**/*', local_route)
        page = context.new_page()
        page.on('pageerror', lambda error: report['pageErrors'].append(str(error)))
        page.goto(args.origin, wait_until='domcontentloaded')
        page.evaluate('document.fonts.ready')
        page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
        page.wait_for_timeout(180)
        cdp = context.new_cdp_session(page)
        cdp.send('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
        return context, page, cdp

    try:
        context, page, cdp = boot()
        page_for_touch = page
        page.evaluate("""() => {
          const group=document.createElement('div');group.id='qa-probes';
          group.style='position:fixed;top:120px;left:20px;z-index:9999;background:#fffcf7;padding:12px;display:grid;gap:8px';
          group.innerHTML='<button id="qa-probe" type="button" style="width:190px;height:48px">Проверка действия</button><label id="qa-label" style="display:block;padding:12px"><input id="qa-check" type="checkbox"> Выбор</label>';
          group.querySelector('button').addEventListener('click',e=>{if(window.__qaCancel)e.preventDefault()});
          document.body.append(group);
        }""")

        def generic_touch():
            reset(page);touch(cdp, point(page, '#qa-probe'))
            value=expect(page,'tap',[8])
            assert any(e['type']=='click' and e['trusted'] and e['pointer']=='touch' for e in value['input']), value
            return value
        case(page,'touch accepted once',generic_touch)

        def generic_mouse():
            reset(page);page.locator('#qa-probe').click();value=expect(page,'tap')
            assert any(e['type']=='click' and e['trusted'] and e['pointer']=='mouse' for e in value['input']),value
            return value
        case(page,'mouse after touch has no vibration',generic_mouse)

        def generic_keyboard():
            page.locator('#qa-probe').focus();reset(page);page.keyboard.press('Enter')
            return expect(page,'tap')
        case(page,'keyboard after touch has no vibration',generic_keyboard)

        def cancelled_click():
            page.evaluate('__qaCancel=true');reset(page);touch(cdp,point(page,'#qa-probe'))
            value=expect(page);page.evaluate('__qaCancel=false')
            assert any(e['type']=='click' and e['trusted'] and e['defaultPrevented'] for e in value['input']),value
            return value
        case(page,'cancelled trusted activation is silent',cancelled_click)

        def programmatic_hover():
            reset(page);page.locator('#qa-probe').evaluate('e=>e.click()');page.locator('#qa-probe').hover()
            return expect(page)
        case(page,'programmatic and hover are silent',programmatic_hover)

        def label_touch():
            reset(page);touch(cdp,point(page,'#qa-label',.85))
            value=expect(page,'tap',[8]);assert page.locator('#qa-check').is_checked(),value
            return value
        case(page,'native label forwarding has one cue',label_touch)

        def reduced_touch():
            page.emulate_media(reduced_motion='reduce');reset(page);touch(cdp,point(page,'#qa-probe'))
            value=expect(page,'tap');page.emulate_media(reduced_motion='no-preference');return value
        case(page,'reduced motion keeps sound without haptic',reduced_touch)
        page.locator('#qa-probes').evaluate('e=>e.remove()')

        def menu_mute():
            touch(cdp,point(page,'[data-mobile-nav] [data-open-menu]'));page.wait_for_function("document.querySelector('#mobile-menu').open")
            reset(page);touch(cdp,point(page,'#mobile-menu [data-feedback-toggle]'));muted=expect(page)
            assert page.evaluate("localStorage.getItem('soyuz_feedback_enabled')")=='false',muted
            reset(page);touch(cdp,point(page,'[data-mobile-nav] [data-open-menu]'));expect(page)
            reset(page);touch(cdp,point(page,'[data-mobile-nav] [data-open-menu]'));expect(page)
            page.reload(wait_until='domcontentloaded')
            page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
            reset(page);touch(cdp,point(page,'[data-mobile-nav] [data-open-menu]'));expect(page)
            assert page.locator('#mobile-menu [data-feedback-toggle]').get_attribute('aria-pressed')=='false'
            reset(page);touch(cdp,point(page,'#mobile-menu [data-feedback-toggle]'));enabled=expect(page,'tap',[8])
            touch(cdp,point(page,'[data-mobile-nav] [data-open-menu]'));page.wait_for_function("!document.querySelector('#mobile-menu').open")
            return {'mute':muted,'unmute':enabled}
        case(page,'mute suppresses actions and unmute signals once',menu_mute)

        def service_tab_touch():
            reset(page);touch(cdp,point(page,'#services [data-sd-tab="1"]'))
            value=expect(page,'select',[10]);assert page.locator('#services [data-sd-tab="1"]').get_attribute('aria-selected')=='true',value
            return value
        case(page,'service tab touch has one selection',service_tab_touch)

        def service_keys():
            page.locator('#services [data-sd-tab="1"]').focus();reset(page);page.keyboard.press('ArrowRight')
            value=expect(page,'select');assert page.locator('#services [data-sd-tab="2"]').get_attribute('aria-selected')=='true',value
            return value
        case(page,'service arrow key has one selection',service_keys)

        def service_open_row_cancel():
            selector='#services .sd-card[aria-hidden="false"] .sd-service[open]>summary'
            p=point(page,selector);reset(page);touch(cdp,p)
            value=expect(page);assert page.locator('#services .sd-card[aria-hidden="false"] .sd-service[open]').count()==1,value
            return value
        case(page,'service already open row cancellation is silent',service_open_row_cancel)

        def service_swipe(cancel=False):
            p=point(page,'#services .sd-card[aria-hidden="false"] .sd-title',.8)
            before=page.locator('#services .sd-tab[aria-selected="true"]').get_attribute('data-sd-tab')
            reset(page);touch(cdp,p,'touchCancel' if cancel else 'touchEnd',dx=-230)
            page.wait_for_timeout(500)
            value=expect(page,None if cancel else 'select',None if cancel else [10])
            after=page.locator('#services .sd-tab[aria-selected="true"]').get_attribute('data-sd-tab')
            assert (after==before) if cancel else (after!=before),(before,after,value)
            return {'before':before,'after':after,**value}
        case(page,'service accepted touch swipe has one cue',lambda:service_swipe())
        case(page,'service cancelled touch drag is silent',lambda:service_swipe(True))

        def team_key():
            page.locator('#masters-rail').scroll_into_view_if_needed()
            page.locator('.team-card:first-child .team-book').focus();reset(page);page.keyboard.press('ArrowRight')
            value=expect(page,'select');assert page.locator('#masters-rail').get_attribute('data-rail-index')=='1',value
            return value
        case(page,'team keyboard changes selected master once',team_key)

        def rail_control_touch():
            p=point(page,'[data-rail-controls="masters-rail"] [data-rail-step="1"]');reset(page);touch(cdp,p)
            value=expect(page,'select',[10]);page.wait_for_timeout(400)
            assert len(evidence(page)['audio'])==1 and len(evidence(page)['haptics'])==1,evidence(page)
            return value
        case(page,'native rail button has one cue through settling',rail_control_touch)

        def rail_touch(cancel=False,vertical=False):
            p=point(page,'.team-card[data-mobile-current="true"] .team-portrait',.8,.35)
            before=int(page.locator('#masters-rail').get_attribute('data-rail-index'))
            reset(page);touch(cdp,p,'touchCancel' if cancel else 'touchEnd',dx=0 if vertical else -230,dy=-180 if vertical else 0)
            page.wait_for_timeout(600)
            after=int(page.locator('#masters-rail').get_attribute('data-rail-index'))
            silent=cancel or vertical
            value=expect(page,None if silent else 'select',None if silent else [10])
            if not silent:assert after!=before,(before,after,value)
            return {'before':before,'after':after,**value}
        case(page,'native rail accepted touch swipe has one cue',lambda:rail_touch())
        case(page,'native rail touch cancellation is silent',lambda:rail_touch(True))
        case(page,'native rail vertical scroll is silent',lambda:rail_touch(vertical=True))

        def short_touch_then_mouse():
            page.locator('#masters-rail').scroll_into_view_if_needed()
            page.locator('.team-card[data-mobile-current="true"] .team-book').focus();page.keyboard.press('Home');page.wait_for_timeout(150)
            p=point(page,'.team-card[data-mobile-current="true"] .team-portrait',.6,.35)
            reset(page);touch(cdp,p,dx=-15);page.wait_for_timeout(200)
            short=expect(page)
            assert page.locator('#masters-rail').get_attribute('data-rail-index')=='0',short
            next_button=page.locator('[data-rail-controls="masters-rail"] [data-rail-step="1"]')
            next_button.scroll_into_view_if_needed();reset(page);next_button.click()
            clicked=expect(page,'select')
            return {'shortTouch':short,'nextMouse':clicked}
        case(page,'short touch cannot lend haptics to next mouse action',short_touch_then_mouse)

        def short_touch_then_wheel():
            page.locator('#masters-rail').scroll_into_view_if_needed()
            page.locator('.team-card[data-mobile-current="true"] .team-book').focus();page.keyboard.press('Home');page.wait_for_timeout(150)
            p=point(page,'.team-card[data-mobile-current="true"] .team-portrait',.6,.35)
            reset(page);touch(cdp,p,dx=-15);page.wait_for_timeout(200);short=expect(page)
            assert page.locator('#masters-rail').get_attribute('data-rail-index')=='0',short
            reset(page);page.mouse.move(**p);page.mouse.wheel(360,0);page.wait_for_timeout(500)
            moved=page.locator('#masters-rail').get_attribute('data-rail-index')
            value=expect(page);assert moved!='0',(moved,value)
            return {'shortTouch':short,'wheelIndex':moved,'wheel':value}
        case(page,'short touch cannot lend feedback to wheel scrolling',short_touch_then_wheel)

        def rail_mouse(cancel=False):
            p=point(page,'.team-card[data-mobile-current="true"] .team-portrait',.8,.35)
            before=int(page.locator('#masters-rail').get_attribute('data-rail-index'))
            if before>=page.locator('.team-card').count()-1:
                page.locator('.team-card[data-mobile-current="true"] .team-book').focus();page.keyboard.press('Home');page.wait_for_timeout(150)
                p=point(page,'.team-card[data-mobile-current="true"] .team-portrait',.8,.35)
                before=0
            reset(page);page.mouse.move(**p);page.mouse.down()
            page.mouse.move(p['x']-230,p['y'],steps=12)
            if cancel:page.keyboard.press('Shift');page.wait_for_timeout(250)
            page.mouse.up();page.wait_for_timeout(500)
            value=expect(page,None if cancel else 'select')
            assert not page.locator('dialog[open]').count(),value
            return {'before':before,'after':page.locator('#masters-rail').get_attribute('data-rail-index'),**value}
        case(page,'native rail mouse drag has sound without vibration',lambda:rail_mouse())
        case(page,'cancelled mouse hold late release is silent',lambda:rail_mouse(True))

        def peeking_card():
            page.locator('#masters-rail').scroll_into_view_if_needed()
            page.locator('.team-card[data-mobile-current="true"] .team-book').focus();page.keyboard.press('Home');page.wait_for_timeout(160)
            p=page.evaluate("""() => {const rail=document.querySelector('#masters-rail').getBoundingClientRect(),card=document.querySelectorAll('.team-card')[1].getBoundingClientRect();return{x:(Math.max(card.left,rail.left)+Math.min(card.right,rail.right))/2,y:card.top+120}}""")
            reset(page);touch(cdp,p);selected=expect(page,'select',[10]);page.wait_for_timeout(450)
            assert page.locator('#masters-rail').get_attribute('data-rail-index')=='1' and not page.locator('dialog[open]').count(),selected
            p=point(page,'.team-card[data-mobile-current="true"] [data-team-open]');reset(page);touch(cdp,p)
            opened=expect(page,'open',[12]);assert page.locator('.team-dialog[open]').count()==1,opened
            p=point(page,'.team-dialog[open] [data-dismiss]');reset(page);touch(cdp,p)
            closed=expect(page,'close',[6]);page.wait_for_timeout(350)
            return {'selection':selected,'open':opened,'close':closed}
        case(page,'peeking selection then discovery keep single owners',peeking_card)

        def master_booking():
            p=point(page,'.team-card[data-mobile-current="true"] .team-book')
            reset(page);touch(cdp,p);opened=expect(page,'open',[12])
            assert page.locator('[data-booking-drawer][open]').count()==1,opened
            route=page.locator('[data-booking-frame]').get_attribute('src')
            assert route and 'yclients.ru' in route,route
            reset(page);page.keyboard.press('Escape');closed=expect(page,'close')
            page.wait_for_function("!document.querySelector('[data-booking-drawer]').open")
            return {'iframeRouteOnly':route,'open':opened,'keyboardClose':closed,'submitted':False}
        case(page,'master booking accepts one cue and keyboard close',master_booking)
        context.close()

        context, page, cdp = boot(1440)
        page_for_touch = page
        page.wait_for_selector('.hero-scene[data-news-state="ready"]')

        def hero_rapid():
            page.evaluate('__holdHeroDecode=true')
            next_button=page.locator('.hero-scene [data-rail-step="1"]')
            reset(page);snapshots=[]
            for index in range(1,7):
                next_button.click()
                state=page.evaluate("""() => ({id:document.querySelector('.hero-slide[data-hero-active="true"]').dataset.newsId,
                  counter:document.querySelector('.hero-scene output').textContent,active:document.querySelectorAll('.hero-slide[data-hero-active="true"]').length,
                  href:document.querySelector('.hero-news-link').href})""")
                assert state['id']==str(9000+index) and state['counter']==f'{index+1:02d} / 10' and state['active']==1,state
                snapshots.append(state)
            page.wait_for_function('__pendingHeroDecode.length>0',timeout=5000)
            pending=page.evaluate('__pendingHeroDecode.length')
            assert pending>0,pending
            held=page.evaluate("document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsId")
            assert held=='9006',held
            page.evaluate('__holdHeroDecode=false;for(const item of __pendingHeroDecode)item.release();__pendingHeroDecode=[]')
            page.wait_for_timeout(450)
            assert page.evaluate("document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsId")=='9006'
            page.locator('.hero-rail').focus();page.keyboard.press('ArrowLeft')
            assert page.evaluate("document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsId")=='9005'
            value=evidence(page);assert not value['haptics'],value
            page.screenshot(path=str(OUT/'hero-after-held-decode.png'))
            return {'selectedWhileDecodeHeld':snapshots,'pendingDecodes':pending,**value}
        case(page,'rapid hero selection is independent of held decode',hero_rapid)

        def hero_touch():
            before=int(page.locator('.hero-scene output').inner_text().split('/')[0])-1
            p=point(page,'.hero-scene [data-rail-step="1"]');reset(page);touch(cdp,p)
            value=expect(page,'select',[10]);assert page.locator('.hero-scene output').inner_text()==f'{(before+1)%10+1:02d} / 10',value
            return value
        case(page,'desktop width hero touch button has one cue',hero_touch)

        def hero_key_reduced():
            page.emulate_media(reduced_motion='reduce');page.locator('.hero-rail').focus();reset(page);page.keyboard.press('ArrowRight')
            value=expect(page,'select');assert page.locator('.hero-rail').get_attribute('data-selection-instant')=='true',value
            return value
        case(page,'hero reduced keyboard selection is immediate and single',hero_key_reduced)
        context.close()
    finally:
        browser.close()

report['pass']=all(row['pass'] for row in report['cases']) and not report['pageErrors']
save()
print(json.dumps({'passed':sum(row['pass'] for row in report['cases']),'failed':sum(not row['pass'] for row in report['cases']),
                  'pageErrors':report['pageErrors'],'results':str(OUT/'results.json')},ensure_ascii=False))
raise SystemExit(not report['pass'])
