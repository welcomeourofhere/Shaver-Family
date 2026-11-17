"""Frozen service disclosure, detailed promo and contacts-dock acceptance; no provider action."""
import argparse,hashlib,json,re,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
FILES=['src/scripts/service-deck.ts','src/scripts/service-disclosure.ts','src/styles/service-deck.css','src/components/MobileNav.astro','src/scripts/dock-actions.ts','src/scripts/dock-surface.ts','src/styles/mobile-nav.css']
def hashes():return{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in FILES}
p=argparse.ArgumentParser();p.add_argument('--origin',required=True);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[\w-]+',a.label)
out=ROOT/'artifacts/iteration67/latest-corrections'/a.label;out.mkdir(parents=True,exist_ok=False)
report={'origin':a.origin,'sourceStart':hashes(),'cases':[],'errors':[],'physicalDevice':False,'providerNavigation':False}
with sync_playwright()as pw:
 browser=pw.chromium.launch(channel='chrome',args=['--mute-audio'])
 try:
  for width in [320,390,800,1440]:
   for motion in ['no-preference','reduce']:
    c=browser.new_context(viewport={'width':width,'height':1000},reduced_motion=motion)
    c.add_init_script("if(top===window&&location.origin!=='null')localStorage.setItem('soyuz.analytics.v1','denied')")
    c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==urlsplit(a.origin).netloc else r.abort())
    page=c.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));row={'width':width,'motion':motion,'pass':False}
    try:
     response=page.goto(a.origin,wait_until='domcontentloaded');assert b'/@vite/client'not in response.body()
     page.evaluate('document.fonts.ready');page.wait_for_timeout(350)
     page.locator('#services').scroll_into_view_if_needed();panel=page.locator('.sd-card[aria-hidden=false]');rows=panel.locator('.sd-service');target=rows.nth(1)
     page.evaluate("""()=>{window.disclosureFrames=[];document.querySelector('.sd-card[aria-hidden=false]').addEventListener('toggle',function record(e){if(!e.target.open)return;this.removeEventListener('toggle',record,true);const r=e.target;let count=0;requestAnimationFrame(function frame(){disclosureFrames.push({height:r.getBoundingClientRect().height,summary:r.querySelector('summary').getBoundingClientRect().height,animated:r.hasAttribute('data-service-opening'),openCount:r.parentElement.querySelectorAll('details[open]').length});if(++count<24)requestAnimationFrame(frame)})},{capture:true})}""")
     target.locator('summary').click();page.wait_for_timeout(420);frames=page.evaluate('disclosureFrames');assert frames and all(f['openCount']==1 for f in frames),frames
     assert target.evaluate('e=>e.open')and panel.locator('details[open]').count()==1
     if motion=='no-preference':assert len({round(f['height'],1)for f in frames if f['animated']})>=3,frames
     else:assert not any(f['animated']for f in frames),frames
     for index in [2,1,0]:rows.nth(index).locator('summary').click();page.wait_for_timeout(25)
     page.wait_for_timeout(300);assert rows.nth(0).evaluate('e=>e.open')and panel.locator('[data-service-opening]').count()==0
     assert panel.locator('.sd-service').evaluate_all('es=>es.every(e=>!e.style.height)')
     row['frames']=frames
     panel_id=panel.get_attribute('id');rows.nth(2).locator('summary').click();page.wait_for_timeout(240)
     page.locator('[data-sd-tab]').nth(1).click();page.wait_for_timeout(30)
     page.evaluate("""id=>{window.returnLayout=null;const r=document.getElementById(id).querySelector('.sd-service');r.addEventListener('toggle',()=>{if(!r.open)return;const a=r.getAnimations().find(a=>'height'in a.effect.getKeyframes()[0]);window.returnLayout=a?{from:a.effect.getKeyframes()[0].height,to:a.effect.getKeyframes().at(-1).height}:null},{once:true})}""",panel_id)
     page.locator('[data-sd-tab]').nth(0).click();page.wait_for_timeout(380)
     returned=page.evaluate("id=>({motion:window.returnLayout,height:parseFloat(getComputedStyle(document.getElementById(id).querySelector('.sd-service')).height)})",panel_id)
     if motion=='no-preference':assert returned['motion'] and abs(float(returned['motion']['to'].replace('px',''))-returned['height'])<=1,returned
     else:assert returned['motion'] is None,returned
     row['categoryReturn']=returned
     if width<=960:
      page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_timeout(350);page.locator('[data-dock-slot][data-action=promo]').click();dialog=page.locator('#promo-dialog');dialog.wait_for(state='visible')
      text=re.sub(r'\s+',' ',dialog.inner_text());assert all(part in text for part in ['30%','СССР','комментарии','администратору','один раз','не суммируются']),text
      if width==320:dialog.evaluate("e=>{for(const n of e.querySelectorAll('h2,p,.promo-code,[data-booking]>span'))n.style.fontSize=parseFloat(getComputedStyle(n).fontSize)*2+'px'}")
      assert not dialog.evaluate('e=>e.scrollWidth>e.clientWidth+1')
      cta=dialog.locator('[data-booking]');cta.scroll_into_view_if_needed();close=dialog.locator('[data-dismiss]').bounding_box();assert close['width']>=44 and close['height']>=44,close
      size=cta.evaluate("e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{w:r.width,h:r.height,p:Math.min(parseFloat(s.paddingLeft),parseFloat(s.paddingRight)),overflow:e.scrollWidth>e.clientWidth+1}}")
      assert size['h']>=44 and size['p']>=12 and not size['overflow'],size
      page.screenshot(path=str(out/f'promo-{width}-{motion}.png'));page.keyboard.press('Escape');page.wait_for_timeout(300)
      page.locator('#contacts').scroll_into_view_if_needed();page.wait_for_timeout(350);actions=page.locator('[data-dock-slot]:visible').evaluate_all('es=>es.map(e=>e.dataset.action)');assert actions==['map-route','booking'],actions
      row.update(promoText=text,promoCTA=size,contactsActions=actions)
     row['pass']=True
    except Exception:
     row['failure']=traceback.format_exc();page.screenshot(path=str(out/f'failure-{width}-{motion}.png'))
    finally:c.close();report['cases'].append(row)
 finally:browser.close()
report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['pass']=all(r['pass']for r in report['cases'])and not report['errors']and report['sourceUnchanged']
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'pass':report['pass'],'cases':len(report['cases']),'errors':len(report['errors']),'report':str(out/'report.json')},ensure_ascii=False));raise SystemExit(0 if report['pass']else 1)
