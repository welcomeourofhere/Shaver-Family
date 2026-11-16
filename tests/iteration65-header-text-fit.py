"""Header content fit with actual 200% text size, independent of browser zoom."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--origin', default='http://127.0.0.1:4321/')
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--static', action='store_true', help='Also delay the built Header module to verify the initial CSS layout')
args = parser.parse_args()
OUT = ROOT / 'tmp/planning/iteration65/header-text-fit'
OUT.mkdir(parents=True, exist_ok=True)
rows, errors = [], []

# Match the whole-site audit: freeze every direct text parent's computed size
# first, then double that size. This is text enlargement, not viewport zoom.
SCALE_TEXT = """()=>{
 const texts=[...document.querySelectorAll('body *')]
   .filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));
 const sizes=texts.map(e=>parseFloat(getComputedStyle(e).fontSize));
 texts.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px');
}"""

GEOMETRY = """()=>{
 const capsule=document.querySelector('.header-capsule'), box=capsule.getBoundingClientRect();
 const controls=[...document.querySelectorAll('.header-nav>a,.more-menu>summary,.header-logo,.header-phone,.header-book,.header-hours .info-trigger-text')]
   .filter(e=>e.getClientRects().length).map(e=>{
    const r=e.getBoundingClientRect(),s=getComputedStyle(e),ranges=[];
    const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
    while(walker.nextNode())if(walker.currentNode.textContent.trim()){
      const range=document.createRange();range.selectNodeContents(walker.currentNode);
      ranges.push(...[...range.getClientRects()].map(v=>({x:v.x,y:v.y,width:v.width,height:v.height,right:v.right,bottom:v.bottom})));
    }
    return{text:e.textContent.trim(),class:e.className,rect:r.toJSON(),padding:[parseFloat(s.paddingLeft),parseFloat(s.paddingRight)],nowrap:s.whiteSpace,ranges};
   });
 return{capsule:box.toJSON(),controls,logo:document.querySelector('.header-logo').getBoundingClientRect().toJSON(),wrap:[getComputedStyle(document.querySelector('.header-nav')).flexWrap,getComputedStyle(document.querySelector('.header-actions')).flexWrap]};
}"""

def check_geometry(value):
    box=value['capsule']
    assert value['wrap']==['wrap','wrap'], ('source CSS not delivered',value['wrap'])
    assert abs((value['logo']['x']+value['logo']['width']/2)-(box['x']+box['width']/2))<1, value
    for i, control in enumerate(value['controls']):
        r=control['rect']
        assert r['x']>=box['x']-1 and r['right']<=box['right']+1 and r['y']>=box['y']-1 and r['bottom']<=box['bottom']+1, control
        assert r['height']>=44,control
        if control['text']:
            assert control['nowrap']=='nowrap' and min(control['padding'])>=12, control
            assert len({round(t['y'])for t in control['ranges']})==1, ('wrapped label',control)
            for t in control['ranges']:
                assert t['x']>=r['x']+control['padding'][0]-1 and t['right']<=r['right']-control['padding'][1]+1, ('clipped label',control)
        for other in value['controls'][i+1:]:
            t=other['rect']
            overlap=max(0,min(r['right'],t['right'])-max(r['x'],t['x']))*max(0,min(r['bottom'],t['bottom'])-max(r['y'],t['y']))
            assert overlap<1, ('overlapping controls',control,other,overlap)

def panel_geometry(page, selector, links_required=True):
    value=page.locator(selector).evaluate("""e=>({rect:e.getBoundingClientRect().toJSON(),links:[...e.querySelectorAll('a')].filter(x=>x.getClientRects().length).map(x=>{const r=x.getBoundingClientRect(),s=getComputedStyle(x);return{text:x.textContent.trim(),rect:r.toJSON(),nowrap:s.whiteSpace,padding:[parseFloat(s.paddingLeft),parseFloat(s.paddingRight)],overflow:x.scrollWidth>x.clientWidth+1}})})""")
    r=value['rect']
    assert r['x']>=0 and r['right']<=page.viewport_size['width'] and r['y']>=0 and r['bottom']<=page.viewport_size['height'],value
    assert value['links'] or not links_required, value
    shell=page.locator('.header-capsule').bounding_box()
    scale=shell['width']/page.locator('.header-capsule').evaluate('e=>e.offsetWidth')
    assert abs((r['y']-(shell['y']+shell['height']))-8*scale)<1, ('popup not below capsule by8px',r,shell)
    for link in value['links']:
        assert link['rect']['height']>=44 and link['nowrap']=='nowrap' and min(link['padding'])>=12 and not link['overflow'],link
    return value

def hold_gap(page,menu_selector,panel_selector):
    shell=page.locator('.header-capsule').bounding_box()
    trigger=page.locator(menu_selector+'>summary').bounding_box()
    panel=page.locator(panel_selector).bounding_box()
    x=max(panel['x']+4,min(panel['x']+panel['width']-4,trigger['x']+trigger['width']/2))
    page.mouse.move(x,shell['y']+shell['height']+4,steps=4)
    page.wait_for_timeout(350)
    assert page.locator(menu_selector).evaluate('e=>e.open'), ('slow8px-gap crossing closed popup',menu_selector)
    assert page.locator(panel_selector).evaluate('e=>e.matches(":hover")'), ('gap is not covered by common bridge',panel_selector)

with sync_playwright() as p:
    browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
    native=browser.new_page()
    native.set_content('<details open><summary>Menu</summary><a href="#first">First</a><a href="#second">Second</a></details><button>Next</button>')
    native.locator('summary').focus();native.keyboard.press('Tab')
    native_link_tabbing=native.evaluate("document.activeElement.tagName==='A'")
    native.close()
    for width in [961,1024,1280,1440]:
        for theme in ['light','dark']:
            for scale in [1,2]:
                context=browser.new_context(viewport={'width':width,'height':720},color_scheme=theme,reduced_motion='no-preference')
                page=context.new_page()
                page.on('pageerror',lambda error:errors.append(error.stack))
                page.goto(args.origin,wait_until='domcontentloaded')
                page.evaluate('document.fonts.ready')
                page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
                page.wait_for_timeout(350)
                if scale==2:page.evaluate(SCALE_TEXT)
                page.wait_for_timeout(100)
                compact=page.evaluate("matchMedia('(max-width:960px)').matches")
                if compact:
                    assert width==961 and not page.locator('.site-header').is_visible(), (width,compact)
                    menu=page.locator('[data-open-menu]');menu.focus();page.keyboard.press('Enter');page.locator('#mobile-menu').wait_for(state='visible');page.wait_for_timeout(350)
                    assert page.locator('#mobile-menu .menu-business>a').is_visible()
                    assert page.locator('#mobile-menu .menu-contact-row>a').is_visible()
                    assert page.locator('#mobile-menu .menu-business>a').evaluate('e=>e.getBoundingClientRect().height>=44')
                    page.keyboard.press('Tab');assert page.locator('#mobile-menu').evaluate('e=>e.contains(document.activeElement)')
                    page.keyboard.press('Escape');page.locator('#mobile-menu').wait_for(state='hidden');assert menu.evaluate('e=>e===document.activeElement')
                    rows.append({'width':width,'theme':theme,'textScale':scale,'compact':True,'availableWidth':page.evaluate('document.documentElement.clientWidth'),'keyboard':True})
                    context.close();print('case',args.engine,width,theme,scale,'compact PASS',flush=True);continue
                value=page.evaluate(GEOMETRY)
                assert value['controls'], 'desktop header controls are missing'
                check_geometry(value)
                unchanged=None
                if scale==1:
                    # The previous nowrap layout is an in-page control, with the
                    # same fonts, scrollbar, dimensions and loaded DOM.
                    baseline=page.add_style_tag(content='.header-nav,.header-actions{flex-wrap:nowrap!important}')
                    old=page.evaluate(GEOMETRY)
                    baseline.evaluate('e=>e.remove()')
                    unchanged=all(abs(a['rect'][k]-b['rect'][k])<.1 for a,b in zip(value['controls'],old['controls'])for k in ['x','y','width','height'])
                    assert unchanged,('standard geometry changed',value,old)
                more=page.locator('.more-menu>summary')
                more.hover()
                page.wait_for_timeout(350)
                assert page.locator('.more-menu').evaluate('e=>e.open')
                more_value=panel_geometry(page,'.more-panel')
                hold_gap(page,'.more-menu','.more-panel')
                if width==1024 and scale==2:
                    page.screenshot(path=str(OUT/f'{args.engine}-{theme}-1024-text200-more.png'))
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)
                assert not page.locator('.more-menu').evaluate('e=>e.open')
                phone=page.locator('.header-phone')
                phone.hover()
                page.wait_for_timeout(350)
                assert page.locator('.header-contact').evaluate('e=>e.open')
                contact_value=panel_geometry(page,'.header-contact-panel')
                hold_gap(page,'.header-contact','.header-contact-panel')
                assert page.locator('.header-contact-panel a[href^="tel:"]').count()==1
                if width==1024 and scale==2:page.screenshot(path=str(OUT/f'{args.engine}-{theme}-1024-text200-phone.png'))
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)
                hours_value=None
                if page.locator('.header-hours-menu').is_visible():
                    page.locator('.header-hours-menu>summary').hover();page.wait_for_timeout(350)
                    assert page.locator('.header-hours-menu').evaluate('e=>e.open')
                    assert page.locator('.header-hours [data-info-tip]').count()==0
                    hours_value=panel_geometry(page,'.header-hours-menu .header-menu-panel',False)
                    hold_gap(page,'.header-hours-menu','.header-hours-menu .header-menu-panel')
                    styles=page.locator('.header-menu-panel').evaluate_all("es=>es.map(e=>({background:getComputedStyle(e).getPropertyValue('--material-bg').trim(),radius:getComputedStyle(e).borderRadius}))")
                    assert len({str(v)for v in styles})==1,styles
                    if width==1440 and scale==1 and theme=='light':page.screenshot(path=str(OUT/f'{args.engine}-1440-hours.png'))
                    page.keyboard.press('Escape');page.wait_for_timeout(300)
                # Actual sequential keyboard navigation, including focus-open
                # menus. No synthetic click or force bypasses the overlap bug.
                page.mouse.move(width/2,350)
                page.evaluate('document.activeElement.blur()')
                page.keyboard.press('Control+Home')
                page.locator('.header-nav>a').first.focus()
                reached=[]
                for _ in range(35):
                    page.keyboard.press('Tab')
                    active=page.evaluate("""()=>{const e=document.activeElement;return{class:typeof e.className==='string'?e.className:'',text:e.textContent?.trim(),tag:e.tagName,visible:e.getClientRects().length>0}}""")
                    if active['class']=='header-phone':
                        page.wait_for_timeout(300)
                        assert page.locator('.header-contact').evaluate('e=>e.open')
                        reached.append('phone')
                        page.keyboard.press('ArrowDown')
                        assert page.locator('.header-contact-panel').evaluate('e=>e.contains(document.activeElement)')
                        page.keyboard.press('Escape');page.wait_for_timeout(250)
                        assert page.locator('.header-phone').evaluate('e=>document.activeElement===e')
                    elif active['tag']=='SUMMARY' and active['text'].startswith('Ещё'):
                        page.wait_for_timeout(300)
                        assert page.locator('.more-menu').evaluate('e=>e.open')
                        reached.append('more')
                        page.keyboard.press('ArrowDown')
                        assert page.locator('.more-panel').evaluate('e=>e.contains(document.activeElement)')
                        page.keyboard.press('Escape');page.wait_for_timeout(250)
                        assert more.evaluate('e=>document.activeElement===e')
                    elif active['class']=='header-book':
                        reached.append('booking');break
                assert set(reached)=={'more','phone','booking'},reached
                # Native details remain one owner, and internal navigation
                # still focuses the actual section after the taller header.
                more.hover();page.wait_for_timeout(300)
                page.locator('.more-panel a[href="#faq"]').click()
                page.wait_for_timeout(1200)
                anchor=page.locator('#faq').evaluate("""e=>{const h=e.querySelector('h2'),header=document.querySelector('.site-header');return{heading:h.getBoundingClientRect().toJSON(),header:header.getBoundingClientRect().toJSON(),hidden:header.classList.contains('is-hidden'),focused:document.activeElement===h}}""")
                assert anchor['focused'] and (anchor['hidden']or anchor['heading']['y']>=anchor['header']['bottom']-1), anchor
                rows.append({'width':width,'theme':theme,'textScale':scale,'geometry':value,'standardUnchanged':unchanged,'morePanel':more_value,'contactPanel':contact_value,'hoursPanel':hours_value,'keyboard':reached,'anchor':anchor})
                context.close()
                print('case',args.engine,width,theme,scale,'PASS',flush=True)
    # The served static CSS establishes the layout before this component's
    # controller is available. Delaying its actual module must not move links.
    delayed=None
    if args.static:
        context=browser.new_context(viewport={'width':1024,'height':720})
        page=context.new_page();held=[]
        def delay_header(route):
            response=route.fetch();html=response.text()
            pattern=r'<script[^>]*src="([^"]*Header\.[^"]+\.js)"[^>]*></script>'
            matches=re.findall(pattern,html);assert len(matches)==1,matches
            held.extend(matches);route.fulfill(response=response,body=re.sub(pattern,'',html))
        page.route(args.origin,delay_header)
        page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'");page.wait_for_timeout(250)
        assert held, 'actual Header controller was not delayed'
        page.evaluate(SCALE_TEXT);before=page.evaluate(GEOMETRY);check_geometry(before)
        page.add_script_tag(type='module',url=urljoin(args.origin,held[0]));page.wait_for_timeout(300)
        after=page.evaluate(GEOMETRY);check_geometry(after)
        delayed=all(abs(a['rect'][k]-b['rect'][k])<.1 for a,b in zip(before['controls'],after['controls'])for k in ['x','y','width','height'])
        assert delayed, ('controller moved header after first render',before,after)
        context.close()
    # Shared native details controller also works when motion is disabled.
    context=browser.new_context(viewport={'width':1024,'height':720},reduced_motion='reduce')
    page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'");page.wait_for_timeout(250);page.evaluate(SCALE_TEXT);check_geometry(page.evaluate(GEOMETRY));page.locator('.more-menu>summary').hover();page.wait_for_timeout(50);assert page.locator('.more-menu').evaluate('e=>e.open');panel_geometry(page,'.more-panel');page.keyboard.press('Escape');page.wait_for_timeout(50);assert not page.locator('.more-menu').evaluate('e=>e.open');context.close()
    browser.close()
assert not errors,errors
(OUT/f'acceptance-{args.engine}.json').write_text(json.dumps({'origin':args.origin,'engine':args.engine,'cases':rows,'nativeLinkTabbing':native_link_tabbing,'popupKeyboardEntry':'ArrowDown','slowGapHoldMs':350,'reducedMotion':True,'delayedControllerUnchanged':delayed,'errors':errors,'published':False,'physicalDevice':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',args.engine,len(rows),'header geometry, text200, mouse/keyboard, anchor, unchanged1x; reduced motion')
