"""Regressions found by the whole-site visual audit, on actual viewport geometry."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/planning/iteration65/visual-fixes';OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('QA_URL','http://127.0.0.1:4321/')
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
rows=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width,height in [(320,568),(390,844),(600,400),(961,600),(1024,600),(1440,900)]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
   context.add_init_script("localStorage.setItem('soyuz_theme','"+theme+"')")
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(URL,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(400)
   # Every cover must retain its intrinsic frame, even on a short viewport.
   for trigger in page.locator('[data-team-open]').all():
    # Native carousel selection uses the first click to select a neighbour.
    trigger.scroll_into_view_if_needed();trigger.click();page.wait_for_timeout(100)
    dialog=page.locator('.team-story-dialog[open]')
    if not dialog.count():trigger.click();dialog.wait_for(state='visible')
    cover=dialog.locator('.story-cover>img');cover.evaluate('e=>e.decode()')
    frame=cover.evaluate('e=>({w:e.clientWidth,h:e.clientHeight,nw:e.naturalWidth,nh:e.naturalHeight})')
    assert abs(frame['w']/frame['h']-frame['nw']/frame['nh'])<.01,frame
    close=dialog.locator('.story-dialog-head button')
    contrast=close.evaluate(r'''e=>{const rgb=s=>s.match(/[\d.]+/g).slice(0,3).map(Number),lum=c=>c.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0),s=getComputedStyle(e),a=lum(rgb(s.color)),b=lum(rgb(s.backgroundColor));return(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}''')
    assert contrast>=3,(width,theme,'invisible close icon',contrast)
    heading=dialog.locator('.story-heading')
    assert heading.evaluate('e=>e.scrollWidth<=e.clientWidth+1'),(width,'heading overflow')
    if trigger.get_attribute('data-team-open')=='souz-svetlana' and width==320:
     lines=heading.evaluate('''e=>{const n=e.querySelector('h2').firstChild,r=document.createRange(),ls=[];for(let i=0;i<n.length;i++){r.setStart(n,i);r.setEnd(n,i+1);const y=r.getBoundingClientRect().y;let l=ls.find(l=>Math.abs(l.y-y)<1);if(!l)ls.push(l={y,text:''});l.text+=n.textContent[i]}return ls.map(l=>l.text.trim())}''')
     assert not any(x in ['.',',','!','?']for x in lines),lines
    if trigger.get_attribute('data-team-open')=='souz-svetlana':page.screenshot(path=str(OUT/f'story-{width}-{theme}.png'))
    close.click();dialog.wait_for(state='hidden')
   page.locator('#contacts').scroll_into_view_if_needed()
   spacing=page.locator('.contact-person').evaluate_all('''es=>es.map(e=>{const a=e.querySelector('h3'),b=e.querySelector('.contact-person-links a:last-child'),r=document.createRange();r.selectNodeContents(b);const box=e.getBoundingClientRect(),first=a.getBoundingClientRect(),last=r.getBoundingClientRect();return{top:first.top-box.top,bottom:box.bottom-last.bottom}})''')
   assert all(abs(x['top']-x['bottom'])<=6 for x in spacing),(width,spacing)
   if width>960:
    page.locator('.footer').scroll_into_view_if_needed();page.evaluate('scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})');page.wait_for_timeout(100)
    collisions=page.locator('.footer-legal a').evaluate_all('''es=>{const buttons=[...document.querySelectorAll('.settings-toggle,.back-to-top')].map(e=>e.getBoundingClientRect());return es.filter(e=>{const a=e.getBoundingClientRect();return buttons.some(b=>Math.min(a.right,b.right)>Math.max(a.left,b.left)&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top))}).map(e=>e.textContent)}''')
    assert not collisions,(width,'fixed control covers legal link',collisions)
   # Enlarge the text itself, preserving the viewport and control padding.
   page.evaluate('''()=>{const es=[...document.querySelectorAll('h1,h2,h3,p,small,a,button,summary,dt,dd,figcaption,label,legend')],sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}''')
   page.wait_for_timeout(250)
   for summary in page.locator('.sd-card .sd-summary').all():
    assert summary.evaluate('''e=>{const a=e.querySelector('.sd-service-main').getBoundingClientRect(),b=e.querySelector('.sd-price').getBoundingClientRect();return a.right<=b.left+1||a.bottom<=b.top+1}'''),(width,'service name overlaps price')
   assert page.locator('.contact-person h3>span').evaluate_all('''es=>es.every(e=>e.getBoundingClientRect().height<=parseFloat(getComputedStyle(e).lineHeight)+1&&e.scrollWidth<=e.clientWidth+1)'''),(width,'contact name chopped at enlarged text')
   if width==320:
    page.locator('.contact-person').first.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'contacts-320-text200-{theme}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,'root overflow')
   assert not errors,errors
   rows.append({'width':width,'height':height,'theme':theme,'passed':True});context.close()
 browser.close()
(OUT/f'{args.engine}.json').write_text(json.dumps({'url':URL,'engine':args.engine,'cases':rows},indent=2),encoding='utf-8')
print('PASS visual fixes',args.engine,len(rows),'cases')
