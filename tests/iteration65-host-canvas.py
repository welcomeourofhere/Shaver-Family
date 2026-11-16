"""Check the site's themed canvas through real/native Tilda host wrappers."""
import argparse,io,json,re
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--origin',required=True)
parser.add_argument('--engine',choices=['chromium','firefox','webkit'],required=True)
parser.add_argument('--label',required=True,help='A new evidence label; existing output is never overwritten')
args=parser.parse_args()
assert urlsplit(args.origin).scheme in ['http','https'] and not urlsplit(args.origin).query
assert re.fullmatch(r'[\w-]+',args.label),args.label
OUT=ROOT/'tmp/planning/iteration65/host-canvas'/args.label/args.engine
OUT.mkdir(parents=True,exist_ok=False)
report={'origin':args.origin,'engine':args.engine,'label':args.label,'cases':[],
        'requestInterception':False,'styleInjection':False,'bookingSubmitted':False}

def save():
 (OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 try:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':390,'height':900},color_scheme=theme,reduced_motion='reduce')
   context.add_init_script("localStorage.setItem('soyuz_theme','"+theme+"')")
   page=context.new_page();page.bring_to_front()
   try:
    page.goto(args.origin,wait_until='domcontentloaded',timeout=45000)
    page.evaluate('document.fonts.ready')
    page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'",timeout=30000)
    if page.locator('[data-analytics-prompt]').is_visible():page.locator('[data-analytics-choice=denied]').click()
    for width in [390,961,1440]:
     page.bring_to_front();page.set_viewport_size({'width':width,'height':900})
     page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
     row={'theme':theme,'width':width,'failures':[]}
     try:
      row['canvas']=page.evaluate('''()=>{
       const probe=document.createElement('span');probe.style.backgroundColor='var(--surface)';document.body.append(probe);
       const expected=getComputedStyle(probe).backgroundColor;probe.remove();
       return {theme:document.documentElement.dataset.theme,expected,compact:matchMedia('(max-width:960px)').matches,
        layers:['html','body','#allrecords','#t-header','#t-footer'].map(selector=>{const e=document.querySelector(selector);return e?{selector,background:getComputedStyle(e).backgroundColor,inline:e.getAttribute('style'),classes:e.className}:null})};
      }''')
      canvas=row['canvas'];layers=canvas['layers']
      if canvas['theme']!=theme:row['failures'].append('requested theme not active')
      if layers[0]['background']!=canvas['expected']:row['failures'].append('root background differs from --surface')
      for layer in layers[1:]:
       if not layer or layer['background']not in ['rgba(0, 0, 0, 0)','transparent']:
        row['failures'].append('opaque Tilda host: '+str(layer))
      page.locator('#contacts').evaluate('e=>scrollTo({top:Math.max(0,e.getBoundingClientRect().top+scrollY-180),behavior:"instant"})')
      page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
      image=page.screenshot(path=str(OUT/f'{theme}-{width}-body-gap.png'))
      row['canvasPixel']=list(Image.open(io.BytesIO(image)).convert('RGB').getpixel((8,200)))
      expected=[int(x)for x in re.findall(r'\d+',canvas['expected'])[:3]]
      if len(expected)!=3 or any(abs(a-b)>2 for a,b in zip(row['canvasPixel'],expected)):
       row['failures'].append('visible canvas pixel differs from --surface')
      page.locator('#contacts').screenshot(path=str(OUT/f'{theme}-{width}-contacts.png'))
      page.locator('.footer').scroll_into_view_if_needed()
      footer=Image.open(io.BytesIO(page.locator('.footer').screenshot(path=str(OUT/f'{theme}-{width}-footer.png')))).convert('RGB')
      row['footerCanvasPixels']=[list(footer.getpixel(point))for point in [(0,0),(footer.width-1,0),(0,12)]]
      if len(expected)!=3 or any(abs(a-b)>2 for pixel in row['footerCanvasPixels']for a,b in zip(pixel,expected)):
       row['failures'].append('visible shared footer canvas differs from --surface')
      row['rootWidth']=page.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})')
      if row['rootWidth']['scroll']>row['rootWidth']['viewport']+1:row['failures'].append('root horizontal overflow')
      for selector in ['#contacts','.footer']:
       if not page.locator(selector).evaluate('e=>e.scrollWidth<=e.clientWidth+1'):row['failures'].append(selector+' horizontal overflow')
      row['clientResources']=page.locator('script[src],link[rel=stylesheet]').evaluate_all('es=>es.map(e=>e.src||e.href).filter(x=>/Soyuz\\/releases\\/|\\/_astro\\//.test(x)).sort()')
     except Exception as error:row['failures'].append(str(error))
     report['cases'].append(row);save()
     print('FAIL'if row['failures']else'PASS',args.label,args.engine,theme,width,flush=True)
   finally:context.close()
 finally:browser.close()
report['failedCases']=sum(bool(row['failures'])for row in report['cases'])
report['passed']=len(report['cases'])==6 and report['failedCases']==0
save()
assert report['passed'],f"{args.label} {args.engine}: {report['failedCases']} of {len(report['cases'])} cases failed; {OUT/'result.json'}"
print('PASS host canvas',args.label,args.engine,len(report['cases']),'cases; browsers closed')
