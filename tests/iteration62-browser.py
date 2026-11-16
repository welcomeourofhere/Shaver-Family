"""Owner corrections: responsive ticket, quiet reading scrollbars, hours and direct drag."""
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
regression=importlib.util.module_from_spec(spec);spec.loader.exec_module(regression)
server,url=regression.serve(ROOT/'dist');before=regression.digest(ROOT/'dist');source_before=regression.sources();rows=[]
out=ROOT/'artifacts/iteration62';out.mkdir(parents=True,exist_ok=True)
result=ROOT/'tmp/planning/iteration62';result.mkdir(parents=True,exist_ok=True)
scale_text="""()=>{const nodes=[...document.querySelectorAll('#first-visit *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const sizes=nodes.map(e=>parseFloat(getComputedStyle(e).fontSize));nodes.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')}"""
try:
 with sync_playwright()as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}))
   context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
   context.route('**/*',lambda route:route.continue_()if route.request.url.startswith(url)else route.abort())
   page=context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for width in [320,390,540,640,768,800,960,1024,1440]:
    for theme in ['light','dark']:
     page.set_viewport_size({'width':width,'height':1100});page.goto(url,wait_until='domcontentloaded');page.evaluate('document.fonts.ready')
     page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
     page.locator('#first-visit').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
     page.locator('.visit-figure').first.wait_for(state='visible');page.wait_for_function("[...document.querySelectorAll('.visit-figure')].every(e=>e.complete&&e.naturalWidth>0)")
     page.locator('.visit-figure').evaluate_all("images=>Promise.all(images.map(image=>image.decode()))")
     for scale in [1,2]:
      if scale==2:page.evaluate(scale_text)
      state=page.locator('.visit-ticket').evaluate("""e=>{const r=e.getBoundingClientRect(),copy=e.querySelector('.visit-copy'),c=copy.getBoundingClientRect(),art=e.querySelector('.visit-art').getBoundingClientRect(),s=e.querySelector('.visit-svetlana').getBoundingClientRect(),n=e.querySelector('.visit-sonya').getBoundingClientRect(),print=e.querySelector('.visit-print').getBoundingClientRect();return{width:r.width,height:r.height,columns:getComputedStyle(e).gridTemplateColumns.split(' ').length,copyTop:c.top-r.top,copyHeight:c.height,seam:art.bottom-r.top,print:print.height,svetlana:s.top-r.top,sonya:n.top-r.top,overflow:e.scrollWidth>e.clientWidth+1,text:copy.scrollWidth>copy.clientWidth+1,buttons:[...e.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect(),style=getComputedStyle(b);return{w:r.width,h:r.height,scroll:b.scrollWidth,client:b.clientWidth,padding:parseFloat(style.paddingLeft),wrap:style.whiteSpace}})}}""")
      assert not state['overflow']and not state['text'],(engine,width,theme,scale,state)
      assert state['svetlana']<0 and state['sonya']>state['svetlana']+8,(engine,width,state)
      assert state['columns']==(1 if state['width']<760 else 2),(width,state)
      if state['columns']==1:
       assert abs(state['seam']-state['copyTop'])<1 and abs(state['print']-state['copyTop'])<1,state
       if scale==1 and state['width']>=500:assert state['copyHeight']<state['seam'],state
      for button in state['buttons']:assert button['h']>=44 and button['client']>=button['scroll']and button['padding']>=12 and button['wrap']=='nowrap',button
      rows.append({'engine':engine,'ticketWidth':width,'theme':theme,'textScale':scale,'geometry':state})
      if engine=='chromium'and scale==1 and theme=='light'and width in [390,640,800,1440]:page.screenshot(path=str(out/f'fair-{width}.png'))
   # A small available section on a wide display must choose the same intrinsic composition.
   page.set_viewport_size({'width':1440,'height':1000});page.goto(url);page.evaluate("document.querySelector('#first-visit').style.width='500px'")
   assert page.locator('.visit-ticket').evaluate("e=>getComputedStyle(e).gridTemplateColumns.split(' ').length")==1
   # Actual opening/closing frames, including reversal. The thumb remains transparent during geometry changes.
   page.emulate_media(reduced_motion='no-preference');page.set_viewport_size({'width':768,'height':900});page.goto(url);page.evaluate('document.fonts.ready');page.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'")
   for card_selector,button_selector,prose_selector,state_key in [('.about-card','[data-about-more]','.about-prose','expanded'),('.review-card','[data-review-read]','.review-prose','reading')]:
    candidate=page.locator(card_selector).filter(has=page.locator(button_selector+':not([hidden])')).first
    candidate.evaluate("e=>e.scrollIntoView({block:'center',inline:'start',behavior:'instant'})");page.wait_for_timeout(400)
    candidate.evaluate("e=>{window.__readTrace=[];const prose=e.querySelector('.reading-prose');const start=performance.now();function sample(now){const s=getComputedStyle(prose);__readTrace.push({t:now-start,moving:prose.hasAttribute('data-reading-transition'),thumb:s.getPropertyValue('--reading-thumb').trim(),range:prose.scrollHeight-prose.clientHeight,width:prose.clientWidth});if(now-start<500)requestAnimationFrame(sample)}requestAnimationFrame(sample)}")
    candidate.locator(button_selector).click();page.wait_for_timeout(550)
    trace=page.evaluate('window.__readTrace');assert len(trace)>4,(engine,trace)
    moving=[r for r in trace if r['moving']];assert moving and all(r['thumb']=='transparent'for r in moving),(engine,trace)
    assert not candidate.locator(prose_selector).get_attribute('data-reading-transition')
    if 'review' in card_selector:
     style=candidate.locator(prose_selector).evaluate("e=>({width:getComputedStyle(e).scrollbarWidth,color:getComputedStyle(e).scrollbarColor,track:getComputedStyle(e,'::-webkit-scrollbar-track').backgroundColor,button:getComputedStyle(e,'::-webkit-scrollbar-button').display})")
     if engine=='firefox':assert 'transparent'in style['color']or 'rgba(0, 0, 0, 0)'in style['color'],style
     else:assert style['width']=='auto'and style['track']=='rgba(0, 0, 0, 0)'and style['button']=='none',style
    rows.append({'engine':engine,'reading':card_selector,'frames':trace})
    candidate.locator(button_selector).click();page.wait_for_timeout(60);candidate.locator(button_selector).click();page.wait_for_timeout(400)
    assert candidate.get_attribute('data-'+state_key)=='true'and not candidate.locator(prose_selector).get_attribute('data-reading-transition')
   # Header hours matches the menu's geometry and uses help cursor; Escape cancels its animation.
   page.set_viewport_size({'width':1440,'height':1000});page.goto(url);page.evaluate('document.fonts.ready');page.mouse.move(30,300)
   hours=page.locator('.header-hours button');hours.hover();page.wait_for_function("document.querySelector('.header-hours button').getAttribute('aria-expanded')==='true'")
   state=hours.evaluate("e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),nav=getComputedStyle(document.querySelector('.more-menu>summary'));return{cursor:s.cursor,h:r.height,radius:s.borderRadius,navRadius:nav.borderRadius,bg:s.backgroundColor,padding:parseFloat(s.paddingLeft)}}")
   assert state['cursor']=='help'and state['h']>=48 and state['radius']==state['navRadius']and state['padding']>=12,state
   page.keyboard.press('Escape');assert hours.get_attribute('aria-expanded')=='false'
   panel=page.locator('#'+hours.get_attribute('aria-describedby'));assert panel.evaluate('e=>e.getAnimations().length')==0
   rows.append({'engine':engine,'hours':state})
   # Continuous pointer drag, reversal, return and cancellation.
   rail=page.locator('[data-of-rail]');rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(450)
   bounds=rail.bounding_box();x=min(1350,bounds['x']+bounds['width']-60);y=max(180,min(650,bounds['y']+220));page.mouse.move(x,y);page.mouse.down();held=[]
   for distance in range(34,1030,34):page.mouse.move(x-distance,y);held.append(page.locator('[data-offers]').get_attribute('data-offer-index'))
   assert len(set(held))>=4,held
   page.mouse.move(x-350,y,steps=8);reverse=page.locator('[data-offers]').get_attribute('data-offer-index');assert reverse!=held[-1];page.mouse.up();page.wait_for_timeout(450)
   assert page.locator('[data-offers]').get_attribute('data-offers-moving')=='false'
   rows.append({'engine':engine,'dragIndices':held,'reverse':reverse})
   # The lower menu keeps actions reachable in narrow and short windows, in both themes.
   for width,height in [(320,568),(390,700),(768,420)]:
    page.set_viewport_size({'width':width,'height':height});page.goto(url);page.wait_for_function("document.querySelector('[data-mobile-nav]')?.dataset.actionCount>0")
    page.locator('[data-open-menu]').click();page.wait_for_timeout(350)
    for theme in ['light','dark']:
     page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
     content=page.locator('#mobile-menu .surface-content');assert content.evaluate('e=>e.scrollWidth<=e.clientWidth+1'),(engine,width,height)
     content.evaluate('e=>e.scrollTop=e.scrollHeight')
     for selector in ['.choice-trigger','.fb-setting']:
      button=content.locator(selector);assert button.evaluate("e=>{const s=getComputedStyle(e);return e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().height>=44&&parseFloat(s.paddingLeft)>=12&&s.whiteSpace==='nowrap'}"),(engine,width,selector)
    content.locator('.menu-settings').evaluate("e=>{const ns=[...e.querySelectorAll('*')].filter(n=>[...n.childNodes].some(c=>c.nodeType===3&&c.textContent.trim())),sizes=ns.map(n=>parseFloat(getComputedStyle(n).fontSize));ns.forEach((n,i)=>n.style.fontSize=sizes[i]*2+'px')}");page.wait_for_timeout(200)
    collisions=content.locator('.menu-setting-row').evaluate_all("rows=>rows.map(row=>{const label=row.querySelector(':scope>span'),control=row.querySelector('.theme-control,.fb-setting'),range=document.createRange();range.selectNodeContents(label);const a=range.getBoundingClientRect(),b=control.getBoundingClientRect();return{label:label.textContent,overlap:a.right>b.left+1&&a.top<b.bottom&&a.bottom>b.top}}).filter(r=>r.overlap)")
    assert not collisions,(engine,width,height,collisions)
    if engine=='chromium':page.screenshot(path=str(out/f'menu-{width}x{height}.png'))
    page.keyboard.press('Escape');rows.append({'engine':engine,'menu':[width,height]})
   assert not errors,errors;context.close()
   if engine=='chromium':
    touch=browser.new_context(viewport={'width':390,'height':900},has_touch=True,is_mobile=True,reduced_motion='reduce');touch.route('**/*',lambda r:r.continue_()if r.request.url.startswith(url)else r.abort())
    t=touch.new_page();cdp=touch.new_cdp_session(t)
    def swipe_text(delta):
     box=t.locator('#review-03 .review-prose').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
     cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
     for step in range(1,13):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+delta*step/12,'id':1}]});t.wait_for_timeout(16)
     cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});t.wait_for_timeout(550)
    for scale in [1,2]:
     t.goto(url);t.evaluate('document.fonts.ready');t.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'")
     if scale==2:t.locator('#review-03 blockquote p').evaluate_all("ps=>ps.forEach(p=>p.style.fontSize='28px')")
     t.evaluate("document.querySelector('#review-03').scrollIntoView({block:'center',inline:'start',behavior:'instant'});document.querySelector('#review-03 [data-review-read]').click()");t.wait_for_timeout(250)
     prose=t.locator('#review-03 .review-prose');line=prose.locator('p').first.evaluate('e=>getComputedStyle(e).lineHeight');assert float(line[:-2]).is_integer(),line
     # A gesture begun inside stays in the reader even when it reaches the end.
     prose.evaluate('e=>e.scrollTop=e.scrollHeight-e.clientHeight-40');t.wait_for_timeout(100);start=t.evaluate('scrollY');swipe_text(-140);assert abs(t.evaluate('scrollY')-start)<2
     # The next gesture at the existing boundary belongs to the page.
     prose.evaluate('e=>e.scrollTop=e.scrollHeight');t.wait_for_timeout(100);start=t.evaluate('scrollY');swipe_text(-90);assert t.evaluate('scrollY')>start+20
     rows.append({'engine':engine,'nativeReaderTouch':True,'textScale':scale,'lineHeight':line,'pageTravel':t.evaluate('scrollY')-start})
    touch.close()
   browser.close();print('PASS',engine,'owner corrections',flush=True)
finally:
 after=regression.digest(ROOT/'dist');source_after=regression.sources();server.shutdown();server.server_close()
 (result/'owner-corrections.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after,'sourcesUnchanged':source_before==source_after,'sourceDigests':source_before,'cases':rows,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
assert before==after and source_before==source_after
