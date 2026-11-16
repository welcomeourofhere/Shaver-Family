"""Permanent native scrollbars: complete caps, no hover resize or inactivity hiding."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321/');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/scrollbars';OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
def rgb(page,name):
 return page.evaluate('''name=>{const c=document.createElement('canvas').getContext('2d');c.fillStyle=getComputedStyle(document.documentElement).getPropertyValue(name).trim();c.fillRect(0,0,1,1);return[...c.getImageData(0,0,1,1).data].slice(0,3)}''',name)
def pixels(path,right,color,top=0,bottom=None):
 image=Image.open(path).convert('RGB');right=round(right);hits=[]
 for y in range(max(0,round(top)),min(image.height,round(bottom)if bottom is not None else image.height)):
  def matches(x):
   pixel=image.getpixel((x,y))
   return pixel[0]-pixel[1]>40 and pixel[0]-pixel[2]>40 if args.engine=='firefox'else max(abs(pixel[i]-color[i])for i in range(3))<8
  xs=[x for x in range(max(0,right-8),min(right,image.width))if matches(x)]
  if xs:hits.append({'count':len(xs),'left':min(xs),'right':max(xs),'y':y})
 assert hits,('native scrollbar not painted',path,right,color)
 width=max(r['count']for r in hits);wide=[r for r in hits if r['count']==width];first,last=hits[0]['y'],hits[-1]['y'];mid=wide[len(wide)//2]
 return{'width':width,'right':mid['right'],'top':first,'bottom':last,'caps':[r['count']for r in hits[:4]],'symmetry':[max(abs(image.getpixel((right-4,y))[c]-image.getpixel((right-1,y))[c])for c in range(3))for y in range(first,min(first+3,last+1))]}
def capture(page,host,name,hover=False):
 box=host.bounding_box();right=page.viewport_size['width']if host.locator(':scope').evaluate('e=>e===document.documentElement')else box['x']+box['width']
 path=OUT/f'{args.engine}-{name}.png';page.screenshot(path=str(path))
 try:
  top=box['y']+24 if args.engine=='firefox'else 0
  bottom=box['y']+box['height']-24 if args.engine=='firefox'else None
  return pixels(path,right,rgb(page,'--blue'if hover else'--scrollbar-thumb'),top,bottom)
 except AssertionError:
  if args.engine!='firefox':raise
  return{'width':None,'nativeOverlayNotCaptured':True}
def native_shape(value,right):
 if args.engine!='firefox':
  assert value['width']==4 and value['right']==round(right)-1,value
  assert value['caps'][0]<4 and max(value['symmetry'])<=8,('thumb has clipped half-caps',value)

with sync_playwright()as p:
 # Firefox's headless test shell forces scrollbar-width:none, even over !important.
 launch={'headless':False,'firefox_user_prefs':{'layout.testing.overlay-scrollbars.always-visible':True}}if args.engine=='firefox'else({'channel':'chrome','ignore_default_args':['--hide-scrollbars']}if args.engine=='chromium'else{})
 browser=getattr(p,args.engine).launch(**launch)
 for theme in ['light','dark']:
  for motion in ['no-preference','reduce']:
   context=browser.new_context(viewport={'width':1440,'height':900},color_scheme=theme,reduced_motion=motion);page=context.new_page();page.on('pageerror',lambda e:errors.append(e.stack));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_function('document.readyState==="complete"&&document.fonts.status==="loaded"');page.bring_to_front();page.mouse.move(100,200);page.wait_for_timeout(1300)
   root=page.locator('html');normal=capture(page,root,f'{theme}-{motion}-normal');native_shape(normal,1440)
   assert page.locator('[data-scrollbar-active],[data-scrollbar-managed]').count()==0
   baseline_client=root.evaluate('e=>e.clientWidth');thumb_height=page.evaluate('innerHeight*innerHeight/document.documentElement.scrollHeight')
   page.mouse.move(1438,max(8,thumb_height/2));page.wait_for_timeout(200)
   hover=capture(page,root,f'{theme}-{motion}-hover',hover=args.engine!='firefox');native_shape(hover,1440)
   if args.engine!='firefox':assert normal['width']==hover['width'],('hover resized native thumb',normal,hover)
   else:assert root.evaluate('e=>getComputedStyle(e).scrollbarWidth')=='thin'
   if normal['width'] is not None:
    page.mouse.down();page.wait_for_timeout(1200);held=capture(page,root,f'{theme}-{motion}-held',hover=args.engine!='firefox')
    if args.engine!='firefox':assert held['width']==normal['width']
    page.mouse.move(1438,500,steps=12);page.mouse.up();page.wait_for_timeout(250);assert page.evaluate('scrollY')>500,('native drag did not scroll',args.engine)
   else:held={'nativeOverlayNotCaptured':True}
   page.mouse.move(200,300);before=page.evaluate('scrollY');page.mouse.wheel(0,160);page.wait_for_timeout(500);assert page.evaluate('scrollY')>before
   assert root.evaluate('e=>e.clientWidth')==baseline_client
   # Real cookie window; its scrollport reaches the window's right edge.
   page.locator('.settings-toggle').click();page.locator('.settings-panel [data-analytics-settings]').click();page.locator('#cookie-settings').wait_for(state='visible');page.set_viewport_size({'width':1440,'height':600});page.wait_for_timeout(350)
   port=page.locator('#cookie-settings .surface-content');box=port.bounding_box();right=box['x']+box['width'];assert port.evaluate('e=>e.scrollHeight>e.clientHeight');page.mouse.move(300,300);page.wait_for_timeout(1100)
   nested=capture(page,port,f'{theme}-{motion}-window-normal');native_shape(nested,right)
   height=port.evaluate('e=>(e.clientHeight-48)*e.clientHeight/e.scrollHeight');page.mouse.move(right-2,box['y']+24+height/2);page.wait_for_timeout(180)
   nested_hover=capture(page,port,f'{theme}-{motion}-window-hover',hover=args.engine!='firefox');native_shape(nested_hover,right)
   if args.engine!='firefox':assert nested['width']==nested_hover['width']
   else:assert port.evaluate('e=>getComputedStyle(e).scrollbarWidth')=='thin'
   box=port.bounding_box();right=box['x']+box['width'];page.mouse.move(right-2,box['y']+24+height/2);page.mouse.down();page.mouse.move(right-2,box['y']+box['height']-30,steps=10);page.mouse.up();page.wait_for_timeout(200);assert port.evaluate('e=>e.scrollTop')>100
   port.evaluate('e=>{e.tabIndex=0;e.focus()}');page.keyboard.press('Home');page.wait_for_timeout(200);home=port.evaluate('e=>e.scrollTop');page.keyboard.press('End');page.wait_for_timeout(200);assert port.evaluate('e=>e.scrollTop')>home
   page.locator('#cookie-settings [data-dismiss]').click();page.wait_for_timeout(300)
   modes=[]
   for width in [959,960,961,962,964,968]:
    page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100)
    sample=page.evaluate('''async()=>{const s=[];for(let i=0;i<10;i++){await new Promise(requestAnimationFrame);s.push({compact:matchMedia('(max-width:960px)').matches,client:document.documentElement.clientWidth,overflow:document.documentElement.scrollWidth>innerWidth+1})}return s}''');assert len({(v['compact'],v['client'])for v in sample})==1 and not any(v['overflow']for v in sample),(width,sample);modes.append({'width':width,'frames':sample})
   assert not errors,errors
   rows.append({'theme':theme,'motion':motion,'rootNormal':normal,'rootHover':hover,'held':held,'windowNormal':nested,'windowHover':nested_hover,'responsive':modes,'firefoxNativeColorAndSize':args.engine=='firefox'});context.close()
 if args.engine=='chromium':
  context=browser.new_context(viewport={'width':390,'height':900},has_touch=True,is_mobile=True);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');page.locator('#faq').scroll_into_view_if_needed();page.wait_for_timeout(250);before=page.evaluate('scrollY');cdp=context.new_cdp_session(page);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':200,'y':600}]})
  for y in range(570,260,-30):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':200,'y':y}]});page.wait_for_timeout(20)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(300);after=page.evaluate('scrollY');assert after>before+100,(before,after);rows.append({'nativeTouch':True,'from':before,'to':after});context.close()
 browser.close()
(OUT/f'permanent-{args.engine}.json').write_text(json.dumps({'origin':args.origin,'engine':args.engine,'cases':rows,'errors':errors,'physicalDevice':False,'published':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',args.engine,len(rows),'native thin compatibility, nested drag/keyboard, wheel and 961px; viewport pixels follow OS overlay'if args.engine=='firefox'else'permanent native 4px, complete rounded caps, hover size, drag/wheel/keyboard and 961px')
