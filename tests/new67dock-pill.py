"""One logical dock: pill corners, hero transparency, content-safe scroll contraction and promo owner."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','webkit'],default='chromium');parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[\w-]+',args.label)
OUT=ROOT/'tmp/planning/iteration67/dock-pill'/args.label;OUT.mkdir(parents=True,exist_ok=False);host=urlsplit(args.origin).netloc
FILES=['src/components/MobileNav.astro','src/scripts/mobile-nav.ts','src/scripts/dock-surface.ts','src/scripts/dock-actions.ts','src/styles/mobile-nav.css','src/styles/dock-surface.css','src/styles/analytics-choice.css','src/config/design.json','src/config/design.ts','src/config/spring.ts','src/components/Header.astro','src/scripts/floating-tone.ts']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in FILES}
SAMPLE="""()=>{const d=document.querySelector('[data-mobile-nav]'),shell=d.querySelector('.dock-shell'),r=d.getBoundingClientRect(),style=getComputedStyle(d);return{rect:r.toJSON(),shellRect:shell.getBoundingClientRect().toJSON(),section:d.dataset.section,condensed:d.dataset.condensed,stacked:d.dataset.stacked,shells:document.querySelectorAll('.dock-shell').length,background:getComputedStyle(shell).backgroundColor,shadow:getComputedStyle(shell).boxShadow,radius:parseFloat(getComputedStyle(shell).borderTopLeftRadius),transform:style.transform,overflow:document.documentElement.scrollWidth>innerWidth+1,buttons:[...d.querySelectorAll('.dock-toolbar>:is(button,a):not([hidden])')].map(b=>{const r=b.getBoundingClientRect(),s=getComputedStyle(b),label=b.querySelector('span:first-child'),range=document.createRange();range.selectNodeContents(label);const icon=b.hasAttribute('data-icon')||b.hasAttribute('data-open-menu');return{tag:b.tagName,foreground:s.color,skin:getComputedStyle(b.querySelector('.dock-skin')).backgroundColor,font:parseFloat(getComputedStyle(label).fontSize),action:b.dataset.action??'menu',label:label.textContent,accessible:b.getAttribute('aria-label'),rect:r.toJSON(),radius:parseFloat(s.borderTopLeftRadius),padding:parseFloat(s.paddingLeft),textRects:icon?0:range.getClientRects().length,fits:icon||range.getBoundingClientRect().width<=r.width-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1}})}}"""
def assert_controls(s):
 assert s['shells']==1 and not s['overflow'],s
 assert s['radius']>=min(s['rect']['width'],s['rect']['height'])/2-.5,s
 for b in s['buttons']:
  assert b['rect']['width']>=43.9 and b['rect']['height']>=43.9 and b['radius']>=min(b['rect']['width'],b['rect']['height'])/2-.5,b
  assert b['fits']and(b['textRects']==0 or b['textRects']==1 and b['padding']>=12),b
start=hashes();rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if args.engine=='chromium'else{}))
 def fresh(width=390,theme='light',motion='no-preference',modules=True):
  c=browser.new_context(viewport={'width':width,'height':900},color_scheme=theme,reduced_motion=motion)
  c.add_init_script("if(top===window){localStorage.setItem('soyuz.analytics.v1','denied');localStorage.setItem('soyuz_theme',%s)}"%json.dumps(theme))
  c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==host and(modules or r.request.resource_type!='script')else r.abort())
  page=c.new_page();page.on('pageerror',lambda e:errors.append(e.stack or str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_timeout(300);return c,page
 def top(page):page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.condensed==='false'");page.wait_for_timeout(300)
 def sample(page):return page.evaluate(SAMPLE)
 # Delayed modules must start with the promo pair and transparent shell in CSS.
 initialPalette={}
 for theme in['light','dark']:
  c,page=fresh(theme=theme,modules=False);s=sample(page);assert_controls(s);assert s['section']=='top'and[s['action']for s in s['buttons']]==['menu','promo','booking']and'0)'in s['background']and s['shadow']=='none',s
  initialPalette[theme]=[(button['action'],button['skin'],button['foreground'])for button in s['buttons']];rows.append({'case':'initial-without-modules','theme':theme,**s});c.close()
 for theme in ['light','dark']:
  c,page=fresh(theme=theme)
  for width in [320,390,430,600,800,960]:
   page.set_viewport_size({'width':width,'height':900});top(page);before=sample(page);assert_controls(before)
   assert before['section']=='top'and before['shadow']=='none'and'0)'in before['background'],before
   if width==390:assert[(button['action'],button['skin'],button['foreground'])for button in before['buttons']]==initialPalette[theme],(initialPalette[theme],before)
   page.evaluate("scrollTo({top:160,behavior:'instant'})");page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.condensed==='true'");page.wait_for_timeout(300);after=sample(page);assert_controls(after)
   ratio=after['rect']['width']/before['rect']['width'];assert .79<=ratio<=.94 and after['rect']['height']<=before['rect']['height']*.82,(before,after)
   assert after['background']not in['transparent','rgba(0, 0, 0, 0)']and after['shadow']!='none',(before,after)
   assert before['buttons'][1]['font']>=after['buttons'][1]['font'],(before,after)
   assert after['transform']in['none','matrix(1, 0, 0, 1, 0, 0)'],after
   rows.append({'case':'scroll-contract','theme':theme,'width':width,'widthRatio':ratio,'before':before,'after':after})
   if width in[320,390,600]:page.screenshot(path=str(OUT/f'{theme}-{width}-condensed.png'))
   top(page);restored=sample(page);assert abs(restored['rect']['width']-before['rect']['width'])<1 and abs(restored['rect']['height']-before['rect']['height'])<1
  # Only the intended existing promo dialog opens; no booking/provider action.
  page.set_viewport_size({'width':390,'height':900});top(page);page.locator('[data-dock-slot][data-action="promo"]').click();page.locator('#promo-dialog').wait_for(state='visible');assert not page.locator('#booking-drawer').evaluate('e=>e.open');page.keyboard.press('Escape');page.wait_for_timeout(300)
  assert page.locator('[data-dock-slot][data-action="promo"]').evaluate('e=>e===document.activeElement')
  page.locator('[data-open-menu]').click();page.wait_for_timeout(320);assert page.locator('#mobile-menu').evaluate('e=>e.open');page.keyboard.press('Escape');page.wait_for_timeout(320);assert_controls(sample(page));rows.append({'case':'promo-and-menu-same-owner','theme':theme,**sample(page)});c.close()
 # Text enlargement and notch insets are content floors, with one-line short labels and stacking.
 for width in [320,390,600]:
  c,page=fresh(width=width,motion='reduce');page.evaluate("""()=>{document.documentElement.style.setProperty('--safe-left','30px');document.documentElement.style.setProperty('--safe-right','22px');for(const e of document.querySelectorAll('.dock-action>span:first-child'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'}""")
  page.wait_for_timeout(150);assert_controls(sample(page));page.evaluate("scrollTo({top:160,behavior:'instant'})");page.wait_for_timeout(200);s=sample(page);assert_controls(s);rows.append({'case':'text200-safe-area','width':width,**s});page.screenshot(path=str(OUT/f'text200-{width}.png'));c.close()
 # Mid-transition reversal, focus continuity and a changed section settle into one material.
 c,page=fresh();page.mouse.click(5,5);page.locator('[data-dock-slot][data-action="promo"]').focus();page.evaluate("scrollTo({top:160,behavior:'instant'})");page.wait_for_timeout(320);small=sample(page);page.evaluate("()=>{window.growFrames=[];requestAnimationFrame(function frame(){growFrames.push({at:performance.now(),height:document.querySelector('.dock-shell').getBoundingClientRect().height});if(growFrames.length<30)requestAnimationFrame(frame)});scrollTo({top:0,behavior:'instant'})}");page.wait_for_timeout(350);large=sample(page);growth=page.evaluate('growFrames');assert any(small['rect']['height']+1<f['height']<large['rect']['height']-1 for f in growth),(small,large,growth);assert page.locator('[data-dock-slot][data-action="promo"]').evaluate('e=>e===document.activeElement');rows.append({'case':'grow-continuity','small':small,'large':large,'frames':growth});page.evaluate("()=>{window.dockFrames=[];function frame(){dockFrames.push(document.querySelector('.dock-shell').getBoundingClientRect().height);if(dockFrames.length<45)requestAnimationFrame(frame)}requestAnimationFrame(frame)}");page.evaluate("scrollTo({top:160,behavior:'instant'})");page.wait_for_timeout(35);page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_timeout(320);assert_controls(sample(page));assert len({round(h,1)for h in page.evaluate('dockFrames')})>3,'No intermediate shell frames during pointer-mode reversal'
 page.locator('#offers').scroll_into_view_if_needed();page.wait_for_timeout(350);offer=sample(page);assert_controls(offer);assert offer['section']=='offers'and[b['action']for b in offer['buttons']]==['menu','offer-prev','offer-action','offer-next'],offer
 page.locator('[data-dock-slot][data-action="offer-action"]').focus();page.locator('#contacts').scroll_into_view_if_needed();page.wait_for_timeout(350);assert page.locator('[data-open-menu]').evaluate('e=>e===document.activeElement');rows.append({'case':'reverse-and-context-focus','offers':offer,'contacts':sample(page)});c.close();browser.close()
assert not errors,errors
end=hashes();assert start==end,'Dock sources changed during QA'
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'rows':rows,'sourceStart':start,'sourceEnd':end,'pageErrors':errors,'physicalDevice':False,'providerCodeExecuted':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS {args.engine}: {len(rows)} dock groups; pill geometry, transparent hero, logical contraction, promo, 200% and context focus')
