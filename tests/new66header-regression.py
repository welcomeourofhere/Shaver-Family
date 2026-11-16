"""Live Header regression QA, without bookings or account writes.

200% text doubles the component's canonical meta/book roles (13/16 -> 26/32).
This is text scaling at a fixed CSS viewport, not physical-device certification.
"""
import argparse, asyncio, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--label',default='final');parser.add_argument('--origin',default='http://127.0.0.1:4321/');ARGS=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/header-regression'/ARGS.label
OUT.mkdir(parents=True,exist_ok=False)
FILES=['src/components/Header.astro','src/styles/header.css','src/config/navigation.ts']
hashes=lambda:{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
REPORT={'started':datetime.now(timezone.utc).isoformat(),'origin':ARGS.origin,'sourceStart':hashes(),'cases':[],'popups':[],'keyboard':[],'clockStatus':[],'errors':[],'findings':[]}
WIDTHS=[961,1038,1047,1062,1100,1280,1366,1440,1920]


async def prepare(page):
 for attempt in range(3):
  try:
   await page.goto(ARGS.origin,wait_until='domcontentloaded');break
  except Exception as error:
   if attempt==2 or 'ERR_ABORTED' not in str(error):raise
   await page.wait_for_timeout(200)
 await page.evaluate('document.fonts.ready');await page.wait_for_timeout(450)


SAMPLE='''()=>{
 const h=document.querySelector('.site-header'),e=h.querySelector('.header-capsule'),r=e.getBoundingClientRect(),scale=r.width/e.offsetWidth;
 const bounds=x=>{const b=x.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom,centerY:b.y+b.height/2}};
 const controls=[...e.querySelectorAll('.header-nav>a,.more-menu>summary,.header-logo,.header-hours summary,.header-contact>summary,.header-book')].filter(x=>x.getClientRects().length);
 const items=controls.map(x=>{const s=getComputedStyle(x),walker=document.createTreeWalker(x,NodeFilter.SHOW_TEXT),tops=[];let node;while(node=walker.nextNode()){if(!node.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(node);for(const b of range.getClientRects())if(b.width&&b.height&&!tops.some(y=>Math.abs(y-b.y)<1))tops.push(b.y);}
 return {label:x.innerText||x.getAttribute('aria-label'),class:x.className,bounds:bounds(x),lines:tops.length,clipped:x.scrollWidth>x.clientWidth+1,paddingLeft:parseFloat(s.paddingLeft),paddingRight:parseFloat(s.paddingRight),fontSize:s.fontSize,icon:!!x.querySelector('svg')};});
 const overlap=[];for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){const a=items[i].bounds,b=items[j].bounds;if(Math.min(a.right,b.right)-Math.max(a.x,b.x)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)>1)overlap.push([items[i].label,items[j].label]);}
 const groups=['.header-nav','.header-actions'].map(s=>{const x=e.querySelector(s);return {selector:s,width:x.clientWidth,scroll:x.scrollWidth}});
 return {capsule:bounds(e),height:e.offsetHeight,scale,items,overlap,groups,theme:document.documentElement.dataset.theme,phoneLabel:getComputedStyle(e.querySelector('.header-phone-label')).display,hoursVisible:!!e.querySelector('.header-hours').getClientRects().length};
}'''


async def popup(page,selector,case):
 await page.mouse.move(1,1);await page.keyboard.press('Escape')
 menu=page.locator(selector);trigger=menu.locator(':scope>summary')
 await trigger.hover();await page.wait_for_function('(s)=>document.querySelector(s).open',arg=selector)
 panel=menu.locator('.header-menu-panel');await panel.wait_for(state='visible')
 await page.wait_for_function('(s)=>!document.querySelector(s).querySelector(".header-menu-panel").getAnimations({subtree:true}).some(a=>a.playState==="running")',arg=selector)
 value=await panel.evaluate('''p=>{const c=p.closest('.header-capsule'),b=c.getBoundingClientRect(),r=p.getBoundingClientRect(),s=getComputedStyle(p),k=b.width/c.offsetWidth;const status=p.querySelector('[data-business-hours-status]');return {gap:(r.top-b.bottom)/k,bottom:r.bottom,viewport:innerHeight,left:r.left,right:r.right,width:innerWidth,radius:s.borderRadius,color:s.color,bg:getComputedStyle(p.querySelector('.surface-shell')).backgroundColor,status:status?{state:status.dataset.state,color:getComputedStyle(status,'::before').backgroundColor,width:getComputedStyle(status,'::before').width,weight:getComputedStyle(status).fontWeight,detailWeight:getComputedStyle(p.querySelector('[data-business-hours-detail]')).fontWeight}:null}}''')
 value.update({'case':case,'selector':selector});REPORT['popups'].append(value)
 if abs(value['gap']-8)>.6 or value['left']<-1 or value['right']>value['width']+1 or value['bottom']>value['viewport']-4:REPORT['findings'].append({'kind':'popup-placement','details':value})
 if value['radius']!='20px':REPORT['findings'].append({'kind':'popup-radius','details':value})
 if value['status'] and (value['status']['width']!='8px' or value['status']['weight']!='600' or value['status']['detailWeight']!='400'):REPORT['findings'].append({'kind':'status-typography','details':value})
 if selector=='.more-menu':
  visible=await page.locator('.header-nav a').evaluate_all('(xs)=>xs.filter(e=>e.getClientRects().length).map(e=>e.getAttribute("href"))')
  if len(visible)!=10 or len(set(visible))!=10:REPORT['findings'].append({'kind':'navigation-destinations','case':case,'actual':visible})
 await page.keyboard.press('Escape');await page.wait_for_function('(s)=>!document.querySelector(s).open',arg=selector)
 await trigger.focus();await page.keyboard.press('ArrowDown')
 first=await menu.evaluate('''m=>{const links=[...m.querySelectorAll('.header-menu-panel a[href],.header-menu-panel button:not(:disabled)')].filter(e=>e.getClientRects().length);return !links.length||links[0]===document.activeElement}''')
 await page.keyboard.press('Escape');await page.wait_for_function('(s)=>!document.querySelector(s).open',arg=selector)
 restored=await trigger.evaluate('e=>e===document.activeElement')
 REPORT['keyboard'].append({'case':case,'selector':selector,'firstItem':first,'focusRestored':restored})
 if not first or not restored:REPORT['findings'].append({'kind':'popup-keyboard','case':case,'selector':selector})


async def main():
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(channel='msedge',headless=True)
   for theme in ['light','dark']:
    context=await browser.new_context(viewport={'width':1440,'height':900},color_scheme=theme,reduced_motion='reduce')
    await context.add_init_script("localStorage.setItem('soyuz.analytics.v1','denied')")
    page=await context.new_page();page.on('pageerror',lambda e:REPORT['errors'].append({'message':str(e),'stack':e.stack}))
    await prepare(page)
    for text_scale in [1,2]:
     await page.locator('.site-header').evaluate('(e,s)=>{e.style.setProperty("--header-meta-font",(13*s)+"px");e.style.setProperty("--header-book-font",(16*s)+"px")}',text_scale)
     for height in [900,420]:
      for width in WIDTHS:
       await page.mouse.move(1,1);await page.keyboard.press('Escape');await page.set_viewport_size({'width':width,'height':height});await page.wait_for_timeout(60)
       case={'width':width,'height':height,'theme':theme,'textScale':text_scale}
       value=await page.evaluate(SAMPLE);value['case']=case;REPORT['cases'].append(value)
       if value['height']>(65 if text_scale==1 else 82):REPORT['findings'].append({'kind':'header-height','details':value})
       if value['overlap'] or any(g['scroll']>g['width']+1 for g in value['groups']):REPORT['findings'].append({'kind':'header-overflow','details':value})
       for item in value['items']:
        is_logo='header-logo' in item['class'];b=item['bounds'];
        if b['height']/value['scale']<43.9 or b['width']/value['scale']<43.9 or item['lines']>1 or item['clipped'] or (not is_logo and min(item['paddingLeft'],item['paddingRight'])<12):REPORT['findings'].append({'kind':'control-label-hit','case':case,'item':item})
        if abs(b['centerY']-value['capsule']['centerY'])>.6:REPORT['findings'].append({'kind':'second-row','case':case,'item':item})
       if width in [961,1047,1100,1440] and height==420:
        for selector in ['.more-menu','.header-contact']+(['.header-hours-menu'] if value['hoursVisible'] else []):await popup(page,selector,case)
       if height==900 and width in [961,1047,1100,1280,1366,1440,1920]:await page.locator('.site-header').screenshot(path=str(OUT/f'header-{width}-{theme}-text{text_scale*100}.png'))
    await context.close()
   # Representative normal-motion floating header at the screenshot's pixel scale.
   context=await browser.new_context(viewport={'width':1047,'height':800},device_scale_factor=1.25,reduced_motion='no-preference')
   page=await context.new_page();await prepare(page)
   await page.evaluate("document.querySelector('.site-header').classList.add('is-floating')")
   await page.wait_for_timeout(420)
   await popup(page,'.header-contact',{'width':1047,'motion':'normal','floating':True,'dpr':1.25})
   await page.locator('.site-header').screenshot(path=str(OUT/'1047-css-floating-dpr125.png'))
   await page.mouse.click(5,5);await page.wait_for_timeout(180)
   await page.locator('.site-header').screenshot(path=str(OUT/'1047-css-floating-dpr125-neutral.png'))
   await context.close()
   for theme in ['light','dark']:
    for hour,state,color in [(7,'closed','rgb(196, 47, 42)'),(12,'open','rgb(111, 190, 122)'),(18,'closing','rgb(255, 204, 41)')]:
     context=await browser.new_context(viewport={'width':1440,'height':480},color_scheme=theme,reduced_motion='reduce')
     page=await context.new_page();page.on('pageerror',lambda e:REPORT['errors'].append({'message':str(e),'stack':e.stack}))
     await page.clock.install(time=datetime.fromisoformat(f'2026-11-16T{hour:02}:00:00+00:00'));await prepare(page)
     await page.locator('.header-hours-menu>summary').hover();await page.wait_for_function("document.querySelector('.header-hours-menu').open")
     value=await page.locator('.header-hours-menu [data-business-hours-status]').evaluate("e=>({state:e.dataset.state,color:getComputedStyle(e,'::before').backgroundColor,width:getComputedStyle(e,'::before').width})")
     value.update({'theme':theme,'expected':state});REPORT['clockStatus'].append(value)
     if value['state']!=state or value['color']!=color or value['width']!='8px':REPORT['findings'].append({'kind':'clock-status','details':value})
     await page.locator('.site-header').screenshot(path=str(OUT/f'{theme}-status-{state}.png'));await context.close()
   await browser.close()
 except Exception as error:
  REPORT['exception']=repr(error);REPORT['findings'].append({'kind':'runner-exception','details':repr(error)})
 finally:
  if len({(p['bg'],p['radius'],p['color']) for p in REPORT['popups']})>1:REPORT['findings'].append({'kind':'popup-style-unification'})
  REPORT['sourceEnd']=hashes();REPORT['sourceChanged']=REPORT['sourceStart']!=REPORT['sourceEnd'];REPORT['finished']=datetime.now(timezone.utc).isoformat()
  (OUT/'report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({'cases':len(REPORT['cases']),'popups':len(REPORT['popups']),'keyboard':len(REPORT['keyboard']),'clockStatus':len(REPORT['clockStatus']),'errors':REPORT['errors'],'findings':REPORT['findings'],'sourceChanged':REPORT['sourceChanged']},ensure_ascii=True))

asyncio.run(main())
raise SystemExit(bool(REPORT['errors'] or REPORT['findings'] or REPORT['sourceChanged']))
