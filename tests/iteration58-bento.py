import os
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
out=Path('artifacts/iteration58');rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome')
 page=b.new_page(viewport={'width':1024,'height':900})
 for w in [960,961,1024,1100,1199,1280]:
  page.set_viewport_size({'width':w,'height':900});page.goto(os.environ.get('QA_URL','http://127.0.0.1:4321/'));page.wait_for_timeout(600)
  row=page.locator('#reviews-rail').evaluate("e=>({width:innerWidth,railWidth:e.clientWidth,layout:e.dataset.reviewLayout,height:e.offsetHeight,tiles:[...e.querySelectorAll('[data-review-card]')].map(c=>({shape:c.dataset.reviewShape,x:c.offsetLeft,y:c.offsetTop,w:c.offsetWidth,h:c.offsetHeight}))})")
  assert row['layout']==('phone' if w<=960 else '3' if row['railWidth']<1100 else '4'),row
  if w==1024:
   page.locator('#reviews').evaluate("e=>e.scrollIntoView({behavior:'instant'})")
   page.locator('#reviews img').evaluate_all("es=>es.forEach(e=>e.loading='eager')")
   page.wait_for_function("()=>[...document.querySelectorAll('#reviews img')].every(e=>e.complete)")
   page.wait_for_timeout(1200);page.locator('#reviews').screenshot(path=str(out/'reviews-tablet.png'))
  rows.append(row)
 b.close()
(out/'bento-verification.json').write_text(json.dumps(rows,indent=2));print([(r['width'],r['layout'],r['height']) for r in rows])
