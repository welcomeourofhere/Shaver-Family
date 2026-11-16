"""Read-only HMR QA for footer composition and adaptive floating controls.
No real booking/payment/account changes. Does not run performance benchmarks.
"""
import argparse, asyncio, hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--origin',default='http://127.0.0.1:4321/')
parser.add_argument('--label',required=True)
parser.add_argument('--phase',choices=['layout','floating','all'],default='all')
parser.add_argument('--channel',default='msedge')
parser.add_argument('--widths',type=int,nargs='+',default=[961,1024,1100,1280,1440,320,390,700,800],help='Layout widths; floating always checks five desktop widths')
args=parser.parse_args()
out=ROOT/'artifacts/iteration66/footer-utilities'/args.label
out.mkdir(parents=True,exist_ok=False)
paths=['src/styles/footer.css','src/styles/site-settings.css','src/scripts/site-settings.ts','src/scripts/floating-tone.ts']
def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}
report={'started':datetime.now(timezone.utc).isoformat(),'origin':args.origin,'sourceStart':hashes(),'layout':[],'floating':[],'errors':[],'findings':[]}
SAMPLE_FOOTER="""()=>{
 const footer=document.querySelector('.footer'),card=footer.querySelector('.footer-card'),bounds=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}},fr=bounds(footer),cr=bounds(card);
 const controls=[...footer.querySelectorAll('a,button')].filter(e=>e.getClientRects().length&&!e.matches('.footer-logo,.footer-address')&&!e.closest('.info-panel'));
 const data=controls.map(e=>{const r=bounds(e),s=getComputedStyle(e),walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),tops=[];let node;while(node=walker.nextNode()){if(!node.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(node);for(const box of range.getClientRects())if(box.width&&box.height&&!tops.some(top=>Math.abs(top-box.top)<1))tops.push(box.top);}
 return {tag:e.tagName,class:e.className,label:e.innerText?.trim()||e.getAttribute('aria-label'),lines:tops.length,paddingLeft:parseFloat(s.paddingLeft),paddingRight:parseFloat(s.paddingRight),clipped:e.scrollWidth>e.clientWidth+1,legal:e.matches('.footer-legal>a'),icon:e.matches('.contact-channel'),bounds:r};});
 return {theme:document.documentElement.dataset.theme,footer:fr,card:cr,groups:[...footer.querySelector('.footer-panel').children].map(e=>({class:e.className,bounds:bounds(e)})),legal:[...footer.querySelectorAll('.footer-legal>a')].map(e=>({text:e.innerText.trim(),href:e.getAttribute('href'),bounds:bounds(e)})),controls:data,pageOverflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,footerOverflow:footer.scrollWidth>footer.clientWidth+1,blankBelowNav:cr.bottom-bounds(footer.querySelector('.footer-groups')).bottom};
}"""
SAMPLE_FLOATING="""()=>{
 const palette=['red','blue','yellow','ink','paper'],rgb=x=>x.startsWith('#')?x.slice(1).match(/../g).map(v=>parseInt(v,16)):x.match(/[\\d.]+/g)?.slice(0,3).map(Number),root=getComputedStyle(document.documentElement),colors=Object.fromEntries(palette.map(n=>[n,rgb(root.getPropertyValue('--'+n).trim())]));
 const same=(a,b)=>a&&b&&a.every((v,i)=>Math.abs(v-b[i])<3),tone=c=>palette.find(n=>same(rgb(c),colors[n]));
 return ['.settings-toggle','.back-to-top'].map(selector=>{const button=document.querySelector(selector),b=button.getBoundingClientRect(),s=getComputedStyle(button),visible=!!button.getClientRects().length&&!button.hidden;let under;
 for(const e of document.elementsFromPoint(b.x+b.width/2,b.y+b.height/2)){if(e.closest('.site-settings,.back-to-top'))continue;const css=getComputedStyle(e);if(e.matches('img,video,iframe')||css.backgroundImage!=='none'){under={kind:'media',tag:e.tagName,class:e.className};break;}if(css.backgroundColor==='transparent'||css.backgroundColor==='rgba(0, 0, 0, 0)')continue;under={kind:'solid',tag:e.tagName,class:e.className,color:css.backgroundColor,tone:tone(css.backgroundColor)};break;}
 const svg=button.querySelector('svg'),path=svg?.querySelector('path,polyline,circle'),icon=path?getComputedStyle(path):null;
 return {selector,visible,tone:button.dataset.floatingTone,selectionSurface:button.dataset.selectionSurface,background:s.backgroundColor,backgroundTone:tone(s.backgroundColor),foreground:s.color,transition:s.transitionDuration,bounds:{x:b.x,y:b.y,width:b.width,height:b.height},under,icon:{exists:!!path,stroke:icon?.stroke,fill:icon?.fill,svgWidth:svg?.getBoundingClientRect().width,svgHeight:svg?.getBoundingClientRect().height}};
 });
}"""
def finding(kind,case,details,severity='failure'):report['findings'].append({'kind':kind,'severity':severity,'case':case,'details':details})
def contrast(a,b):
 def channels(x):return [float(n)/255 for n in re.findall(r'[\d.]+',x)[:3]]
 def lum(x):
  vals=[n/12.92 if n<=.04045 else ((n+.055)/1.055)**2.4 for n in channels(x)]
  return sum(a*b for a,b in zip(vals,[.2126,.7152,.0722]))
 la,lb=sorted([lum(a),lum(b)]);return (lb+.05)/(la+.05)
