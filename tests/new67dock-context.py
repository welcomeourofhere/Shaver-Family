"""Compiled dock: real palette/skins/hit targets, Works SSOT, native route and menu content."""
import argparse
import hashlib
import json
import math
import re
import traceback
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--origin',required=True)
parser.add_argument('--engine',choices=['chromium','firefox','webkit'],required=True)
parser.add_argument('--channel',choices=['chrome','msedge'],default='chrome',help='Installed Chromium browser; ignored for other engines')
parser.add_argument('--scope',choices=['full','motion'],default='full')
parser.add_argument('--label',required=True)
args=parser.parse_args();assert re.fullmatch(r'[\w-]+',args.label)
OUT=ROOT/'tmp/planning/iteration67/dock-context'/args.label;OUT.mkdir(parents=True,exist_ok=False)
host=urlsplit(args.origin).netloc
first_visit=next(offer for offer in json.loads((ROOT/'content/offers.json').read_text(encoding='utf-8'))['offers']if offer['id']=='first-visit')
promo=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))['promo']
def normal(value):return' '.join(value.split())
FILES=['src/scripts/dock-surface.ts','src/scripts/mobile-nav.ts','src/scripts/dock-actions.ts','src/scripts/floating-tone.ts','src/components/MobileNav.astro','src/components/Header.astro','src/config/design.ts','src/config/design.json','src/config/spring.ts','src/styles/mobile-nav.css','src/styles/dock-surface.css']
def hashes():return{file:hashlib.sha256((ROOT/file).read_bytes()).hexdigest()for file in FILES}
def channels(value):return list(map(float,re.findall(r'[\d.]+',value)))[:3]
def contrast(a,b):
 def luminance(value):
  rgb=[v/255 for v in channels(value)];return sum((v/12.92 if v<=.04045 else((v+.055)/1.055)**2.4)*w for v,w in zip(rgb,[.2126,.7152,.0722]))
 x,y=luminance(a),luminance(b);return(max(x,y)+.05)/(min(x,y)+.05)
SAMPLE="""()=>{const dock=document.querySelector('[data-mobile-nav]'),shell=dock.querySelector('.dock-shell'),toolbar=dock.querySelector('.dock-toolbar');return{section:dock.dataset.section,condensed:dock.dataset.condensed,tone:dock.dataset.floatingTone,actionTone:toolbar.dataset.selectionSurface,plate:getComputedStyle(shell).backgroundColor,rect:dock.getBoundingClientRect().toJSON(),overflow:document.documentElement.scrollWidth>innerWidth+1,buttons:[...toolbar.querySelectorAll(':scope>:is(button,a):not([hidden])')].map(button=>{const label=button.querySelector('span:first-child'),skin=button.querySelector('.dock-skin'),style=getComputedStyle(button),range=document.createRange();range.selectNodeContents(label);return{action:button.dataset.action||'menu',primary:button.hasAttribute('data-dock-primary'),tag:button.tagName,label:label.textContent,accessible:button.getAttribute('aria-label'),disabled:!!button.disabled,rect:button.getBoundingClientRect().toJSON(),background:getComputedStyle(skin).backgroundColor,foreground:style.color,skinTransform:getComputedStyle(skin).transform,font:parseFloat(getComputedStyle(label).fontSize),outline:{color:style.outlineColor,width:parseFloat(style.outlineWidth),style:style.outlineStyle},icon:button.hasAttribute('data-icon')||button.hasAttribute('data-open-menu'),padding:parseFloat(style.paddingLeft),lines:range.getClientRects().length,fits:range.getBoundingClientRect().width<=button.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)+1,href:button.href,target:button.target,rel:button.rel,popup:button.getAttribute('aria-haspopup'),controls:button.getAttribute('aria-controls')}})}}"""
def controls(sample):
 assert not sample['overflow'],sample
 for button in sample['buttons']:
  assert button['rect']['width']>=43.9 and button['rect']['height']>=43.9,button
  if not button['icon']:assert button['padding']>=12 and button['lines']==1 and button['fits'],button
  if not button['disabled']:assert contrast(button['background'],button['foreground'])>=4.5,button

