"""Bounded platform checks. HMR is developmental evidence, not release/Safari acceptance."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--origin', default='http://127.0.0.1:4321/')
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--label', required=True)
parser.add_argument('--checks', choices=['bootstrap', 'all'], default='all')
parser.add_argument('--anchor-fixture', action='store_true', help='Exercise the production feature-query body explicitly; not evidence of iOS feature support')
args = parser.parse_args()
out = ROOT / 'tmp/planning/iteration66/mobile-platform' / args.label / args.engine
out.mkdir(parents=True, exist_ok=False)
results = []
allowed = urlsplit(args.origin).netloc


def check(name, condition, details=None):
    results.append({'name': name, 'pass': bool(condition), 'details': details})


def route_local(route):
    if urlsplit(route.request.url).netloc == allowed:
        route.continue_()
    else:
        route.abort()


def snapshot(page):
    return page.evaluate("""() => {
      const root=document.documentElement, css=getComputedStyle(root);
      return {theme:root.dataset.theme, color:document.querySelector('meta[name="theme-color"]').content,
        surface:css.getPropertyValue('--surface').trim(),scheme:document.querySelector('meta[name="color-scheme"]')?.content,
        viewport:document.querySelector('meta[name="viewport"]').content,
        overflow:root.scrollWidth>root.clientWidth+1};
    }""")


with sync_playwright() as playwright:
    browser = getattr(playwright, args.engine).launch(headless=True, **({'channel': 'chrome'} if args.engine == 'chromium' else {}))
    try:
        for os_theme, saved, expected in [('dark', None, 'dark'), ('light', None, 'light'),
                                         ('dark', 'broken', 'dark'), ('dark', 'light', 'light'),
                                         ('light', 'dark', 'dark')]:
            context = browser.new_context(viewport={'width': 390, 'height': 844}, color_scheme=os_theme)
            context.route('**/*', lambda route: route.abort() if route.request.resource_type == 'script' else route_local(route))
            if saved is not None:
                context.add_init_script(f"localStorage.setItem('soyuz_theme',{json.dumps(saved)});")
            page = context.new_page()
            page.goto(args.origin, wait_until='domcontentloaded')
            data = snapshot(page)
            check(f'early-theme-{os_theme}-{saved}', data['theme'] == expected and data['color'] == data['surface'], data)
            check(f'zoom-and-scheme-{os_theme}-{saved}', data['scheme'] == 'light dark' and 'viewport-fit=cover' in data['viewport'] and 'user-scalable=no' not in data['viewport'] and 'maximum-scale=1' not in data['viewport'], data)
            context.close()

        if args.checks == 'all':
            context = browser.new_context(viewport={'width': 390, 'height': 844}, color_scheme='dark', reduced_motion='reduce')
            context.route('**/*', route_local)
            page = context.new_page()
            page.goto(args.origin, wait_until='networkidle')
            if args.anchor_fixture:
                # Use the loaded build's selectors, including native-export specificity guards.
                body=page.evaluate("""() => {
                  const bodies=[];
                  const walk=rules=>{for(const rule of rules){
                    if(rule instanceof CSSSupportsRule&&rule.conditionText.replace(/\\s/g,'')==='(-webkit-touch-callout:none)')
                      bodies.push([...rule.cssRules].map(child=>child.cssText).join('\\n'));
                    else if(rule.cssRules)walk(rule.cssRules);
                  }};
                  for(const sheet of document.styleSheets)walk(sheet.cssRules);
                  return bodies.join('\\n');
                }""")
                assert body,'Missing production point-anchor feature rule'
                page.add_style_tag(content=body)
            page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
            page.emulate_media(color_scheme='light')
            page.wait_for_function("document.documentElement.dataset.theme==='light'")
            check('runtime-auto-os-change', snapshot(page)['theme'] == 'light')
            for cycle in range(3):
                page.locator('[data-mobile-nav] [data-open-menu]').click()
                page.wait_for_function("document.querySelector('#mobile-menu').open")
                data = page.evaluate("""() => {
                  const nav=document.querySelector('[data-mobile-nav]'), a=nav.closest('[data-mobile-nav-anchor]'),r=nav.getBoundingClientRect();
                  return {one:document.querySelectorAll('[data-mobile-nav]').length,anchorInDialog:a.parentElement.id==='mobile-menu',
                    width:r.width,left:r.left,right:r.right,supports:CSS.supports('-webkit-touch-callout','none'),
                    position:getComputedStyle(nav).position,anchorPosition:getComputedStyle(a).position,
                    anchorWidth:a.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
                }""")
                check(f'dock-dialog-owner-{cycle}', data['one'] == 1 and data['anchorInDialog'] and data['left'] >= 3 and data['right'] <= 391 and not data['overflow'], data)
                check(f'dock-feature-anchor-{cycle}', (data['position'] == 'absolute' and data['anchorPosition'] == 'fixed' and data['anchorWidth'] == 0) if data['supports'] or args.anchor_fixture else data['position'] == 'fixed', data)
                if cycle == 0:
                    page.locator('#mobile-menu [data-theme-toggle]').click()
                    page.wait_for_function("document.documentElement.dataset.theme==='dark'")
                    page.emulate_media(color_scheme='dark')
                    page.emulate_media(color_scheme='light')
                    check('runtime-manual-persists-os', snapshot(page)['theme'] == 'dark' and snapshot(page)['color'] == snapshot(page)['surface'], snapshot(page))
                    page.screenshot(path=str(out / 'mobile-menu.png'))
                page.keyboard.press('Escape')
                page.wait_for_function("!document.querySelector('#mobile-menu').open")
                check(f'dock-return-{cycle}', page.evaluate("!document.querySelector('#mobile-menu').contains(document.querySelector('[data-mobile-nav-anchor]'))"))
            page.evaluate("localStorage.clear();dispatchEvent(new StorageEvent('storage',{key:null}))")
            page.wait_for_function("document.documentElement.dataset.theme==='light'")
            check('runtime-clear-restores-auto', snapshot(page)['theme'] == 'light')

            for width in [390, 600, 720, 760, 800, 960, 961, 1100, 1440]:
                for theme in ['light', 'dark']:
                    page.set_viewport_size({'width': width, 'height': 900})
                    page.evaluate("theme=>{localStorage.setItem('soyuz_theme',theme);dispatchEvent(new StorageEvent('storage',{key:'soyuz_theme',newValue:theme}))}", theme)
                    page.locator('#contacts').scroll_into_view_if_needed()
                    page.wait_for_timeout(80)
                    data = page.evaluate("""() => {
                      const el=s=>document.querySelector(s),r=s=>{const b=el(s).getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom}};
                      return {available:el('#contacts').clientWidth,map:r('.contact-map'),business:r('.contact-visit'),
                        people:[...document.querySelectorAll('.contact-person')].map(el=>{const b=el.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,right:b.right,bottom:b.bottom}}),
                        overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
                        textClips:[...document.querySelectorAll('.contact-visit .btn,.contact-person-copy a')].filter(el=>el.scrollWidth>el.clientWidth+1).map(el=>el.textContent)};
                    }""")
                    side_by_side = abs(data['map']['y'] - data['business']['y']) <= 1 and data['map']['right'] <= data['business']['x']
                    compact = data['business']['y'] >= data['map']['bottom']
                    people_stacked = abs(data['people'][0]['x']-data['business']['x'])<=1 and data['people'][0]['y']>=data['business']['bottom'] and data['people'][1]['y']>=data['people'][0]['bottom']
                    map_full_height = abs(data['map']['bottom']-data['people'][1]['bottom'])<=1
                    check(f'contacts-layout-{width}-{theme}', not data['overflow'] and not data['textClips'] and (compact if data['available'] < 700 else side_by_side and people_stacked and map_full_height), data)
                    if width in [390, 800, 1440] and theme == 'dark':
                        page.screenshot(path=str(out / f'contacts-{width}.png'))

            page.set_viewport_size({'width': 800, 'height': 900})
            page.evaluate("""() => {
              const nodes=[...document.querySelectorAll('.contact-person-copy *,.contact-visit *')]
                .filter(node=>[...node.childNodes].some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim()))
                .map(node=>[node,parseFloat(getComputedStyle(node).fontSize)]);
              for(const [node,size] of nodes)node.style.fontSize=`${size*2}px`;
            }""")
            page.wait_for_timeout(150)
            check('contacts-200-percent-text', not snapshot(page)['overflow'], page.evaluate("""({root:document.documentElement.scrollWidth,width:document.documentElement.clientWidth,
              clips:[...document.querySelectorAll('.contact-layout *')].filter(el=>el.clientWidth&&el.scrollWidth>el.clientWidth+1).map(el=>({tag:el.tagName,class:el.className,width:el.clientWidth,scroll:el.scrollWidth,text:el.textContent?.slice(0,100)}))})"""))
            page.screenshot(path=str(out / 'contacts-800-text200.png'))
            context.close()

            if args.engine != 'firefox':
                context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
                context.route('**/*', route_local)
                page = context.new_page()
                page.goto(args.origin, wait_until='networkidle')
                page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'")
                page.locator('[data-mobile-nav] [data-open-menu]').tap()
                page.wait_for_function("document.querySelector('#mobile-menu').open")
                check('touch-menu-opens', page.locator('#mobile-menu').evaluate('el=>el.open'))
                page.locator('[data-mobile-nav] [data-open-menu]').tap()
                page.wait_for_function("!document.querySelector('#mobile-menu').open")
                check('touch-menu-closes', not page.locator('#mobile-menu').evaluate('el=>el.open'))
                context.close()

            for motion in ['no-preference', 'reduce']:
                for width in [390, 1440]:
                    context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion=motion)
                    context.route('**/*', route_local)
                    page = context.new_page()
                    page.goto(args.origin, wait_until='networkidle')
                    page.wait_for_function("document.querySelector('.contact-layout')?.dataset.revealMode==='fade'")
                    data = page.evaluate("""() => {
                      const el=document.querySelector('.contact-layout'),r=el.getBoundingClientRect();
                      return{pending:el.dataset.revealPending,top:r.top,height:r.height,margin:getComputedStyle(document.documentElement).getPropertyValue('--reveal-margin').trim()};
                    }""")
                    # Move naturally into the reveal threshold. No anchor/focus bypass.
                    page.evaluate("top=>scrollTo({top:top-innerHeight+110,behavior:'instant'})", data['top'])
                    page.wait_for_function("document.querySelector('.contact-layout').dataset.revealed==='true'")
                    measured = page.evaluate("""() => {
                      const el=document.querySelector('.contact-layout'),a=el.getAnimations()[0],r=el.getBoundingClientRect();
                      return{height:r.height,opacity:getComputedStyle(el).opacity,animation:!!a,
                        duration:a?.effect.getTiming().duration,frames:a?.effect.getKeyframes().map(f=>f.opacity),
                        pending:el.hasAttribute('data-reveal-pending')};
                    }""")
                    check(f'reveal-{width}-{motion}', abs(data['height']-measured['height']) <= 1 and not measured['pending'] and (not measured['animation'] if motion == 'reduce' else measured['animation'] and measured['frames'][0] == '0.2' and measured['duration'] == 360), {'before': data, 'after': measured})
                    page.wait_for_timeout(450)
                    check(f'reveal-finished-{width}-{motion}', page.locator('.contact-layout').evaluate("el=>getComputedStyle(el).opacity==='1'"))
                    context.close()
    finally:
        browser.close()

(out / 'results.json').write_text(json.dumps({'origin': args.origin, 'engine': args.engine, 'anchorFixture': args.anchor_fixture, 'boundary': 'Isolated browser engine, external requests blocked. Optional CSS feature-body fixture is explicit. Not a physical phone or public release.', 'checks': results}, ensure_ascii=False, indent=2), encoding='utf-8')
failures = [row for row in results if not row['pass']]
print(json.dumps({'passed': len(results)-len(failures), 'failed': len(failures), 'failures': failures, 'results': str(out / 'results.json')}, ensure_ascii=False))
raise SystemExit(bool(failures))