async def init(context):
 await context.add_init_script("localStorage.setItem('soyuz.analytics.v1','denied');")
async def prepare(page):
 for attempt in range(3):
  try:
   await page.goto(args.origin,wait_until='domcontentloaded');break
  except Exception as error:
   if attempt==2 or 'ERR_ABORTED' not in str(error):raise
   await page.wait_for_timeout(250)
 await page.evaluate('document.fonts.ready')
 await page.locator('.footer').wait_for()
 await page.wait_for_timeout(450)
async def layout(browser):
 titles=[p['title'] for p in json.loads((ROOT/'content/legal/pages.json').read_text(encoding='utf-8'))['pages']]
 for theme in ['light','dark']:
  context=await browser.new_context(viewport={'width':1440,'height':1000},color_scheme=theme,reduced_motion='reduce');await init(context)
  page=await context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
  for width in args.widths:
   await page.set_viewport_size({'width':width,'height':1000 if width>960 else 900})
   await prepare(page)
   for enlarged in [False,True]:
    if enlarged:
     await page.evaluate("""()=>{const values=[...document.querySelectorAll('.footer a,.footer button,.footer p,.footer h2,.footer-location')].map(e=>[e,parseFloat(getComputedStyle(e).fontSize)*2]);for(const[e,size]of values)e.style.fontSize=size+'px'}""")
    await page.evaluate('scrollTo(0,document.documentElement.scrollHeight)');await page.wait_for_timeout(250)
    data=await page.evaluate(SAMPLE_FOOTER);case={'width':width,'theme':theme,'textScale':2 if enlarged else 1};data.update(case);report['layout'].append(data)
    if data['footerOverflow']:finding('footer-overflow',case,{'width':data['footer']['width']})
    if data['pageOverflow']:finding('page-overflow',case,'Root scrollWidth exceeds clientWidth; ownership may be outside footer')
    normalized=lambda x:' '.join(x.split())
    if sorted(map(normalized,[x['text'] for x in data['legal']]))!=sorted(map(normalized,titles)):finding('legal-full-title',case,data['legal'])
    bad_hit=[x for x in data['controls'] if x['bounds']['height']<43.9 or x['bounds']['width']<43.9]
    if bad_hit:finding('hit-area',case,bad_hit)
    bad_labels=[x for x in data['controls'] if not x['icon'] and not x['legal'] and (x['lines']>1 or x['clipped'])]
    if bad_labels:finding('action-label',case,bad_labels)
    multiline_legal=[x for x in data['controls'] if x['legal'] and x['lines']>1]
    if multiline_legal:finding('legal-multiline',case,multiline_legal,'review')
    cr=data['card'];outside=[x for x in data['controls'] if x['bounds']['x']<cr['x']-1 or x['bounds']['right']>cr['right']+1]
    if outside:finding('outside-footer-card',case,outside)
    stem=f'footer-{width}-{theme}'+('-text200' if enlarged else '')
    if not enlarged or width in [320,390,700,961,1024]:
     if width<=960:
      await page.locator('.footer').evaluate('(e)=>scrollTo(0,e.getBoundingClientRect().top+scrollY)');await page.wait_for_timeout(100)
     await page.locator('.footer').screenshot(path=str(out/(stem+'.png')))
     await page.evaluate('scrollTo(0,document.documentElement.scrollHeight)');await page.screenshot(path=str(out/(stem+'-viewport.png')))
  await context.close()
