"""Actual compiled promo layout: 200% text, intrinsic wrapping, native controls; no style fixture."""
import argparse,hashlib,json,re,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--origin',required=True);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[\w-]+',a.label)
out=ROOT/'artifacts/iteration67/promo-layout'/a.label;out.mkdir(parents=True,exist_ok=False)
files=['src/components/MobileNav.astro','src/styles/mobile-nav.css','src/styles/system.css']
hashes=lambda:{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest()for x in files}
report={'sourceStart':hashes(),'origin':a.origin,'cases':[],'pageErrors':[],'styleFixture':False,'fontScale':2,'physicalDevice':False}
with sync_playwright()as pw:
 for engine,kind,channel in [('chrome','chromium','chrome'),('edge','chromium','msedge'),('firefox','firefox',None),('webkit','webkit',None)]:
  browser=getattr(pw,kind).launch(**({'channel':channel,'args':['--mute-audio']}if kind=='chromium'else{}))
  try:
   for width in [320,390,600]:
    for theme in ['light','dark']:
     row={'engine':engine,'browserVersion':browser.version,'width':width,'theme':theme,'pass':False}
     c=browser.new_context(viewport={'width':width,'height':1000},color_scheme=theme,reduced_motion='reduce');c.route('**/*',lambda r:r.continue_()if urlsplit(r.request.url).netloc==urlsplit(a.origin).netloc else r.abort());page=c.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
     try:
      response=page.goto(a.origin,wait_until='domcontentloaded');assert b'/@vite/client'not in response.body();page.evaluate('document.fonts.ready');page.wait_for_timeout(180)
      prompt=page.locator('[data-analytics-prompt]')
      if prompt.is_visible():prompt.locator('.analytics-choice-close').click();prompt.wait_for(state='hidden')
      page.locator('[data-dock-slot][data-action=promo]').click();dialog=page.locator('#promo-dialog');dialog.wait_for(state='visible')
      before=dialog.locator('h2').evaluate('e=>({font:parseFloat(getComputedStyle(e).fontSize),height:e.getBoundingClientRect().height})')
      dialog.evaluate("e=>{for(const n of e.querySelectorAll('h2,p,.promo-code,[data-booking]>span'))n.style.fontSize=parseFloat(getComputedStyle(n).fontSize)*2+'px'}")
      layout=dialog.evaluate(r"""e=>{const t=e.querySelector('h2'),x=e.querySelector('[data-dismiss]'),walker=document.createTreeWalker(t,NodeFilter.SHOW_TEXT),words=[];let n;while(n=walker.nextNode())for(const m of n.textContent.matchAll(/[А-ЯЁа-яё0-9%]+/g)){const r=document.createRange();r.setStart(n,m.index);r.setEnd(n,m.index+m[0].length);words.push({word:m[0],lines:[...r.getClientRects()].filter(r=>r.width>0).length})}return{heading:t.getBoundingClientRect().toJSON(),close:x.getBoundingClientRect().toJSON(),words,font:parseFloat(getComputedStyle(t).fontSize),overflow:e.scrollWidth>e.clientWidth+1}}""")
      assert layout['font']==before['font']*2 and not layout['overflow'],layout
      assert next(w['lines']for w in layout['words']if w['word'].lower()=='первый')==1,layout
      assert layout['close']['width']>=44 and layout['close']['height']>=44 and layout['close']['top']<=layout['heading']['top']+1,layout
      cta=dialog.locator('[data-booking]');cta.scroll_into_view_if_needed();control=cta.evaluate("e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),t=e.querySelector('.mobile-action-short'),q=document.createRange();q.selectNodeContents(t);return{height:r.height,padding:Math.min(parseFloat(s.paddingLeft),parseFloat(s.paddingRight)),lines:q.getClientRects().length,overflow:e.scrollWidth>e.clientWidth+1,hit:document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)?.closest('[data-booking]')===e}}")
      assert control['height']>=44 and control['padding']>=12 and control['lines']==1 and not control['overflow']and control['hit'],control
      page.screenshot(path=str(out/f'{engine}-{width}-{theme}.png'));row.update(before=before,layout=layout,cta=control,**{'pass':True})
     except Exception:row['failure']=traceback.format_exc();page.screenshot(path=str(out/f'{engine}-{width}-{theme}-failure.png'))
     finally:c.close();report['cases'].append(row)
  finally:browser.close()
report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['pass']=all(r['pass']for r in report['cases'])and not report['pageErrors']and report['sourceUnchanged']
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'pass':report['pass'],'cases':len(report['cases']),'pageErrors':len(report['pageErrors']),'report':str(out/'report.json')},ensure_ascii=False));raise SystemExit(0 if report['pass']else 1)
