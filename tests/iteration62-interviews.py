"""Four new complete interviews: routes, modal consumers, media, text scaling and personal booking."""
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
slugs=['milena-malyshevskaya','sonya-kid','svetlana-demina','lyubov-shklyaeva'];articles={s:json.loads((ROOT/f'content/master-articles/{s}.json').read_text(encoding='utf-8'))for s in slugs}
masters=json.loads((ROOT/'content/team.json').read_text(encoding='utf-8'))['masters'];server,url=reg.serve(ROOT/'dist');before=reg.digest(ROOT/'dist');sources=reg.sources();rows=[]
out=ROOT/'artifacts/iteration62';out.mkdir(exist_ok=True,parents=True)
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}));context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');context.route('**/*',lambda r:r.continue_()if r.request.url.startswith(url)else r.abort());page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for slug,article in articles.items():
    count=len(json.loads((ROOT/f'content/master-articles/{slug}.media.json').read_text(encoding='utf-8')))
    for width,theme,scale in [(390,'light',1),(390,'dark',1),(768,'light',1),(1440,'light',1),(390,'light',2)]:
     page.set_viewport_size({'width':width,'height':1000});page.goto(url+'masters/'+slug+'/');page.evaluate('document.fonts.ready');page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme);story=page.locator('article.master-story')
     if scale==2:story.evaluate("e=>{const ns=[...e.querySelectorAll('*')].filter(n=>[...n.childNodes].some(c=>c.nodeType===3&&c.textContent.trim())),sizes=ns.map(n=>parseFloat(getComputedStyle(n).fontSize));ns.forEach((n,i)=>n.style.fontSize=sizes[i]*2+'px')}")
     assert page.locator('h1').count()==1 and story.locator('img').count()==count
     state=story.evaluate("e=>{const q=e.querySelector('.story-answer>h2'),s=getComputedStyle(q),r=e.getBoundingClientRect();return{width:r.width,pageOverflow:document.documentElement.scrollWidth-innerWidth,overflow:e.scrollWidth-e.clientWidth,font:s.fontFamily,weight:s.fontWeight,colour:s.color,expected:getComputedStyle(e.querySelector('blockquote')).color,emptyHeadings:[...e.querySelectorAll('h1,h2,h3,h4')].filter(h=>!h.textContent.trim()).length}}")
     assert state['pageOverflow']<=1 and state['overflow']<=1 and state['weight']=='600' and state['colour']==state['expected']and 'Manrope'in state['font']and not state['emptyHeadings'],(engine,slug,width,scale,state)
     if engine=='chromium'and width==1440:
      story.locator('img').evaluate_all("images=>{for(const i of images)i.loading='eager';return Promise.all(images.map(i=>i.decode()))}")
      assert story.locator('img').evaluate_all('images=>images.every(i=>i.complete&&i.naturalWidth>0)')
      story.locator('.story-heading').scroll_into_view_if_needed();page.screenshot(path=str(out/f'article-{slug}-1440.png'))
     if engine=='chromium'and width==390 and scale==1 and theme=='light':page.screenshot(path=str(out/f'article-{slug}-390.png'))
     rows.append({'engine':engine,'slug':slug,'route':True,'width':width,'theme':theme,'textScale':scale,'photos':count,'geometry':state})
    # Each card uses the shared story dialog and its own company, including keyboard closure.
    page.set_viewport_size({'width':390,'height':900});page.goto(url);page.evaluate('document.fonts.ready');trigger=page.locator('[data-team-open="'+article['masterId']+'"]');trigger.evaluate("e=>e.closest('.team-card').scrollIntoView({block:'center',inline:'start',behavior:'instant'})");page.wait_for_timeout(200);trigger.click();dialog=page.locator('#team-dialog-'+article['masterId'])
    if not dialog.evaluate('e=>e.open'):page.wait_for_timeout(200);trigger.click()
    page.wait_for_function('(id)=>document.getElementById(id).open',arg=dialog.get_attribute('id'));assert dialog.locator('[data-article-slug="'+slug+'"]').count()==1
    assert dialog.locator('article.master-story img').count()==count;assert ' '.join(dialog.locator('#'+dialog.get_attribute('aria-labelledby')).text_content().split())==' '.join(article['title'].split())
    dialog.locator('.team-dialog-actions [data-booking]').click();master=next(m for m in masters if m['id']==article['masterId']);expected=master['bookingUrl'].replace('https://n','https://b')
    page.wait_for_function('(u)=>document.querySelector("[data-booking-frame]").src===u',arg=expected);assert not dialog.evaluate('e=>e.open');page.keyboard.press('Escape');assert not page.locator('#booking-drawer').evaluate('e=>e.open')
    rows.append({'engine':engine,'slug':slug,'dialogAndPersonalBooking':True,'expectedProvider':expected,'photos':count})
   assert not errors,errors;context.close();browser.close();print('PASS',engine,'new interviews: 20 route/theme/text and 4 dialog/booking cases',flush=True)
finally:
 after=reg.digest(ROOT/'dist');server.shutdown();server.server_close();(ROOT/'tmp/planning/iteration62/interviews.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'sourcesUnchanged':sources==reg.sources(),'sourceDigests':sources,'cases':rows,'purchaseSubmitted':False,'bookingSubmitted':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert len(rows)==72 and before==after and sources==reg.sources()
