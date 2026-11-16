"""Shared chrome, pending gifts, icon geometry and non-wrapping action acceptance."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('QA_URL','http://127.0.0.1:4321/')
OUT=ROOT/'tmp/planning/iteration65/shell';OUT.mkdir(parents=True,exist_ok=True)
ART=ROOT/'artifacts/iteration65';ART.mkdir(parents=True,exist_ok=True)
rows=[]
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome')
 for width in [320,390,600,768,960,961,1024,1440]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
   context.add_init_script("localStorage.setItem('soyuz_theme','"+theme+"');localStorage.setItem('soyuz.analytics.v1','denied')")
   errors=[];page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(URL,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(650)
   assert not errors,errors
   assert page.locator('.site-header').count()==page.locator('.footer').count()==1
   assert page.locator('.visit-copy h3').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)>=38'),(width,'fair price title lost its size token')
   assert page.locator('[data-back-to-top] svg path').count()==1,'up arrow has unresolved SVG reference'
   assert page.locator('.footer-legal a').count()==3
   assert not page.locator('.footer [data-analytics-settings]').count()
   assert all(len(t)>15 for t in page.locator('.footer-legal a').all_text_contents())
   page.locator('#gifts').evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})');page.wait_for_timeout(150)
   assert page.locator('.gifts-placeholder').is_visible()
   assert page.locator('.gifts-placeholder img,.gifts-placeholder button,.gifts-placeholder [inert]').count()==0
   assert page.locator('.gifts-placeholder').evaluate('e=>getComputedStyle(e).filter')=='none'
   assert page.locator('.certificates .certificate-buy').is_enabled()
   if width>960:
    pending=page.locator('.gifts-placeholder').bounding_box();certificate=page.locator('.certificates').bounding_box()
    assert abs(pending['height']-certificate['height'])<1,(pending,certificate)
   assert not page.locator('.certificates').evaluate('e=>Boolean(e.closest(".gifts-pending"))')
   if width==1440 and theme=='light':page.locator('.gifts-layout').screenshot(path=str(ART/'gifts-pending-1440.png'))
   page.locator('.footer').scroll_into_view_if_needed();page.wait_for_timeout(100)
   assert page.locator('[data-back-to-top]').is_visible()==(width>960)
   if width==1440 and theme=='light':page.locator('.footer').screenshot(path=str(ART/'footer-1440.png'))
   if width<=960:
    page.locator('[data-open-menu]').click();page.locator('.menu-contact-row a').wait_for(state='visible');page.wait_for_timeout(350)
    box=page.locator('.menu-contact-row').evaluate('e=>[...e.querySelectorAll("a,button")].map(x=>{let r=x.getBoundingClientRect(),s=getComputedStyle(x);return{w:r.width,h:r.height,y:r.y,pl:parseFloat(s.paddingLeft),pr:parseFloat(s.paddingRight)}})')
    assert len(box)==4 and all(abs(x['h']-48)<1 for x in box)and max(x['y']for x in box)-min(x['y']for x in box)<1,box
    assert page.locator('.menu-contact-row').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    if width==390 and theme=='light':page.locator('#mobile-menu').screenshot(path=str(ART/'menu-390.png'))
   else:
    page.locator('[data-site-settings]').click();assert page.locator('#site-settings-panel').is_visible()
    assert page.locator('#site-settings-panel button').count()==3
    page.locator('[data-site-settings]').click()
    page.locator('.footer .info-trigger-text').click();page.wait_for_timeout(100)
    status=page.locator('.footer .business-hours-status')
    assert status.is_visible()
    assert status.evaluate('e=>e.getBoundingClientRect().height<=parseFloat(getComputedStyle(e).lineHeight)+1')
    page.locator('.footer .info-trigger-text').click()
   overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
   assert not overflow,(width,theme,'horizontal overflow')
   assert not errors,errors
   rows.append({'width':width,'theme':theme,'passed':True});context.close()
 for width in [320,390,768,1440]:
  context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
  page=context.new_page();page.goto(URL,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(600)
  page.evaluate("""()=>{const es=[...document.querySelectorAll('h1,h2,h3,p,small,a,button,summary,dt,dd,figcaption,label,legend')],sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}""")
  page.wait_for_timeout(400);page.locator('.footer').scroll_into_view_if_needed()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,'text200 overflow')
  clips=page.locator('.footer').evaluate("""e=>[...e.querySelectorAll('a,button')].filter(x=>x.getBoundingClientRect().width&&x.scrollWidth>x.clientWidth+1).map(x=>x.textContent)""")
  assert not clips,(width,clips)
  if width<=960:
   page.locator('[data-open-menu]').click();page.locator('.menu-contact-row a').wait_for(state='visible');page.wait_for_timeout(350)
   assert page.locator('.dock-content').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
  if width==1440:page.locator('.footer').screenshot(path=str(ART/'footer-text200.png'))
  rows.append({'width':width,'text200':True,'passed':True});context.close()
 browser.close()
(OUT/'result.json').write_text(json.dumps({'url':URL,'cases':rows},indent=2),encoding='utf-8')
print('PASS shared UI',len(rows),'cases')

