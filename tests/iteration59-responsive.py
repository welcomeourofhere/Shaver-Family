import os
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
out=Path('artifacts/iteration59');results=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome')
 for width in [320,390,768,1440]:
  for theme in ['light','dark']:
   for scale in [1,2]:
    c=b.new_context(viewport={'width':width,'height':900},has_touch=width<=960,reduced_motion='reduce');page=c.new_page();page.goto(os.environ.get('QA_URL','http://127.0.0.1:4321/'),wait_until='domcontentloaded');page.evaluate('document.fonts.ready')
    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
    if scale==2:page.evaluate("()=>{const nodes=[...document.querySelectorAll('body *')].filter(e=>!e.closest('svg,script,style')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const sizes=nodes.map(e=>parseFloat(getComputedStyle(e).fontSize));nodes.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')}")
    page.locator('[data-team-open="souz-darya"]').first.evaluate('e=>e.click()');page.wait_for_timeout(150);d=page.locator('#team-dialog-souz-darya');assert d.locator('.story-answer').count()==34
    assert not d.locator('.surface-content').evaluate('e=>e.scrollWidth>e.clientWidth+1'),(width,theme,scale)
    page.keyboard.press('Escape')
    for i in range(3):
     item=page.locator('.faq-item').nth(i);item.locator('summary').click();assert item.get_attribute('open') is not None
    hours=page.locator('.contact-business-lines .info-trigger-text');hours.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(350);hours.tap() if width<=960 else hours.click();assert hours.get_attribute('aria-expanded')=='true',(width,theme,scale);page.keyboard.press('Escape');assert hours.get_attribute('aria-expanded')=='false'
    size=hours.evaluate('e=>({w:e.clientWidth,s:e.scrollWidth,h:e.getBoundingClientRect().height,wrap:getComputedStyle(e).whiteSpace})');assert size['w']>=size['s'] and size['h']>=44 and size['wrap']=='nowrap',size
    results.append({'width':width,'theme':theme,'textScale':scale,'passed':True});c.close()
 b.close()
(out/'responsive.json').write_text(json.dumps(results,indent=2));print('PASS',len(results),'responsive/theme/text/reduced-motion scenarios')