report={'engine':args.engine,'channel':args.channel if args.engine=='chromium'else None,'selection':args.scope,'origin':args.origin,'sourceStart':hashes(),'pageErrors':[],'externalRequests':[],'palette':[],'functional':[],'motion':[],'findings':[],
        'scope':'Compiled UI with feedback preference muted for visual isolation; providers aborted, no booking submission/GPS/hardware or publication claim'}
def save():(OUT/f'{args.engine}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def failure(name,error):report['findings'].append({'kind':'case-failed','case':name,'error':str(error),'traceback':traceback.format_exc()});save()
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':args.channel,'args':['--mute-audio']}if args.engine=='chromium'else{}));report['browserVersion']=browser.version
 def fresh(theme='light',width=390,motion='no-preference'):
  context=browser.new_context(viewport={'width':width,'height':900},color_scheme=theme,reduced_motion=motion)
  context.add_init_script("""if(top===window){try{const now=Date.now();localStorage.setItem('soyuz.analytics.v2',JSON.stringify({version:2,notice:'2026-11-16',updatedAt:now,expiresAt:now+180*86400000,metrika:false,ga4:false}));localStorage.setItem('soyuz_feedback_enabled','false');localStorage.setItem('soyuz_theme',%s);window.__dockFixtureStorage={ok:true}}catch(error){window.__dockFixtureStorage={ok:false,error:String(error)}}}"""%json.dumps(theme))
  def route(r):
   if urlsplit(r.request.url).netloc==host:r.continue_()
   else:report['externalRequests'].append(r.request.url);r.abort()
  context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(e.stack or str(e)));page.goto(args.origin,wait_until='domcontentloaded');storage=page.evaluate("()=>({marker:window.__dockFixtureStorage,analytics:JSON.parse(localStorage.getItem('soyuz.analytics.v2')),feedback:localStorage.getItem('soyuz_feedback_enabled'),theme:localStorage.getItem('soyuz_theme')})");assert storage['marker']=={'ok':True}and storage['feedback']=='false'and storage['theme']==theme and storage['analytics']['version']==2 and storage['analytics']['metrika']is False and storage['analytics']['ga4']is False and storage['analytics']['expiresAt']-storage['analytics']['updatedAt']==180*86400000,storage;page.wait_for_function("document.querySelector('.dock-toolbar').style.gridTemplateColumns!==''");page.wait_for_function("document.fonts.status==='loaded'");page.wait_for_timeout(200);return context,page
 def sample(page):return page.evaluate(SAMPLE)
 def section(page,identifier):
  page.evaluate("id=>document.getElementById(id).scrollIntoView({block:'start',behavior:'instant'})",identifier)
  page.wait_for_function('id=>document.querySelector("[data-mobile-nav]").dataset.section===id',arg=identifier);page.wait_for_timeout(260)
 for theme in (['light','dark']if args.scope=='full'else[]):
  context,page=fresh(theme)
  pairs=set()
  for identifier in ['top','services','masters','works','about','offers','reviews','faq','contacts','footer']:
   try:
    if identifier=='top':page.evaluate("scrollTo({top:160,behavior:'instant'})");page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.condensed==='true'");page.wait_for_timeout(260)
    else:section(page,identifier)
    page.mouse.move(2,2);page.evaluate('document.activeElement.blur()');base=sample(page);controls(base)
    assert base['plate']not in['transparent','rgba(0, 0, 0, 0)'],base
    primary=next(b for b in base['buttons']if b['primary']);secondary=next(b for b in base['buttons']if not b['primary']and b['action']!='menu')if len(base['buttons'])>2 else base['buttons'][0]
    assert channels(primary['background'])!=channels(secondary['background'])and all(channels(b['background'])!=channels(base['plate'])for b in base['buttons']),base
    pairs.add((base['tone'],primary['background'],secondary['background']))
    states=[]
    for role,selector in [('primary','[data-dock-primary]:not([hidden]):not(:disabled)'),('secondary','[data-dock-secondary]:not([hidden]):not(:disabled)')]:
     target=page.locator('.dock-toolbar').locator(selector).first
     if not target.count():continue
     target.hover();hover=sample(page);controls(hover);active=next(b for b in hover['buttons']if b['action']==target.get_attribute('data-action'))
     assert channels(active['background'])!=channels(base['plate']),active
     page.mouse.move(2,2);action=target.get_attribute('data-action');target.evaluate("e=>{const enabled=[...e.parentElement.children].filter(b=>b.matches('button,a')&&!b.hidden&&!b.disabled&&b.getClientRects().length),index=enabled.indexOf(e);if(index<1)throw Error('No preceding dock control for real Tab focus');enabled[index-1].focus({preventScroll:true})}");page.keyboard.press('Tab');native_tab=page.evaluate("()=>({tag:document.activeElement.tagName,action:document.activeElement.dataset.action||'menu'})");focus_method='native-tab'
     if target.evaluate("e=>e.tagName==='A'&&e!==document.activeElement"):
      # The port's native Tab preference can skip links. Inherit the real keyboard
      # modality from its focused button; still require actual :focus-visible.
      target.evaluate('e=>e.focus({preventScroll:true})');focus_method='native-tab-then-anchor-focus'
     focus=sample(page);controls(focus);focused=next(b for b in focus['buttons']if b['action']==action)
     assert target.evaluate('e=>e.matches(":focus-visible")')and focused['outline']['width']>=2 and focused['outline']['style']!='none',focused
     ring=contrast(focused['outline']['color'],focus['plate'])
     if ring<3:report['findings'].append({'kind':'focus-ring-contrast','theme':theme,'section':identifier,'role':role,'ratio':ring,'ring':focused['outline']['color'],'plate':focus['plate']})
     states.append({'role':role,'hover':hover,'focus':focus,'focusMethod':focus_method,'nativeTab':native_tab});page.evaluate('document.activeElement.blur()')
    report['palette'].append({'theme':theme,'requestedSection':identifier,'base':base,'states':states});save()
   except Exception as error:failure(f'palette-{theme}-{identifier}',error)
  if len({tone for tone,_,_ in pairs})<3 or len({(a,b)for _,a,b in pairs})<3:report['findings'].append({'kind':'insufficient-palette-variation','theme':theme,'pairs':list(pairs)})
  # Native route remains an actual link, with native popup/default and no drawer/GPS work.
  try:
   section(page,'contacts');route=page.locator('[data-dock-map-route]');href=route.get_attribute('href')
   assert[b['action']for b in sample(page)['buttons']]==['menu','map-route','booking']
   assert href=='https://yandex.ru/maps/?rtext=~58.588674%2C49.669973'and route.get_attribute('target')=='_blank'and'noopener'in route.get_attribute('rel').split()and route.get_attribute('aria-haspopup')is None
   before=len(report['externalRequests'])
   with page.expect_popup()as opened:route.click()
   popup=opened.value;page.wait_for_timeout(120);popup.close()
   assert href in report['externalRequests'][before:]and not page.locator('#booking-drawer').evaluate('e=>e.open')
   report['functional'].append({'theme':theme,'case':'native-route','href':href,'nativePopup':True,'bookingOpened':False})
  except Exception as error:failure(f'route-{theme}',error)
  finally:context.close()
  context,page=fresh(theme)
  # The one selected work and its canonical team link supply both arrows and booking.
  try:
   section(page,'works');fan=page.locator('.works-fan');before=fan.get_attribute('data-work-index')
   assert[b['action']for b in sample(page)['buttons']]==['menu','work-prev','work-booking','work-next']
   page.locator('[data-dock-slot][data-action="work-next"]').click();page.wait_for_function('previous=>document.querySelector(".works-fan").dataset.workIndex!==previous',arg=before);page.wait_for_function("document.querySelector('.works-fan').dataset.workMoving!=='true'")
   canonical=page.evaluate("()=>{const selected=document.querySelector('[data-work-card][data-work-current=\"true\"]'),link=[...document.querySelectorAll('.team-book[data-master]')].find(e=>e.dataset.master===selected.dataset.workMasterId);return{master:selected.dataset.workMasterId,booking:link.dataset.bookingUrl,accessible:link.getAttribute('aria-label')}}")
   booking=page.locator('[data-dock-slot][data-action="work-booking"]');assert booking.get_attribute('aria-label')==canonical['accessible']
   u=urlsplit(canonical['booking']);match=re.fullmatch(r'[nb](\d+)\.yclients\.(ru|com)',u.netloc);assert match
   expected=urlunsplit((u.scheme,'b'+match[1]+'.yclients.ru',u.path,u.query,u.fragment))
   booking.click();page.locator('#booking-drawer').wait_for(state='visible');assert page.locator('#booking-drawer').get_attribute('data-booking-url')==expected
   page.keyboard.press('Escape');page.wait_for_timeout(160)
   report['functional'].append({'theme':theme,'case':'works-native-owner','beforeIndex':before,'afterIndex':fan.get_attribute('data-work-index'),'selectedMaster':canonical['master'],'canonicalWidget':expected,'providerCodeExecuted':False})
  except Exception as error:failure(f'works-{theme}',error)
  finally:context.close()
  context,page=fresh(theme)
  # Menu title is still the accessible label, without a visible brand heading.
  try:
   section(page,'about');page.locator('[data-open-menu]').click();page.wait_for_timeout(320)
   menu=page.evaluate("()=>{const title=document.querySelector('#menu-title'),business=document.querySelector('.dock-content .menu-business'),phone=business.querySelector('a'),hours=business.querySelector(':scope>span'),r=e=>e.getBoundingClientRect();return{labelledby:document.querySelector('#mobile-menu').getAttribute('aria-labelledby'),title:{text:title.textContent,width:r(title).width,height:r(title).height,clip:getComputedStyle(title).clipPath},phoneCenter:(r(phone).left+r(phone).right)/2,hoursCenter:(r(hours).left+r(hours).right)/2,center:(r(business).left+r(business).right)/2,hoursText:hours.textContent}}")
   assert not re.search('ежедневно',menu['hoursText'],re.I),menu
   assert menu['labelledby']=='menu-title'and menu['title']['text'].strip()and menu['title']['width']<=1.1 and menu['title']['height']<=1.1 and abs(menu['phoneCenter']-menu['center'])<1 and abs(menu['hoursCenter']-menu['center'])<1,menu
   report['functional'].append({'theme':theme,'case':'menu-content',**menu});page.screenshot(path=str(OUT/f'{theme}-menu.png'));page.keyboard.press('Escape')
  except Exception as error:failure(f'menu-{theme}',error)
  finally:context.close()
  context,page=fresh(theme)
  try:
   assert page.locator('#promo-dialog [data-copy-promo]').text_content()==promo,'The code must already exist in SSR markup'
   page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.section==='top'&&document.querySelector('[data-mobile-nav]').dataset.condensed==='false'");page.locator('[data-dock-slot][data-action="promo"]').click();page.locator('#promo-dialog').wait_for(state='visible')
   paragraphs=page.locator('#promo-dialog p').all_text_contents();assert normal(first_visit['description'])in[normal(text)for text in paragraphs]and normal(first_visit['note'])in[normal(text)for text in paragraphs],paragraphs
   report['functional'].append({'theme':theme,'case':'canonical-promo-details','description':first_visit['description'],'note':first_visit['note'],'ssrCode':promo});page.keyboard.press('Escape')
  except Exception as error:failure(f'promo-{theme}',error)
  finally:context.close()
 # Real animation samples verify painted objects strain while all actual controls retain their target floor.
 try:
  context,page=fresh();page.mouse.click(2,2)
  page.evaluate("""()=>{
   window.materialFrames=[];window.materialReversalAt=null;window.materialTransitions=[];
   const dock=document.querySelector('[data-mobile-nav]'),menu=dock.querySelector('.dock-menu');
   const nativeRAF=window.requestAnimationFrame.bind(window);
   window.requestAnimationFrame=callback=>nativeRAF(time=>{
    const from=dock.dataset.condensed,before=menu.getBoundingClientRect().toJSON();
    callback(time);
    if(from!==dock.dataset.condensed)materialTransitions.push({at:performance.now(),from,to:dock.dataset.condensed,before,after:menu.getBoundingClientRect().toJSON()});
   });
   const start=performance.now();scrollTo({top:160,behavior:'instant'});
   requestAnimationFrame(function tick(){
    const frame={at:performance.now(),section:dock.dataset.section,condensed:dock.dataset.condensed,buttons:[...dock.querySelectorAll('.dock-toolbar>:is(button,a):not([hidden])')].map(b=>{
     const r=b.getBoundingClientRect(),m=new DOMMatrix(getComputedStyle(b.querySelector('.dock-skin')).transform==='none'?undefined:getComputedStyle(b.querySelector('.dock-skin')).transform);
     return{action:b.dataset.action||'menu',width:r.width,height:r.height,x:m.a,y:m.d};
    })};materialFrames.push(frame);
    if(materialReversalAt===null&&frame.condensed==='true'&&frame.buttons[0].height>44.1&&frame.buttons[0].height<55){materialReversalAt=frame.at;scrollTo({top:0,behavior:'instant'})}
    if(performance.now()<start+700)requestAnimationFrame(tick);
   });
  }""");page.wait_for_timeout(800)
  frames=page.evaluate('materialFrames');report['resizeMotionFrames']=frames;save();assert all(b['width']>=43.9 and b['height']>=43.9 for frame in frames for b in frame['buttons']),frames
  reversal=page.evaluate('materialReversalAt');peak=any(abs(b['x']-1)>.015 and abs(b['y']-1)>.025 for frame in frames for b in frame['buttons']);report['peakSampling']={'legacyThreshold':{'x':.015,'y':.025},'observed':peak,'scope':'Observation only; required motion contract is real size change, painted strain, interrupted continuity, stable endpoint and hit floor'}
  assert reversal is not None and any(b['x']<.999 and b['y']>1.001 for frame in frames for b in frame['buttons']),'No intermediate resized hit target and positive painted strain were observed'
  transitions=page.evaluate('materialTransitions');report['geometryTransitions']=transitions;save();retarget=next(row for row in transitions if row['from']=='true'and row['to']=='false')
  retarget['poseDelta']=max(abs(retarget['before'][key]-retarget['after'][key])for key in ['left','top','width','height'])
  assert retarget['poseDelta']<.75 and any(frame['at']>reversal and frame['condensed']=='false'and 44.1<frame['buttons'][0]['height']<55.9 for frame in frames)and frames[-1]['buttons'][0]['height']>=55.9,(retarget,frames[-1])
  report['motion'].append({'case':'actual-object-strain-and-reversal','reversalAt':reversal,'retarget':retarget,'frames':frames});page.screenshot(path=str(OUT/'reversal-settled.png'))
 except Exception as error:failure('resize-motion',error)
 finally:context.close()
 # Same-size action replacements are plain updates: no button/skin/shell transform effects.
 try:
  context,page=fresh();section(page,'about');page.mouse.click(2,2);before=sample(page)
  page.evaluate("""()=>{window.sameSizeAnimations=[];const native=Element.prototype.animate;Element.prototype.animate=function(frames,options){if(document.querySelector('[data-mobile-nav]').contains(this))sameSizeAnimations.push({target:this.className,transform:frames.some(f=>'transform'in f||'translate'in f||'scale'in f),duration:options.duration});return native.call(this,frames,options)}}""")
  section(page,'faq');after=sample(page);updates=page.evaluate('sameSizeAnimations')
  old=next(b for b in before['buttons']if b['primary']);new=next(b for b in after['buttons']if b['primary'])
  assert abs(old['rect']['width']-new['rect']['width'])<1 and abs(old['rect']['height']-new['rect']['height'])<1,(before,after)
  assert not any(a['transform']for a in updates),updates
  report['motion'].append({'case':'same-size-plain-action-update','before':before,'after':after,'animations':updates})
 except Exception as error:failure('same-size-motion',error)
 finally:context.close()
 for width in ([320,390,600]if args.scope=='full'else[]):
  try:
   context,page=fresh(width=width,motion='reduce');section(page,'contacts')
   page.evaluate("""()=>{const root=document.documentElement;root.style.setProperty('--safe-left','30px');root.style.setProperty('--safe-right','22px');for(const e of document.querySelectorAll('.dock-action>span:first-child'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'}""");page.wait_for_timeout(160);s=sample(page);controls(s);report['functional'].append({'case':'text200-safe-area','width':width,'sample':s})
   page.locator('[data-open-menu]').click();page.wait_for_timeout(100);page.locator('.dock-content .menu-business [data-action-label]').evaluate("e=>e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'");page.wait_for_timeout(120)
   phone=page.locator('.dock-content .menu-business>a').evaluate("e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),t=document.createRange();t.selectNodeContents(e.querySelector('[data-action-label]'));return{label:e.textContent,aria:e.getAttribute('aria-label'),height:r.height,padding:parseFloat(s.paddingLeft),lines:t.getClientRects().length,fits:t.getBoundingClientRect().width<=e.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1}}")
   assert phone['height']>=44 and phone['padding']>=12 and phone['lines']==1 and phone['fits']and phone['aria'],phone
   report['functional'].append({'case':'menu-phone200','width':width,**phone});page.keyboard.press('Escape')
   page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_function("document.querySelector('[data-mobile-nav]').dataset.section==='top'&&document.querySelector('[data-mobile-nav]').dataset.condensed==='false'");page.locator('[data-dock-slot][data-action="promo"]').click();page.locator('#promo-dialog').wait_for(state='visible')
   page.locator('#promo-dialog').evaluate("root=>{for(const e of root.querySelectorAll('p,h2,[data-copy-promo],.surface-content>.btn'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'}")
   close=page.locator('#promo-dialog .dialog-head>.icon-btn').evaluate("e=>{const r=e.getBoundingClientRect();return{width:r.width,height:r.height}}")
   if close['width']<43.9 or close['height']<43.9:report['findings'].append({'kind':'promo-close-hit-area','width':width,'close':close})
   cta=page.locator('#promo-dialog .surface-content>.btn');cta.scroll_into_view_if_needed();geometry=cta.evaluate("e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),label=e.querySelector('.mobile-action-short'),range=document.createRange();range.selectNodeContents(label);return{height:r.height,padding:parseFloat(s.paddingLeft),lines:range.getClientRects().length,fits:range.getBoundingClientRect().width<=r.width-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight)+1,dialogOverflow:e.closest('dialog').scrollWidth>e.closest('dialog').clientWidth+1}}")
   assert geometry['height']>=44 and geometry['padding']>=12 and geometry['lines']==1 and geometry['fits']and not geometry['dialogOverflow'],geometry
   report['functional'].append({'case':'promo200-scroll','width':width,'close':close,**geometry});page.screenshot(path=str(OUT/f'promo200-{width}.png'));page.keyboard.press('Escape')
  except Exception as error:failure(f'text200-{width}',error)
  finally:context.close()
 browser.close()
report['sourceEnd']=hashes();save();assert report['sourceStart']==report['sourceEnd']and not report['pageErrors'],report
assert not report['findings'],report['findings'];print(f'PASS {args.engine}: {len(report["palette"])} actual section/theme palettes, {len(report["functional"])} native/menu/text cases, real skin reversal with every target>=44')
