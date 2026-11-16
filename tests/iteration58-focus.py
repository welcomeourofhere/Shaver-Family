import os
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
out=Path('artifacts/iteration58');out.mkdir(exist_ok=True);results=[]
with sync_playwright()as p:
 b=p.chromium.launch(channel='chrome')
 for width in [390,768,1440]:
  c=b.new_context(viewport={'width':width,'height':900},has_touch=width<961);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(os.environ.get('QA_URL','http://127.0.0.1:4321/'),wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(400)
  if width<961:
   logo=page.locator('.hero-brand img').evaluate('(e)=>({y:e.getBoundingClientRect().top,src:e.currentSrc})');assert logo['y']>=56 and 'logo-paper.svg'in logo['src'];page.screenshot(path=str(out/f'hero-{width}.png'))
   page.locator('.sd-stack').evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(250)
   seen=set()
   for dx in [-180,180]*5:
    expected=page.locator('[data-sd-panel]').evaluate_all("es=>es.find(e=>e.style.getPropertyValue('--card-level')==='1').dataset.sdPanel")
    r=page.locator('.sd-stack').bounding_box();x=width*.5;y=max(100,min(600,r['y']+160));page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y,steps=12);page.mouse.up();page.wait_for_timeout(500)
    actual=page.locator('[data-sd-tab][aria-selected=true]').get_attribute('data-sd-tab');assert actual==expected,(width,dx,expected,actual);seen.add(actual)
   assert len(seen)==5,seen
   page.locator('[data-about-card]').first.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(300);page.locator('[data-about-more]').first.click();page.wait_for_timeout(300)
   assert page.locator('.about-prose').first.evaluate("e=>getComputedStyle(e).scrollbarWidth")=='none';page.screenshot(path=str(out/f'about-{width}.png'))
   page.locator('#review-03').evaluate("e=>e.scrollIntoView({block:'center',inline:'start',behavior:'instant'})");page.wait_for_timeout(400);button=page.locator('#review-03 [data-review-read]');button.click();page.wait_for_timeout(300)
   assert page.locator('#review-03 .review-prose').evaluate("e=>getComputedStyle(e).scrollbarWidth")=='thin'
  else:
   page.locator('#services').evaluate("e=>e.scrollIntoView({behavior:'instant'})");page.wait_for_timeout(300)
   for tab in page.locator('[data-sd-tab]').all():
    tab.click();page.wait_for_timeout(300)
    active=page.locator('.sd-card[aria-hidden=false]')
    for row in active.locator('.sd-service').all():
     row.evaluate('(e)=>e.open=true');page.wait_for_timeout(100)
     page.wait_for_function("()=>{const im=document.querySelector('.sd-card[aria-hidden=false] [data-photo-current=true]');return im&&im.complete&&im.naturalWidth>0&&im.currentSrc.includes('/service-posters/')}" )
   page.screenshot(path=str(out/'services-desktop.png'))
  page.locator('[data-team-open="souz-sofya-shalaginova"]').first.evaluate('(e)=>e.click()');page.wait_for_timeout(500)
  for theme in ['light','dark']:
   page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
   colors=page.locator('dialog[open] .story-answer').first.evaluate("e=>{const q=e.querySelector('h4'),a=e.querySelector('blockquote');return {q:getComputedStyle(q).color,a:getComputedStyle(a).color,weight:getComputedStyle(q).fontWeight}}")
   assert colors['q']==colors['a'] and colors['weight']=='600',colors
  assert not errors,errors;results.append({'width':width,'passed':True,'errors':errors});c.close()
 b.close()
(out/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(results)
