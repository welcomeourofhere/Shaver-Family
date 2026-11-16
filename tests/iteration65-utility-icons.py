"""Inspect real utility controls without creating bookings or enabling analytics."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:4366/');args=parser.parse_args()
out=ROOT/'artifacts/iteration65/utility-icons';out.mkdir(parents=True,exist_ok=True);rows=[]
with sync_playwright() as p:
 for engine in ['chromium','firefox','webkit']:
  browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}))
  for width in [390,1440]:
   for theme in ['light','dark']:
    context=browser.new_context(viewport={'width':width,'height':900},color_scheme=theme,reduced_motion='reduce');context.route('**/*',lambda r:r.continue_()if r.request.url.startswith(args.url)else r.abort());page=context.new_page();page.goto(args.url);page.evaluate('document.fonts.ready');page.locator('#footer').scroll_into_view_if_needed();page.wait_for_timeout(150)
    case=f'{engine}-{width}-{theme}'
    if width<=960:
     page.locator('[data-open-menu]').click();page.wait_for_timeout(100);host=page.locator('#mobile-menu .menu-contact-row');host.scroll_into_view_if_needed()
    else:
     page.locator('[data-site-settings]').focus();page.keyboard.press('Enter');page.wait_for_function("document.querySelector('[data-site-settings]').getAttribute('aria-expanded')==='true'");host=page.locator('#site-settings-panel')
    controls=host.locator('.preference-controls')
    measured=controls.locator('button').evaluate_all("""buttons=>buttons.map(b=>{const r=b.getBoundingClientRect();return{label:b.getAttribute('aria-label'),width:r.width,height:r.height,icons:[...b.querySelectorAll('.utility-icon')].filter(i=>i.getClientRects().length).map(i=>({width:i.getBoundingClientRect().width,height:i.getBoundingClientRect().height,viewBox:i.getAttribute('viewBox')}))}})""")
    assert len(measured)==3
    for button in measured:
     assert button['width']==48 and button['height']==48,button
     assert len(button['icons'])==1,button
     for icon in button['icons']:assert icon['width']==24 and icon['height']==24 and icon['viewBox']=='0 0 24 24',icon
    def shot(state):
     page.wait_for_timeout(100)
     if width<=960:host.screenshot(path=str(out/f'{case}-{state}.png'))
     else:page.screenshot(path=str(out/f'{case}-{state}.png'),clip={'x':8,'y':804,'width':252,'height':88})
    shot('normal')
    controls.locator('[data-analytics-settings]').hover();shot('hover')
    sound=controls.locator('[data-feedback-toggle]');sound.click();page.wait_for_function("document.querySelector('[data-feedback-toggle]').getAttribute('aria-pressed')==='false'");shot('muted');sound.click()
    toggle=controls.locator('[data-theme-toggle]');toggle.focus();page.keyboard.press('Enter');page.wait_for_function('(original)=>document.documentElement.dataset.theme!==original',arg=theme);shot('theme-keyboard');page.keyboard.press('Enter');page.wait_for_function('(original)=>document.documentElement.dataset.theme===original',arg=theme)
    assert controls.locator('[data-feedback-toggle]').get_attribute('aria-pressed')=='true'
    rows.append({'engine':engine,'width':width,'theme':theme,'controls':measured,'hover':True,'muted':True,'keyboardThemeRoundtrip':True});context.close()
  browser.close()
(ROOT/'tmp/planning/iteration65/utility-icons.json').write_text(json.dumps({'rows':rows,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(rows),'utility contexts, normal/hover/muted/keyboard-theme states')
