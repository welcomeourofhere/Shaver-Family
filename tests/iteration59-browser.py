import os
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
out=Path('artifacts/iteration59')/os.environ.get('QA_ENGINE','chromium');out.mkdir(exist_ok=True,parents=True);results=[]
with sync_playwright()as p:
 engine=os.environ.get('QA_ENGINE','chromium');b=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else {}));page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(os.environ.get('QA_URL','http://127.0.0.1:4321/'));page.evaluate('document.fonts.ready');page.wait_for_timeout(600)
 # A continuous desktop drag crosses more than one card before pointerup.
 rail=page.locator('[data-of-rail]');rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(600);box=rail.bounding_box();x=min(1380,box['x']+box['width']-50);y=max(180,min(700,box['y']+220));page.mouse.move(x,y);page.mouse.down();held=[]
 for step in range(1,31):
  page.mouse.move(x-step*34,y);page.wait_for_timeout(10);held.append(page.locator('[data-offers]').get_attribute('data-offer-index'))
 assert len(set(held))>=3,held
 page.mouse.move(x-500,y,steps=10);reverse=page.locator('[data-offers]').get_attribute('data-offer-index');page.mouse.up();page.wait_for_timeout(800);results.append({'desktop-continuous-held':held,'reverse-index':reverse})
 assert reverse!=held[-1],reverse
 before=page.locator('[data-offers]').get_attribute('data-offer-index');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-900,y,steps=20);page.mouse.move(x,y,steps=20);page.mouse.up();page.wait_for_timeout(600);assert page.locator('[data-offers]').get_attribute('data-offer-index')==before
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-120,y,steps=8);page.locator('[data-of-rail]').dispatch_event('pointercancel',{'pointerId':1});page.mouse.up();page.wait_for_timeout(600);assert page.locator('[data-offers]').get_attribute('data-offer-index')==before

 # Hours popup in header, repeat click, Escape and contact instance.
 page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_timeout(600);trigger=page.locator('.header-hours button');trigger.click();page.wait_for_timeout(200);assert trigger.get_attribute('aria-expanded')=='true';page.screenshot(path=str(out/'hours-desktop.png'));page.keyboard.press('Escape');assert trigger.get_attribute('aria-expanded')=='false'
 # FAQ surfaces vary, hover stays yellow.
 faq=page.locator('.faq-item');colors=[]
 for i in range(3):
  faq.nth(i).locator('summary').click();page.wait_for_timeout(100);colors.append(faq.nth(i).evaluate('e=>getComputedStyle(e).backgroundColor'))
 assert len(set(colors))==3,colors
 for width in [390,768,1440]:
  page.set_viewport_size({'width':width,'height':900});page.goto(os.environ.get('QA_URL','http://127.0.0.1:4321/'));page.wait_for_timeout(500)
  page.locator('[data-team-open="souz-darya"]').first.evaluate('e=>e.click()');page.wait_for_timeout(450);d=page.locator('#team-dialog-souz-darya');assert d.locator('.story-answer').count()==34
  assert d.locator('.story-photo-grid img').count()==23 # cover is separate
  assert ' '.join(d.locator('.story-heading').inner_text().split()).casefold()=='дарья мерзлякова. знакомство.'
  assert not d.locator('.surface-content').evaluate('e=>e.scrollWidth>e.clientWidth+1')
  page.screenshot(path=str(out/f'darya-{width}.png'));page.keyboard.press('Escape');results.append({'article-width':width,'questions':34})
 assert not errors,errors;b.close()
(out/'browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(results)
