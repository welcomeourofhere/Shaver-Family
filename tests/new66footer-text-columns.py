"""24 footer text-layout cases and real keyboard paths; providers blocked."""
import argparse
import hashlib
import json
import re
import traceback
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--origin',default='http://127.0.0.1:4321/')
parser.add_argument('--label',required=True)
args=parser.parse_args()
assert re.fullmatch(r'[\w-]+',args.label)
host=urlsplit(args.origin).netloc
assert urlsplit(args.origin).hostname in ['localhost','127.0.0.1']
OUT=ROOT/'tmp/planning/iteration66/footer-text'/args.label
OUT.mkdir(parents=True,exist_ok=False)
site=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
legal=json.loads((ROOT/'content/legal/pages.json').read_text(encoding='utf-8'))['pages']
operator=json.loads((ROOT/'content/legal/operator.json').read_text(encoding='utf-8'))
nav=['Услуги и цены','Мастера','Работы','Акции','Контакты и карта']
nav_ids=['services','masters','works','offers','contacts']
def source_hashes():
 return{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted((ROOT/'src').rglob('*'))if p.is_file()}
report={'origin':args.origin,'sourceStart':source_hashes(),'cases':[],'pageErrors':[],
        'boundary':'Chrome on Windows, local rendered browser QA at the recorded origin, blocked providers, no real contact/booking/purchase or publication.'}
