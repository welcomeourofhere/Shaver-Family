"""Live CDP device switching, pointer/keyboard skip access, resolved browser metadata."""
import argparse,base64,hashlib,json,re,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[\w-]+',args.label);assert urlsplit(args.origin).hostname in ['localhost','127.0.0.1']
OUT=ROOT/'artifacts/iteration67/device-switch'/args.label;OUT.mkdir(parents=True,exist_ok=False);host=urlsplit(args.origin).netloc
def hashes():return{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((ROOT/'src').rglob('*'))if p.is_file()}
report={'origin':args.origin,'sourceStart':hashes(),'cases':[],'pageErrors':[],'boundary':'Chrome on Windows, CDP metrics+touch+UA changes without reload. No physical Android/browser toolbar colour acceptance. Providers blocked for local source QA.'}
SAMPLE="""()=>{const root=document.documentElement,skip=document.querySelector('.skip'),s=getComputedStyle(root),rect=q=>{const e=document.querySelector(q);return e?e.getBoundingClientRect().toJSON():null};return{inner:[innerWidth,innerHeight],compact:matchMedia('(max-width:960px)').matches,coarse:matchMedia('(pointer:coarse)').matches,ua:navigator.userAgent,overflow:root.scrollWidth-innerWidth,theme:root.dataset.theme,surface:s.getPropertyValue('--surface').trim(),scheme:s.colorScheme,metas:[...document.querySelectorAll('meta[name="theme-color"],meta[name="color-scheme"]')].map(e=>({name:e.name,content:e.content,media:e.media})),header:rect('.site-header'),dock:rect('[data-mobile-nav]'),reviews:document.querySelector('[data-review-bento]')?.dataset.reviewFormat,menu:{open:document.querySelector('#mobile-menu').open,owned:document.querySelector('#mobile-menu').dataset.dockOwned,locked:document.body.dataset.modalScrollLocked},skip:{rect:skip.getBoundingClientRect().toJSON(),focused:skip===document.activeElement,visibleFocus:skip.matches(':focus-visible'),modality:root.dataset.inputModality},main:{active:document.activeElement?.id==='main',tabIndex:document.querySelector('#main').tabIndex,outline:getComputedStyle(document.querySelector('#main')).outlineStyle}}}"""
def meta_check(data):
 for name,value in [('theme-color',data['surface']),('color-scheme',data['theme'])]:
  found=[m for m in data['metas']if m['name']==name];assert len(found)==1 and found[0]['content']==value and found[0]['media']=='',found
 assert data['scheme']==data['theme'],data
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome',args=['--mute-audio'])
 try:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme=theme,reduced_motion='reduce');context.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==host else r.abort());page=context.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_function("document.querySelector('#mobile-menu')?.dataset.dockOwned==='true'&&document.querySelector('[data-review-bento]')?.dataset.bentoReady==='true'");prompt=page.locator('[data-analytics-prompt]')
   if prompt.is_visible():prompt.locator('.analytics-choice-close').click();prompt.wait_for(state='hidden')
   cdp=context.new_cdp_session(page);time_origin=page.evaluate('performance.timeOrigin')
   sequence=[('desktop',1440,1000,False),('phone',390,844,True),('tablet',820,1180,True),('landscape',932,430,True),('desktop-return',1440,1000,False),('phone-return',430,932,True),('compact-edge',960,900,True),('desktop-edge',961,900,False)]
   for label,width,height,mobile in sequence:
    row={'name':label,'theme':theme,'width':width,'height':height}
    try:
     ua='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Mobile Safari/537.36'if mobile else'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
     cdp.send('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':2 if mobile else 1,'mobile':mobile,'screenWidth':width,'screenHeight':height});cdp.send('Emulation.setTouchEmulationEnabled',{'enabled':mobile});cdp.send('Emulation.setUserAgentOverride',{'userAgent':ua});page.wait_for_timeout(200)
     data=page.evaluate(SAMPLE);row['state']=data;meta_check(data);compact=width<=960
     assert data['inner']==[width,height]and data['compact']==compact and data['coarse']==mobile and data['overflow']<=1,data
     assert (data['header']['width']==0)==compact and(data['dock']['width']>0)==compact and data['reviews']==('phone'if compact else'module'),data
     assert data['menu']['owned']=='true'
     if not compact:assert not data['menu']['open']and data['menu']['locked']is None,data
     elif not data['menu']['open']:
      box=page.locator('[data-open-menu]').first.bounding_box();point={'x':box['x']+box['width']/2,'y':box['y']+box['height']/2};cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_function('document.querySelector("#mobile-menu").open');row['actualTrustedTouchOpenedMenu']=True
     row['timeOrigin']=page.evaluate('performance.timeOrigin');assert row['timeOrigin']==time_origin
     if label in ['phone','desktop-return']:
      image=cdp.send('Page.captureScreenshot',{'format':'png'});(OUT/f'{theme}-{label}.png').write_bytes(base64.b64decode(image['data']))
     row['pass']=True
    except Exception:row['pass']=False;row['failure']=traceback.format_exc()
    report['cases'].append(row)
   # Real owner controls, then a host-duplicate metadata fixture. No root/body styling fixture.
   row={'name':'runtime-os-manual-and-duplicates','theme':theme}
   try:
    opposite='dark'if theme=='light'else'light';page.emulate_media(color_scheme=opposite);page.wait_for_timeout(50);data=page.evaluate(SAMPLE);meta_check(data);assert data['theme']==opposite
    page.evaluate("for(const name of ['theme-color','color-scheme']){const e=document.createElement('meta');e.name=name;e.content='incorrect-host-fixture';e.media='(prefers-color-scheme:dark)';document.head.append(e)}")
    page.locator('[data-site-settings]').click();page.locator('#site-settings-panel [data-theme-toggle]').click();data=page.evaluate(SAMPLE);meta_check(data);assert data['theme']==theme;page.emulate_media(color_scheme=theme);page.wait_for_timeout(50);meta_check(page.evaluate(SAMPLE));page.locator('[data-site-settings]').click();row['pass']=True;row['state']=data
   except Exception:row['pass']=False;row['failure']=traceback.format_exc()
   report['cases'].append(row)
   row={'name':'skip-pointer-keyboard-enter','theme':theme}
   try:
    page.mouse.click(940,300);page.locator('.skip').focus();data=page.evaluate(SAMPLE);row['pointerState']=data;assert data['skip']['modality']=='pointer'and data['skip']['rect']['bottom']<=0,data
    page.keyboard.press('Tab');page.keyboard.press('Shift+Tab');data=page.evaluate(SAMPLE);row['keyboardState']=data;assert data['skip']['focused']and data['skip']['rect']['y']>=0 and data['skip']['modality']=='keyboard',data
    page.keyboard.press('Enter');data=page.evaluate(SAMPLE);assert data['main']['active']and data['main']['tabIndex']==-1 and data['skip']['rect']['bottom']<=0,data;row['pass']=True;row['state']=data
   except Exception:row['pass']=False;row['failure']=traceback.format_exc()
   report['cases'].append(row);context.close()
  context=browser.new_context(viewport={'width':1440,'height':1000},java_script_enabled=False);context.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==host else r.abort());page=context.new_page();row={'name':'no-js-native-skip'}
  try:
   page.goto(args.origin,wait_until='domcontentloaded');page.keyboard.press('Tab');assert page.locator('.skip').evaluate('e=>e===document.activeElement&&e.getBoundingClientRect().top>=0');page.keyboard.press('Enter');assert page.locator('#main').evaluate('e=>e===document.activeElement');row['pass']=True
  except Exception:row['pass']=False;row['failure']=traceback.format_exc()
  report['cases'].append(row);context.close()
 finally:browser.close()
report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['passed']=sum(row['pass']for row in report['cases']);report['failed']=len(report['cases'])-report['passed'];(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':report['passed'],'failed':report['failed'],'errors':report['pageErrors'],'sourceUnchanged':report['sourceUnchanged'],'result':str(OUT/'results.json')},ensure_ascii=False));assert report['failed']==0 and not report['pageErrors']and report['sourceUnchanged']
