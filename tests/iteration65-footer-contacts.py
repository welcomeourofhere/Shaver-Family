"""Final footer hierarchy, personal contact spacing and independent dark colour roles."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/planning/iteration65/footer-contacts';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
URL=os.environ.get('QA_URL','http://127.0.0.1:4321/')
rows=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width in [320,390,600,720,768,960,961,1024,1280,1440,1920]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
   context.add_init_script("localStorage.setItem('soyuz_theme','"+theme+"')")
   page=context.new_page();page.goto(URL,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(500)
   contact=page.locator('#contacts');contact.scroll_into_view_if_needed()
   for portrait in page.locator('.contact-portrait img').all():
    portrait.scroll_into_view_if_needed()
    page.wait_for_function('e=>e.complete&&e.naturalWidth>0',arg=portrait.element_handle())
    portrait.evaluate('e=>e.decode()')
   metrics=page.locator('.contact-person').evaluate_all('''es=>es.map(e=>{const r=e.getBoundingClientRect(),p=e.querySelector('.contact-portrait').getBoundingClientRect(),c=e.querySelector('.contact-person-copy').getBoundingClientRect(),links=[...e.querySelectorAll('[data-action-label]')].map(e=>e.getBoundingClientRect());return{x:r.x,y:r.y,w:r.width,photo:{top:p.top-r.top,bottom:r.bottom-p.bottom,left:p.left-r.left},side:c.left>=p.right,linkGap:links[1].top-links[0].bottom}})''')
   assert all(x['side']and max(x['photo'].values())-min(x['photo'].values())<1 for x in metrics),(width,theme,'portrait inset',metrics)
   assert all(6<=x['linkGap']<=10 for x in metrics),(width,'phone too far from Telegram',metrics)
   available=contact.evaluate('e=>e.clientWidth')
   if 700<=available<=960:
    assert abs(metrics[0]['y']-metrics[1]['y'])<1 and metrics[1]['x']>metrics[0]['x'],(width,'two personal cards should share a row',metrics)
   page.locator('.footer').scroll_into_view_if_needed()
   aligned=page.locator('.footer-contact').evaluate('''e=>{const n=e.querySelector('.footer-phone').querySelector('span:not(.mobile-action-short)'),r=document.createRange();r.selectNodeContents(n);return[r.getBoundingClientRect().left,e.querySelector('.contact-channels').getBoundingClientRect().left,e.querySelector('.footer-booking').getBoundingClientRect().left]}''')
   if width>=1280:assert max(aligned)-min(aligned)<=1,(width,'footer contacts left edge',aligned)
   if width==1440:
    tops=page.locator('.footer-nav-column').evaluate_all('es=>es.map(e=>e.getBoundingClientRect().top)')
    assert max(tops)-min(tops)<1,tops
    assert page.locator('.footer').bounding_box()['height']<450
    page.locator('.footer').screenshot(path=str(OUT/f'footer-{args.engine}-{theme}.png'))
   assert page.locator('.footer-legal a').count()==3
   assert not page.locator('.footer [data-analytics-settings]').count()
   if theme=='dark':
    assert page.locator('#sd-heading').evaluate('e=>getComputedStyle(e).color')=='rgb(255, 204, 41)'
    assert page.locator('html').evaluate("e=>getComputedStyle(e).getPropertyValue('--scrollbar-thumb').trim()")=='#c42f2a'
   page.evaluate('''()=>{const es=[...document.querySelectorAll('h1,h2,h3,p,small,a,button,summary,dt,dd,figcaption,label,legend')],sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);es.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}''');page.wait_for_timeout(500)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,'text200 horizontal overflow')
   assert page.locator('.footer').evaluate('''e=>[...e.querySelectorAll('a,button')].filter(x=>x.getBoundingClientRect().width).every(x=>x.scrollWidth<=x.clientWidth+1)'''),(width,'clipped footer action')
   assert page.locator('.contact-person h3>span').evaluate_all('es=>es.every(e=>e.scrollWidth<=e.clientWidth+1)'),(width,'clipped contact name')
   if width in [320,768,1440]and theme=='light':
    page.locator('.footer').screenshot(path=str(OUT/f'footer-{width}-{args.engine}-text200.png'))
    page.locator('.contact-person').first.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'contacts-{width}-{args.engine}-text200.png'))
   rows.append({'width':width,'theme':theme,'normal':True,'text200':True,'portraitInsets':metrics});context.close()
 browser.close()
(OUT/f'{args.engine}.json').write_text(json.dumps({'url':URL,'engine':args.engine,'cases':rows},indent=2),encoding='utf-8')
print('PASS footer/contacts',args.engine,len(rows),'normal + enlarged-text cases')