SAMPLE="""e=>{
 const rect=x=>x.getBoundingClientRect().toJSON(),lineCount=x=>{const w=document.createTreeWalker(x,NodeFilter.SHOW_TEXT),tops=[];let n;while(n=w.nextNode())if(n.textContent.trim()){const r=document.createRange();r.selectNodeContents(n);for(const b of r.getClientRects())if(b.width&&!tops.some(t=>Math.abs(t-b.top)<1))tops.push(b.top)}return tops.length};
 const controls=[...e.querySelectorAll('.footer-links>a,.footer-hours button')].map(x=>{const s=getComputedStyle(x);return{label:x.innerText.trim(),href:x.getAttribute('href'),tag:x.tagName,button:x.matches('button,.btn'),booking:x.matches('[data-booking]'),rect:rect(x),font:s.fontSize,weight:s.fontWeight,padding:[parseFloat(s.paddingLeft),parseFloat(s.paddingRight)],lines:lineCount(x),clipped:x.scrollWidth>x.clientWidth+1,ellipsis:s.textOverflow==='ellipsis'}}),card=e.querySelector('.footer-card'),summary=e.querySelector('.footer-summary'),identity=e.querySelector('.footer-identity'),copy=e.querySelector('.footer-copyright');
 return{footer:rect(e),card:rect(card),overflow:e.scrollWidth>e.clientWidth+1,cardOverflow:card.scrollWidth>card.clientWidth+1,pageOverflow:document.documentElement.scrollWidth>innerWidth+1,controls,groups:[...e.querySelectorAll('.footer-group')].map(g=>({class:g.className,rect:rect(g),heading:{text:g.querySelector('h2').innerText,weight:getComputedStyle(g.querySelector('h2')).fontWeight,font:getComputedStyle(g.querySelector('h2')).fontSize}})),summary:[...summary.children].map(x=>({class:x.className,rect:rect(x),text:x.innerText})),identity:{text:identity.innerText,font:getComputedStyle(identity).fontSize,weight:getComputedStyle(identity).fontWeight,lines:lineCount(identity),rect:rect(identity)},copyright:{font:getComputedStyle(copy).fontSize,weight:getComputedStyle(copy).fontWeight,rect:rect(copy)},icons:e.querySelectorAll('.footer-contact-links svg,.footer-contact-links .ui-icon').length};
}"""
normalize=lambda s:' '.join(s.split())
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome',args=['--mute-audio'])
 for width in [320,390,800,961,1100,1440]:
  for theme in ['light','dark']:
   for scale in [1,2]:
    context=browser.new_context(viewport={'width':width,'height':1000},color_scheme=theme,reduced_motion='reduce')
    context.route('**/*',lambda route:route.continue_()if urlsplit(route.request.url).netloc==host else route.abort())
    context.add_init_script('if(window.top===window){localStorage.setItem("soyuz_theme",'+json.dumps(theme)+');localStorage.setItem("soyuz_feedback_enabled","false")}')
    page=context.new_page();page.on('pageerror',lambda error:report['pageErrors'].append(str(error)))
    row={'width':width,'theme':theme,'textScale':scale}
    try:
     page.goto(args.origin,wait_until='domcontentloaded');page.evaluate('document.fonts.ready');page.wait_for_timeout(250)
     footer=page.locator('.footer')
     if scale==2:
      footer.evaluate("""e=>{const all=[...e.querySelectorAll('*')].filter(x=>[...x.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const sizes=all.map(x=>parseFloat(getComputedStyle(x).fontSize));all.forEach((x,i)=>x.style.fontSize=sizes[i]*2+'px')}""")
     footer.scroll_into_view_if_needed();page.wait_for_timeout(100)
     data=footer.evaluate(SAMPLE);row['layout']=data
     assert not data['overflow']and not data['cardOverflow']and not data['pageOverflow'],data
     assert [g['heading']['text']for g in data['groups']]==['Навигация','Связаться','Документы'],data
     assert all(g['heading']['weight']=='400'for g in data['groups']),data
     if width in [320,390]and scale==1:
      groups=data['groups']
      assert abs(groups[0]['rect']['y']-groups[1]['rect']['y'])<1,groups
      assert groups[2]['rect']['y']>=max(groups[0]['rect']['bottom'],groups[1]['rect']['bottom']),groups
      if width==320:assert data['card']['height']<900,data['card']
     actual_nav=footer.locator('.footer-groups>a')
     assert [normalize(s)for s in actual_nav.all_inner_texts()]==nav
     nav_rects=actual_nav.evaluate_all('es=>es.map(e=>e.getBoundingClientRect().toJSON())')
     assert max(r['x']for r in nav_rects)-min(r['x']for r in nav_rects)<1 and all(nav_rects[i]['bottom']<=nav_rects[i+1]['y']+1 for i in range(4)),nav_rects
     assert [urlsplit(h).fragment for h in actual_nav.evaluate_all('es=>es.map(e=>e.href)')]==nav_ids
     contacts=footer.locator('.footer-contact-links>a')
     assert [normalize(s)for s in contacts.all_inner_texts()]==[site['phone'],'Онлайн-запись','Telegram','MAX','ВКонтакте']
     assert contacts.evaluate_all('es=>es.map(e=>e.getAttribute("href"))')==['tel:'+site['phoneLink'],site['bookingUrl'],site['telegram'],site['maxUrl'],site['vkMessageUrl']]
     assert contacts.nth(1).get_attribute('data-booking')is not None and contacts.nth(1).get_attribute('aria-controls')=='booking-drawer'
     assert data['icons']==0
     assert [normalize(s)for s in footer.locator('.footer-legal>a').all_inner_texts()]==[v['title']for v in legal]
     assert [g['class']for g in data['summary']]==['footer-logo','footer-description','footer-address','footer-hours']
     assert footer.locator('.footer-booking').count()==0
     assert abs(data['summary'][1]['rect']['y']-data['summary'][0]['rect']['bottom']-16)<1,data['summary']
     assert normalize(data['summary'][2]['text'])==site['city']+', '+site['address']
     assert site['hours']in data['summary'][3]['text']
     assert all(data['summary'][i]['rect']['bottom']<=data['summary'][i+1]['rect']['y']+1 for i in range(3)),data['summary']
     assert data['identity']['font']==data['copyright']['font']==str(12*scale)+'px'
     assert data['identity']['weight']==data['copyright']['weight']=='400'
     assert normalize(data['identity']['text'])==operator['legalName']+' · ИНН '+operator['inn']+' · ОГРНИП '+operator['ogrnip']
     if width>960 and scale==1:
      assert data['identity']['lines']==1,data['identity']
      assert max(g['rect']['y']for g in data['groups'])-min(g['rect']['y']for g in data['groups'])<1,data['groups']
     for c in data['controls']:
      assert not c['clipped']and not c['ellipsis'],c
      assert c['rect']['x']>=data['card']['x']-1 and c['rect']['right']<=data['card']['right']+1,c
      if c['button']:
       assert c['rect']['height']>=44 and min(c['padding'])>=12 and c['lines']==1,c
      else:
       assert c['rect']['height']>= (44 if width<=960 else 32) and c['weight']=='600',c
       if c['booking']:assert c['lines']==1,c
     # Follow the actual DOM tab order, including both shared actions.
     controls=footer.locator('.footer-logo,.footer-hours button,.footer-links>a')
     assert controls.count()==15
     controls.nth(0).focus();focused=[]
     for i in range(15):
      if i:page.keyboard.press('Tab')
      assert controls.nth(i).evaluate('e=>e===document.activeElement'),(i,page.evaluate('document.activeElement.outerHTML'))
      focused.append(controls.nth(i).get_attribute('aria-label')or controls.nth(i).inner_text())
     row['keyboardOrder']=focused
     hours=footer.locator('.footer-hours button');hours.focus();page.keyboard.press('Enter')
     assert hours.get_attribute('aria-expanded')=='true'
     tip=page.locator('#'+hours.get_attribute('aria-describedby'))
     assert tip.is_visible()
     tip_bounds=tip.bounding_box();assert tip_bounds['x']>=0 and tip_bounds['x']+tip_bounds['width']<=width+1,tip_bounds
     page.keyboard.press('Escape');assert hours.get_attribute('aria-expanded')=='false'and hours.evaluate('e=>e===document.activeElement')
     row['hoursKeyboard']=True
     if scale==1 and width in [390,1440]:
      destinations=[]
      for i in range(5):
       actual_nav.nth(i).focus();page.keyboard.press('Enter');page.wait_for_timeout(100)
       assert page.evaluate('location.hash')=='#'+nav_ids[i]
       assert page.locator('#'+nav_ids[i]).is_visible();destinations.append(nav_ids[i])
      row['keyboardActivatedNavigation']=destinations
      booking=footer.locator('.footer-contact-links [data-booking]');booking.focus();page.keyboard.press('Enter')
      drawer=page.locator('[data-booking-drawer]');drawer.wait_for(state='visible')
      frame=page.locator('[data-booking-frame]');row['bookingFrame']=frame.get_attribute('src')
      assert row['bookingFrame']and'yclients' in row['bookingFrame']
      page.keyboard.press('Escape');drawer.wait_for(state='hidden');assert booking.evaluate('e=>e===document.activeElement')
     page.evaluate('document.activeElement?.blur()');page.mouse.move(width-2,1);page.wait_for_timeout(80)
     footer.screenshot(path=str(OUT/f'{width}-{theme}-{scale}x.png'))
     row['pass']=True
    except Exception:
     row['pass']=False;row['failure']=traceback.format_exc();page.screenshot(path=str(OUT/f'failure-{width}-{theme}-{scale}x.png'))
    finally:
     report['cases'].append(row);context.close()
 browser.close()
report['sourceEnd']=source_hashes();report['unchanged']=report['sourceStart']==report['sourceEnd']
report['passed']=sum(r['pass']for r in report['cases']);report['failed']=24-report['passed']
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'failed':report['failed'],'pageErrors':report['pageErrors'],'unchanged':report['unchanged'],'results':str(OUT/'results.json')},ensure_ascii=False))
assert report['failed']==0 and report['pageErrors']==[] and report['unchanged']
