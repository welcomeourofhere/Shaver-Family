"""Intrinsic SSR caption geometry over every unique reviewed label, including text200."""
import argparse,hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--origin',required=True);parser.add_argument('--label',required=True);args=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/works-titles'/args.label;OUT.mkdir(parents=True,exist_ok=True)
SOURCE=['src/content/works.ts','src/components/Works.astro','src/styles/works.css','content/work-photo-titles.json','content/work-photos.json','content/work-photos-owner.json']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in SOURCE}
before=hashes();cases=[];errors=[]
with sync_playwright()as p:
 b=p.chromium.launch(channel='chrome');c=b.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(200)
 samples=page.locator('[data-work-card]').evaluate_all('''cards=>[...new Map(cards.map(c=>[c.dataset.workCaption,c.dataset.workId])).entries()].map(([title,id])=>({title,id}))''')
 assert page.locator('.works-caption-size-title').count()==len(samples);assert page.locator('.works-caption-size-author').count()==6
 assert page.locator('.works-caption h3').count()==1;assert page.locator('.works-caption-size').evaluate_all('es=>es.every(e=>e.tagName==="SPAN"&&e.getAttribute("aria-hidden")==="true"&&getComputedStyle(e).visibility==="hidden")')
 for width in[1440,961,390,320]:
  page.set_viewport_size({'width':width,'height':1000})
  for scale in[1,2]:
   page.locator('.works-caption').evaluate('(e,s)=>{e.style.setProperty("--works-title-size",20*s+"px");e.style.setProperty("--works-author-size",13*s+"px")}',scale);page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(80);geometry=[]
   for item in samples:
    page.locator(f'[data-work-id="{item["id"]}"]').evaluate('e=>e.click()');page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"')
    row=page.locator('#works').evaluate('''e=>{const c=e.querySelector('.works-caption'),h=c.querySelector('h3'),p=c.querySelector('p'),r=c.getBoundingClientRect(),f=e.querySelector('.works-fan').getBoundingClientRect(),controls=e.querySelector('.works-controls').getBoundingClientRect();return{title:h.textContent,height:r.height,controlsFromFan:controls.top-f.top,sectionHeight:e.getBoundingClientRect().height,font:getComputedStyle(h).font,fontReserve:getComputedStyle(c.querySelector('.works-caption-size-title')).font,authorFont:getComputedStyle(p).font,authorReserveFont:getComputedStyle(c.querySelector('.works-caption-size-author')).font,titleHeight:h.getBoundingClientRect().height,authorGap:p.getBoundingClientRect().top-h.getBoundingClientRect().bottom,overflow:document.documentElement.scrollWidth>innerWidth+1}}''')
    assert row['title']==item['title']and row['font']==row['fontReserve']and row['authorFont']==row['authorReserveFont']and abs(row['authorGap']-4)<.1 and not row['overflow'],row;geometry.append(row)
   assert max(r['height']for r in geometry)-min(r['height']for r in geometry)<.5,geometry
   assert max(r['controlsFromFan']for r in geometry)-min(r['controlsFromFan']for r in geometry)<.5,geometry
   if width in[1440,390,320]:page.mouse.click(2,100);page.locator('#works').screenshot(path=str(OUT/f'{width}-text{scale*100}.png'))
   cases.append({'case':'stable intrinsic caption and controls over every unique reviewed label','width':width,'text':scale*100,'geometry':geometry})
 c.close();b.close()
assert not errors,errors
assert hashes()==before,'Display-title source changed during verification'
(OUT/'verification.json').write_text(json.dumps({'cases':cases,'pageerrors':errors,'sourceHashes':before,'origin':args.origin},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(cases),'intrinsic title groups;',len(samples),'unique titles; errors0; source unchanged')
