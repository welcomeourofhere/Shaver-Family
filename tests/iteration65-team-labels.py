"""Verify team actions, centred discovery labels and their single keyboard owner."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:4321/')
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
args = parser.parse_args()
out = ROOT / 'artifacts/iteration65/team-labels'
out.mkdir(parents=True, exist_ok=True)
news = (ROOT / 'public/data/news.json').read_text(encoding='utf-8')
rows = []

def resource(route):
    url = route.request.url
    if url.endswith('/data/news.json'):
        route.fulfill(status=200, content_type='application/json', body=news, headers={'Access-Control-Allow-Origin': '*'})
    elif url.startswith(args.url):
        route.continue_()
    else:
        route.abort()

with sync_playwright() as p:
    browser = getattr(p, args.engine).launch(**({'channel': 'chrome'} if args.engine == 'chromium' else {}))
    for width in [320, 390, 600, 768, 960, 961, 1024, 1100, 1200, 1440]:
        for theme in ['light', 'dark']:
            context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=theme, reduced_motion='reduce')
            context.route('**/*', resource)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(args.url, wait_until='domcontentloaded')
            page.evaluate('document.fonts.ready')
            page.locator('#masters').scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            for scale in [1, 2]:
                if scale == 2:
                    page.evaluate("""() => {
                      const nodes=[...document.querySelectorAll('body *')].filter(e=>!e.matches('script,style,svg,svg *')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));
                      const sizes=nodes.map(e=>parseFloat(getComputedStyle(e).fontSize));
                      nodes.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px');
                    }""")
                page.wait_for_timeout(500)
                measured = page.locator('.team-card .team-book').evaluate_all("""buttons=>buttons.map(b=>{
                  const label=b.querySelector('[data-action-label]'),style=getComputedStyle(b),r=b.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(label);
                  const text=range.getBoundingClientRect(),rects=[...range.getClientRects()];
                  return {master:b.dataset.master,label:label.textContent,accessible:b.getAttribute('aria-label'),width:r.width,height:r.height,font:getComputedStyle(label).fontSize,paddingLeft:parseFloat(style.paddingLeft),paddingRight:parseFloat(style.paddingRight),lines:rects.length,textWidth:text.width,available:r.width-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight),inside:text.left>=r.left+parseFloat(style.paddingLeft)-.6&&text.right<=r.right-parseFloat(style.paddingRight)+.6,scrollWidth:b.scrollWidth,clientWidth:b.clientWidth};
                })""")
                assert len(measured) == 6
                for item in measured:
                    assert item['label'].replace('\u00a0', ' ') in ['Записаться', 'Записаться к мастеру'], item
                    assert item['accessible'].startswith('Записаться к мастеру: '), item
                    assert item['inside'] and item['lines'] == 1, (width, theme, scale, item)
                    assert item['paddingLeft'] >= 12 and item['paddingRight'] >= 12 and item['height'] >= 44, item
                    assert item['scrollWidth'] <= item['clientWidth'] + 1, item
                discovery = page.locator('.team-card').evaluate_all("""cards=>cards.map(card=>{
                  const button=card.querySelector('.team-portrait'),label=card.querySelector('.team-discover'),b=button.getBoundingClientRect(),r=label.getBoundingClientRect(),style=getComputedStyle(label),range=document.createRange();range.selectNodeContents(label);const text=range.getBoundingClientRect();
                  return {name:card.querySelector('.team-name').textContent,accessible:button.getAttribute('aria-label'),label:label.textContent,centerError:Math.abs((r.left+r.right-b.left-b.right)/2),width:r.width,portraitWidth:b.width,height:r.height,paddingLeft:parseFloat(style.paddingLeft),paddingRight:parseFloat(style.paddingRight),lines:range.getClientRects().length,inside:text.left>=r.left+parseFloat(style.paddingLeft)-.6&&text.right<=r.right-parseFloat(style.paddingRight)+.6,owners:card.querySelectorAll('button[data-team-open]').length,spanHidden:label.getAttribute('aria-hidden'),spanTabIndex:label.tabIndex};
                })""")
                for item in discovery:
                    assert item['label'] == 'Знакомство' and item['accessible'] == 'Знакомство: '+item['name'], item
                    assert item['centerError'] <= .6 and item['width'] < item['portraitWidth'] * .9, (width, theme, scale, item)
                    assert item['inside'] and item['lines'] == 1, (width, theme, scale, item)
                    assert item['paddingLeft'] == 20 and item['paddingRight'] == 20 and item['height'] >= 44, item
                    assert item['owners'] == 1 and item['spanHidden'] == 'true' and item['spanTabIndex'] == -1, item
                if width in [320, 1440] and scale == 1:
                    for i in range(6):
                        card = page.locator('.team-card').nth(i)
                        portrait = card.locator('.team-portrait')
                        portrait.focus()
                        page.wait_for_timeout(100)
                        page.keyboard.press('Tab')
                        page.wait_for_function('(selector)=>document.querySelector(selector)===document.activeElement', arg=f'.team-card:nth-child({i+1}) .team-book')
                        page.keyboard.press('Shift+Tab')
                        page.wait_for_function('(selector)=>document.querySelector(selector)===document.activeElement', arg=f'.team-card:nth-child({i+1}) .team-portrait')
                        page.keyboard.press('Enter')
                        dialog = page.locator('#'+portrait.get_attribute('aria-controls'))
                        page.wait_for_function('(id)=>document.getElementById(id).open', arg=dialog.get_attribute('id'))
                        page.keyboard.press('Escape')
                        page.wait_for_function('(id)=>!document.getElementById(id).open', arg=dialog.get_attribute('id'))
                        page.wait_for_timeout(100)
                        card.locator('.team-discover').click()
                        page.wait_for_function('(id)=>document.getElementById(id).open', arg=dialog.get_attribute('id'))
                        page.keyboard.press('Escape')
                        page.wait_for_function('(id)=>!document.getElementById(id).open', arg=dialog.get_attribute('id'))
                        page.wait_for_timeout(100)
                assert not errors, errors
                rows.append({'engine':args.engine,'width':width,'theme':theme,'textScale':scale,'buttons':measured,'discovery':discovery,'keyboardAndLabelClick':width in [320,1440] and scale==1})
                if width in [320, 1024, 1440]:
                    target = '.team-card:first-child .team-book' if scale == 2 else '.team-card:first-child .team-discover'
                    page.locator('.team-portrait').first.focus()
                    page.locator(target).evaluate("e=>scrollTo({top:e.getBoundingClientRect().top+scrollY-280,behavior:'instant'})")
                    page.screenshot(path=str(out / f'{args.engine}-{width}-{theme}-{scale}.png'))
            context.close()
    browser.close()
(ROOT / f'tmp/planning/iteration65/team-labels-{args.engine}.json').write_text(json.dumps({'rows':rows,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {len(rows)} cases; {len(rows)*12} team action labels; 24 keyboard/label-click journeys; {args.engine}')
