"""Compiled reviews startup: reserved geometry, first input, complete reading/rail, no JS."""
import argparse,hashlib,json,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--origin',required=True);p.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');p.add_argument('--label',required=True);p.add_argument('--single',action='store_true');p.add_argument('--only-method',nargs='+',choices=['approach','focus','click','hash','resize-before','text200','before-swap','nojs','resize-after','reading-interrupt']);a=p.parse_args();assert urlsplit(a.origin).hostname in ['127.0.0.1','localhost'];OUT=ROOT/'artifacts/iteration69'/a.label;OUT.mkdir(parents=True,exist_ok=False)
source=ROOT/'src/scripts/reviews.ts';start=hashlib.sha256(source.read_bytes()).hexdigest();rows=[]
POSE="""()=>{const b=document.querySelector('[data-review-bento]'),r=b.getBoundingClientRect();return{top:r.top+scrollY,height:r.height,width:r.width,y:scrollY,ready:b.dataset.bentoReady,layout:b.dataset.reviewLayout,cards:[...b.querySelectorAll('[data-review-card]')].filter(c=>!c.hidden).map(c=>({id:c.id,reading:c.dataset.reading,visibility:getComputedStyle(c).visibility})),next:document.querySelector('#faq').getBoundingClientRect().top+scrollY}}"""
with sync_playwright()as pw:
 b=getattr(pw,a.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if a.engine=='chromium'else{}))
 try:
  cases=[(390,'light','approach','no-preference')]if a.single else[(w,t,'approach',m)for w in [320,390,768,960,961,1440]for t in ['light','dark']for m in ['no-preference','reduce']]+[(390,'light',method,'reduce')for method in ['focus','click','hash','resize-before','text200','before-swap','nojs','resize-after','reading-interrupt']]
  if a.only_method:cases=[c for c in cases if c[2]in a.only_method]
  assert cases,'No selected scenarios'
  for width,theme,method,motion in cases:
   c=b.new_context(viewport={'width':width,'height':844},is_mobile=a.engine!='firefox',has_touch=True,color_scheme=theme,reduced_motion=motion,java_script_enabled=method!='nojs');page=c.new_page();page.set_default_timeout(12000);errors=[];row={'width':width,'theme':theme,'method':method,'motion':motion,'errors':errors,'pass':False}
   if method!='nojs':c.add_init_script("(()=>{if(top!==window)return;localStorage.setItem('soyuz_theme',"+json.dumps(theme)+");localStorage.setItem('soyuz.analytics.v1','denied');const get=crypto.getRandomValues.bind(crypto);crypto.getRandomValues=function(a){if(a instanceof Uint32Array&&a.length===1){a[0]=90210;return a}return get(a)}})()")
   c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).hostname in ['127.0.0.1','localhost']else r.abort());page.on('pageerror',lambda e:errors.append(str(e)))
   try:
    page.goto(a.origin+('#reviews'if method=='hash'else''),wait_until='domcontentloaded');page.wait_for_function("document.fonts.status==='loaded'");page.wait_for_timeout(350);before=page.evaluate(POSE);row['before']=before
    if method=='nojs':
     values=page.locator('[data-review-card] blockquote').evaluate_all("es=>es.map(e=>({text:e.textContent.length,visible:getComputedStyle(e).visibility!=='hidden'}))");assert len(values)==8 and all(v['text']>0 and v['visible']for v in values);row['noJsCards']=values
    elif method=='before-swap':
     stopped=page.evaluate("""()=>{document.dispatchEvent(new Event('astro:before-swap'));const b=document.querySelector('[data-review-bento]');return{data:{...b.dataset},busy:b.getAttribute('aria-busy'),styles:[...b.children].map(c=>c.getAttribute('style'))}}""")
     page.set_viewport_size({'width':1440,'height':700});page.locator('#reviews').evaluate("e=>e.scrollIntoView({behavior:'instant'})");page.wait_for_timeout(400)
     after_stop=page.evaluate("""()=>{const b=document.querySelector('[data-review-bento]');return{data:{...b.dataset},busy:b.getAttribute('aria-busy'),styles:[...b.children].map(c=>c.getAttribute('style'))}}""")
     assert stopped==after_stop,(stopped,after_stop);row['noUpdatesAfterCleanup']=True
    else:
     assert before['height']>0 and len(before['cards'])in([8]if width<=960 else[3,4]),before
     if method=='resize-before':page.set_viewport_size({'width':1440,'height':700});page.wait_for_timeout(100)
     if method=='text200':page.evaluate("for(const e of document.querySelectorAll('#reviews blockquote p,#reviews button'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'")
     if method=='focus':page.locator('#reviews [data-rail-step="1"]').focus()
     elif method=='click':page.locator('#reviews [data-rail-step="1"]').evaluate('e=>e.click()')
     elif method!='hash':page.locator('#reviews').evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
     page.wait_for_function("document.querySelector('[data-review-bento]').dataset.bentoReady==='true'");page.wait_for_timeout(120);after=page.evaluate(POSE);row['after']=after
     if method not in ['hash','resize-before']:assert abs(after['height']-before['height'])<=1 and abs(after['next']-before['next'])<=1,(before,after)
     if method=='resize-after':
      row['resizeSteps']=[]
      for w in [1440,390,961,768,320,1440,390]:
       page.set_viewport_size({'width':w,'height':844});page.wait_for_function("w=>document.querySelector('[data-review-bento]').dataset.reviewLayout===(w<=960?'phone':document.querySelector('[data-review-bento]').dataset.reviewLayout)&&((w<=960)===(document.querySelector('[data-review-bento]').dataset.reviewLayout==='phone'))",arg=w);page.wait_for_timeout(250);pose=page.evaluate(POSE);assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1');assert pose['ready']=='true';row['resizeSteps'].append({'width':w,'layout':pose['layout'],'cards':len(pose['cards'])})
     compact=page.evaluate("matchMedia('(max-width:960px)').matches")
     if compact:
      controls=page.locator('#reviews [data-rail-controls]');n=len(after['cards']);assert n==8
      if method in ['focus','click']and page.locator('[data-review-bento]').get_attribute('data-rail-index')!='0':page.locator('#reviews [data-rail-step="-1"]').focus();page.keyboard.press('Enter')
      seen=[]
      for index in range(n):
       page.wait_for_function("i=>Number(document.querySelector('[data-review-bento]').dataset.railIndex)===i",arg=index);seen.append(page.locator('#reviews [data-rail-count]').inner_text())
       if index<n-1:page.locator('#reviews [data-rail-step="1"]').focus();page.keyboard.press('Enter')
      assert page.locator('#reviews [data-rail-step="1"]').is_disabled();row['fullCycle']=seen
      for index in range(n-2,-1,-1):page.locator('#reviews [data-rail-step="-1"]').focus();page.keyboard.press('Enter');page.wait_for_function("i=>Number(document.querySelector('[data-review-bento]').dataset.railIndex)===i",arg=index)
      card=page.locator('[data-review-card]').filter(has=page.locator('[data-review-read]:not([hidden])')).first
      if card.count():
       card.evaluate("e=>e.scrollIntoView({block:'nearest',inline:'center',behavior:'instant'})");button=card.locator('[data-review-read]');button.focus();page.keyboard.press('Enter');page.wait_for_function("e=>e.dataset.reading==='true'",arg=card.element_handle());row['expanded']=True;button.focus();page.keyboard.press('Enter');page.wait_for_function("e=>e.dataset.reading==='false'",arg=card.element_handle())
       if method=='reading-interrupt':
        for turn in range(6):button.focus();page.keyboard.press('Enter');page.wait_for_timeout(20)
        page.wait_for_timeout(350);assert card.get_attribute('data-reading')=='false'and button.get_attribute('aria-expanded')=='false';assert card.locator('[data-review-gallery]').get_attribute('aria-hidden')=='false';row['rapidToggleCount']=6

     else:
      first=page.locator('[data-review-card]:not([hidden])');ids=first.evaluate_all('es=>es.map(e=>e.id)');page.locator('[data-review-more]').focus();page.keyboard.press('Enter');page.wait_for_timeout(150);assert 6<=page.locator('[data-review-card]:not([hidden])').count()<=8;assert set(ids)<=set(page.locator('[data-review-card]:not([hidden])').evaluate_all('es=>es.map(e=>e.id)'));page.keyboard.press('Enter');page.wait_for_timeout(100);assert page.locator('[data-review-card]:not([hidden])').count()==len(ids);row['desktopExpandCollapse']=True
     assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    assert not errors;row['pass']=True
   except Exception:row['failure']=traceback.format_exc()
   finally:
    if not row['pass']or width==390 and theme=='light':
     try:page.screenshot(path=str(OUT/(str(len(rows))+'-'+method+'.png')),timeout=5000)
     except Exception as e:row['screenshotFailure']=str(e)
    c.close();rows.append(row);(OUT/'results.json').write_text(json.dumps({'engine':a.engine,'origin':a.origin,'rows':rows,'sourceStart':start,'deliveryFixture':True,'providerRequestsBlocked':True,'performanceClaim':False},ensure_ascii=False,indent=2),encoding='utf-8')
   print(json.dumps({k:row[k]for k in ['width','theme','method','motion','pass']}),flush=True)
   if not row['pass']:break
 finally:b.close()
report={'engine':a.engine,'origin':a.origin,'rows':rows,'sourceStart':start,'sourceEnd':hashlib.sha256(source.read_bytes()).hexdigest(),'browsersClosed':True,'deliveryFixture':True,'providerRequestsBlocked':True,'performanceClaim':False,'requestedMethods':a.only_method};(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');assert report['sourceStart']==report['sourceEnd']and len(rows)==len(cases)and all(r['pass']for r in rows)
print('PASS reviews startup',len(rows),'browsersclosed END')