async def floating(browser):
 for theme in ['light','dark']:
  for width in [961,1024,1100,1280,1440]:
   context=await browser.new_context(viewport={'width':width,'height':1000},color_scheme=theme,reduced_motion='no-preference');await init(context);page=await context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));await prepare(page);await page.wait_for_function("document.querySelector('.settings-toggle')?.dataset.floatingTone")
   offsets=await page.evaluate("""()=>{const max=document.documentElement.scrollHeight-innerHeight;return [...new Set([...document.querySelectorAll('main>section,footer')].flatMap(e=>{const r=e.getBoundingClientRect();return [Math.max(0,Math.min(max,scrollY+r.top-innerHeight*.3)),Math.max(0,Math.min(max,scrollY+r.top+r.height*.6-innerHeight*.7))]}))].sort((a,b)=>a-b)}""")
   captured=set()
   for pos in offsets:
    await page.mouse.move(width/2,5);await page.evaluate('(y)=>scrollTo(0,y)',pos);await page.wait_for_timeout(240)
    await page.wait_for_function("['.settings-toggle','.back-to-top'].every(s=>!document.querySelector(s).getAnimations().some(a=>a.playState==='running'))");buttons=await page.evaluate(SAMPLE_FLOATING);entry={'width':width,'theme':theme,'scrollY':await page.evaluate('scrollY'),'buttons':buttons};report['floating'].append(entry)
    for button in buttons:
     if not button['visible']:continue
     case={'width':width,'theme':theme,'scrollY':entry['scrollY'],'selector':button['selector']}
     if not button['backgroundTone']:finding('floating-not-palette',case,button)
     if button['tone']!=button['backgroundTone']:finding('floating-tone-owner',case,button)
     under=button.get('under') or {}
     if under.get('tone') in ['red','blue','yellow','ink'] and under['tone']==button['backgroundTone']:finding('floating-matches-surface',case,button)
     ratio=contrast(button['foreground'],button['background']);button['glyphContrast']=ratio
     if ratio<3:finding('floating-glyph-contrast',case,button)
     if not button['icon']['exists'] or button['icon']['svgWidth']<20:finding('floating-icon',case,button)
     key=button['selector']+'-'+str(under.get('tone'))
     if under.get('tone') in ['red','blue','yellow','ink'] and key not in captured:
      captured.add(key);stem=f'floating-{width}-{theme}-{button["selector"][1:]}-on-{under["tone"]}';await page.screenshot(path=str(out/(stem+'.png')))
      await page.locator(button['selector']).hover();await page.wait_for_function("['.settings-toggle','.back-to-top'].every(s=>!document.querySelector(s).getAnimations().some(a=>a.playState==='running'))");hover=(await page.evaluate(SAMPLE_FLOATING))[0 if button['selector']=='.settings-toggle' else 1];entry.setdefault('hover',[]).append(hover)
      if hover.get('backgroundTone')==under.get('tone'):finding('floating-hover-matches-surface',case,hover)
      if contrast(hover['foreground'],hover['background'])<3:finding('floating-hover-glyph-contrast',case,hover)
   await page.evaluate('scrollTo(0,document.documentElement.scrollHeight)');await page.wait_for_timeout(240)
   await page.locator('[data-site-settings]').click();await page.wait_for_timeout(160);panel=page.locator('#site-settings-panel');shown=await panel.is_visible();entry={'width':width,'theme':theme,'panelShown':shown,'panelButtons':await panel.locator('button').count()};report.setdefault('settingsPanel',[]).append(entry)
   await page.screenshot(path=str(out/f'settings-panel-{width}-{theme}.png'));await panel.locator('[data-theme-toggle]').click();await page.wait_for_timeout(260);entry['themeFlipped']=await page.evaluate('document.documentElement.dataset.theme')!=theme;entry['themeIcon']=await panel.locator('[data-theme-toggle]').evaluate("e=>({pressed:e.getAttribute('aria-pressed'),sun:getComputedStyle(e.querySelector('.sun')).opacity,moon:getComputedStyle(e.querySelector('.moon')).opacity})");await page.keyboard.press('Escape');entry['escapeClosed']=not await panel.is_visible();entry['focusRestored']=await page.locator('[data-site-settings]').evaluate('(e)=>e===document.activeElement')
   if not all([shown,entry['escapeClosed'],entry['focusRestored'],entry['themeFlipped']]):finding('settings-panel',{'width':width,'theme':theme},entry)
   await context.close()
async def main():
 try:
  async with async_playwright() as p:
   browser=await p.chromium.launch(channel=args.channel,headless=True)
   if args.phase in ['layout','all']:await layout(browser)
   if args.phase in ['floating','all']:await floating(browser)
   await browser.close()
 except Exception as exc:
  report['exception']=repr(exc);finding('runner-exception',{},repr(exc))
 finally:
  report['sourceEnd']=hashes();report['sourceChanged']=report['sourceStart']!=report['sourceEnd'];report['finished']=datetime.now(timezone.utc).isoformat();(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  summary={'out':str(out),'layoutCases':len(report['layout']),'floatingSamples':len(report['floating']),'errors':len(report['errors']),'sourceChanged':report['sourceChanged'],'findings':{kind:sum(x['kind']==kind for x in report['findings']) for kind in set(x['kind'] for x in report['findings'])}}
  print(json.dumps(summary,ensure_ascii=True))
asyncio.run(main())
raise SystemExit(bool(report['errors'] or report.get('exception') or report['sourceChanged'] or any(row['severity']=='failure' for row in report['findings'])))
