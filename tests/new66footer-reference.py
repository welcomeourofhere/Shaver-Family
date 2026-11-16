"""Live main-footer acceptance: facts, focus order, dialog owners and startup.

Uses the real HMR page. Provider iframe is replaced by an empty local response;
no booking, payment or message is submitted. Layout matrix has its own report.
"""
import argparse, asyncio, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--label',default='acceptance');ARGS=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/footer-reference'/ARGS.label
OUT.mkdir(parents=True,exist_ok=False)
SITE=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
LEGAL=json.loads((ROOT/'content/legal/pages.json').read_text(encoding='utf-8'))['pages']
OPERATOR=json.loads((ROOT/'content/legal/operator.json').read_text(encoding='utf-8'))
FILES=['src/components/Footer.astro','src/styles/footer.css','src/config/navigation.ts']
hashes=lambda:{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
REPORT={'started':datetime.now(timezone.utc).isoformat(),'sourceStart':hashes(),'cases':[],'errors':[],'findings':[]}
normal=lambda text:' '.join(text.split())

async def prepare(page,path='/'):
 for attempt in range(3):
  try:
   await page.goto('http://127.0.0.1:4321'+path,wait_until='domcontentloaded');break
  except Exception as error:
   if attempt==2 or not any(s in str(error) for s in ['ERR_ABORTED','context was destroyed']):raise
   await page.wait_for_timeout(250)
 await page.evaluate('document.fonts.ready')
 await page.wait_for_timeout(500)
 await page.locator('.footer').scroll_into_view_if_needed()

async def inspect(page,case):
 footer=page.locator('.footer')
 text=normal(await footer.inner_text())
 entry={'case':case,'text':text,'navigation':await footer.locator('.footer-groups a').evaluate_all('(xs)=>xs.map(e=>({text:e.innerText,href:e.getAttribute("href")}))')}
 for fact in [OPERATOR['legalName'],OPERATOR['inn'],OPERATOR['ogrnip']]:
  if normal(fact) not in text:REPORT['findings'].append({'kind':'missing-fact','case':case,'fact':fact})
 if normal('Первый барбершоп в Кирове, где стригут и бреют только девушки') not in text:REPORT['findings'].append({'kind':'brand-description','case':case})
 if len(entry['navigation'])!=6:REPORT['findings'].append({'kind':'popular-navigation-count','case':case,'actual':entry['navigation']})
 if await footer.locator('.footer-bottom .footer-legal').count():REPORT['findings'].append({'kind':'legal-below-divider','case':case})
 bottomFonts=await footer.locator('.footer-bottom>p').evaluate_all('(xs)=>xs.map(e=>{const s=getComputedStyle(e);return [s.fontSize,s.fontWeight,s.fontFamily,s.lineHeight]})')
 if bottomFonts[0]!=bottomFonts[1]:REPORT['findings'].append({'kind':'bottom-typography','case':case,'actual':bottomFonts})
 actions=await footer.locator('.footer-actions').evaluate('e=>[...e.children].map(e=>e.className)')
 if actions!=['footer-booking','contact-channels']:REPORT['findings'].append({'kind':'booking-before-channels','case':case,'actual':actions})
 labels=await footer.locator('.footer-legal a').all_text_contents()
 if sorted(map(normal,labels))!=sorted(normal(p['title']) for p in LEGAL):REPORT['findings'].append({'kind':'legal-titles','case':case,'actual':labels})
 legalHrefs=await footer.locator('.footer-legal a').evaluate_all('(xs)=>xs.map(e=>e.getAttribute("href"))')
 if sorted(legalHrefs)!=sorted('/'+p['slug']+'/' for p in LEGAL):REPORT['findings'].append({'kind':'legal-hrefs','case':case,'actual':legalHrefs})
 for channel,key in [('telegram','telegram'),('max','maxUrl'),('vk','vkMessageUrl')]:
  if await footer.locator(f'[data-contact-channel="{channel}"]').get_attribute('href')!=SITE[key]:REPORT['findings'].append({'kind':'channel-route','case':case,'channel':channel})
 entry['geometry']=await footer.evaluate('''f=>{
  const controls=[...f.querySelectorAll('a,button')].filter(e=>e.getClientRects().length&&!e.closest('.info-panel'));
  const textRects=e=>{const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),out=[];let n;while(n=w.nextNode()){if(!n.textContent.trim()||n.parentElement.closest('.sr-only,[aria-hidden="true"]'))continue;const r=document.createRange();r.selectNodeContents(n);for(const b of r.getClientRects())if(b.width&&b.height)out.push({left:b.left,right:b.right,top:b.top,bottom:b.bottom});}return out;};
  const links=controls.map(e=>({label:e.innerText.trim()||e.getAttribute('aria-label'),rects:textRects(e)}));
  const overlap=[];for(let i=0;i<links.length;i++)for(let j=i+1;j<links.length;j++)for(const a of links[i].rects)for(const b of links[j].rects)if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)overlap.push([links[i].label,links[j].label]);
  const hitOverlap=[];for(let i=0;i<controls.length;i++)for(let j=i+1;j<controls.length;j++){const a=controls[i].getBoundingClientRect(),b=controls[j].getBoundingClientRect();if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)hitOverlap.push([links[i].label,links[j].label]);}
  return {overflow:f.scrollWidth>f.clientWidth+1,overlap,hitOverlap,height:f.querySelector('.footer-card').getBoundingClientRect().height};
 }''')
 if entry['geometry']['overflow'] or entry['geometry']['overlap'] or entry['geometry']['hitOverlap']:REPORT['findings'].append({'kind':'geometry','case':case,'details':entry['geometry']})
 REPORT['cases'].append(entry)
 return entry

async def main():
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(channel='msedge',headless=True)
   for theme in ['light','dark']:
    for width in [320,390,700,800,961,1440]:
     context=await browser.new_context(viewport={'width':width,'height':900},color_scheme=theme,reduced_motion='reduce')
     await context.add_init_script("localStorage.setItem('soyuz.analytics.v1','denied')")
     await context.route('**/*yclients.ru/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<!doctype html><title>Provider route verification</title>'))
     page=await context.new_page();page.on('pageerror',lambda e:REPORT['errors'].append(str(e)))
     await prepare(page)
     case={'theme':theme,'width':width,'mode':'interactive'}
     entry=await inspect(page,case)
     controls=page.locator('.footer a,.footer button').filter(visible=True)
     expected=await controls.evaluate_all('(xs)=>xs.filter(e=>!e.closest(".info-panel")).map(e=>e.id||e.getAttribute("aria-label")||e.innerText.trim())')
     await page.locator('.footer-logo').focus()
     visited=[]
     for _ in expected:
      current=await page.evaluate('''()=>{const e=document.activeElement,s=getComputedStyle(e);return {name:e.id||e.getAttribute('aria-label')||e.innerText.trim(),inFooter:!!e.closest('.footer'),focused:e.matches(':focus-visible'),outline:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth),outlineColor:s.outlineColor}}''')
      visited.append(current)
      await page.keyboard.press('Tab')
     entry['keyboard']=visited
     if [x['name'] for x in visited]!=expected or any(not x['inFooter'] or not x['focused'] or x['outline']=='none' or x['outlineWidth']<1 for x in visited):REPORT['findings'].append({'kind':'keyboard','case':case,'expected':expected,'actual':visited})
     for target,dialog in [('.footer-booking a','#booking-drawer')]:
      control=page.locator(target);await control.focus();await page.keyboard.press('Enter');await page.locator(dialog).wait_for(state='visible')
      await page.keyboard.press('Escape');await page.locator(dialog).wait_for(state='hidden')
      returned=await control.evaluate('e=>e===document.activeElement')
      entry.setdefault('dialogs',[]).append({'target':target,'focusReturned':returned})
      if not returned:REPORT['findings'].append({'kind':'dialog-focus-return','case':case,'target':target})
     await page.locator('.footer').screenshot(path=str(OUT/f'footer-{width}-{theme}.png'))
     await context.close()
   for width in [320,1440]:
    context=await browser.new_context(viewport={'width':width,'height':900},java_script_enabled=False)
    page=await context.new_page();await prepare(page);entry=await inspect(page,{'width':width,'mode':'no-js'});entry['fallbackBookingHref']=await page.locator('.footer-booking a').get_attribute('href')
    if not entry['fallbackBookingHref'].startswith('https://'):REPORT['findings'].append({'kind':'fallback-booking','case':entry['case']})
    await context.close()
   context=await browser.new_context(viewport={'width':390,'height':900},reduced_motion='reduce')
   await context.add_init_script("localStorage.setItem('soyuz.analytics.v1','denied')")
   page=await context.new_page();await prepare(page,'/privacy-policy/');entry=await inspect(page,{'width':390,'mode':'legal-route'})
   bad=await page.locator('.footer-groups a').evaluate_all('(xs)=>xs.filter(e=>!e.getAttribute("href").startsWith("/#")).map(e=>e.getAttribute("href"))')
   if bad:REPORT['findings'].append({'kind':'legal-page-home-anchors','actual':bad})
   await context.close();await browser.close()
 except Exception as error:
  REPORT['exception']=repr(error);REPORT['findings'].append({'kind':'runner-exception','details':repr(error)})
 finally:
  REPORT['sourceEnd']=hashes();REPORT['sourceChanged']=REPORT['sourceStart']!=REPORT['sourceEnd'];REPORT['finished']=datetime.now(timezone.utc).isoformat()
  (OUT/'report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({'cases':len(REPORT['cases']),'errors':REPORT['errors'],'findings':REPORT['findings'],'sourceChanged':REPORT['sourceChanged']},ensure_ascii=True))

asyncio.run(main())
raise SystemExit(bool(REPORT['errors'] or REPORT['findings'] or REPORT['sourceChanged']))
