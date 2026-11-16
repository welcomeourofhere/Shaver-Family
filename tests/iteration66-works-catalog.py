"""Bounded merged-catalog verification; the unchanged motion contract has its own proof."""
import argparse, hashlib, json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',required=True);parser.add_argument('--label',required=True);args=parser.parse_args()
OUT=ROOT/'artifacts/iteration66/works-catalog'/args.label;OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['src/content/works.ts','src/components/Works.astro','src/scripts/works.ts','src/styles/works.css','content/work-photos.json','content/work-photos-owner.json','content/work-photo-titles.json']
def hashes():return{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in SOURCES}
before=hashes();wall=json.loads((ROOT/'content/work-photos.json').read_text(encoding='utf8'));owner=json.loads((ROOT/'content/work-photos-owner.json').read_text(encoding='utf8'));labels=json.loads((ROOT/'content/work-photo-titles.json').read_text(encoding='utf8'))
expected={p['id']:{'masterId':p['masterId'],'title':p['title'],'variants':p['variants']}for p in wall['photos']}
for p in owner['photos']:expected[p['id']]={'masterId':p['masterId'],'title':p['title'],'variants':p['variants']}
for p in owner['duplicates']:expected[p['duplicateOf']]['masterId']=p['masterId']
for row in labels['photos']:
 style=next(s for s in labels['catalog']if s['id']==row['primaryId']);expected[row['id']]['title']=f"{style['en']} ({style.get('displayRu',style['ru'])})"
cases=[];errors=[];failed=[]

def check(page):
 state=page.locator('#works').evaluate('''e=>{const c=e.querySelector('[data-work-current=true]'),im=c.querySelector('img'),r=c.getBoundingClientRect(),f=e.querySelector('.works-fan').getBoundingClientRect();return{id:c.dataset.workId,masterId:c.dataset.workMasterId,title:c.dataset.workCaption,label:c.getAttribute('aria-label'),count:e.querySelector('output').textContent,src:im.currentSrc,width:im.naturalWidth,height:im.naturalHeight,complete:im.complete,ratio:c.offsetWidth/c.offsetHeight,overflow:document.documentElement.scrollWidth>innerWidth+1,cut:r.left<f.left-1||r.right>f.right+1||r.top<f.top-1||r.bottom>f.bottom+1,master:e.querySelector('[data-work-author]').textContent,titleShown:e.querySelector('.works-caption h3').textContent,captionHeight:e.querySelector('.works-caption').getBoundingClientRect().height,controlsTop:e.querySelector('.works-controls').getBoundingClientRect().top,sectionHeight:e.getBoundingClientRect().height,dialogs:e.querySelectorAll('dialog').length,links:e.querySelectorAll('a').length}}''')
 item=expected[state['id']];norm=lambda value:' '.join(value.split())
 assert state['masterId']==item['masterId'] and norm(state['title'])==norm(item['title']) and norm(state['titleShown'])==norm(item['title']),state
 assert norm(item['title'])in norm(state['label']) and norm(state['master'])in norm(state['label']),state
 assert state['complete'] and state['width']>0 and state['height']>0 and any(v['url']in state['src']for v in item['variants']),state
 assert abs(state['ratio']-.75)<.006 and not state['overflow'] and not state['cut'] and state['dialogs']==state['links']==0,state
 return state

def settled(page):
 page.wait_for_function('document.querySelector(".works-fan").dataset.workMoving!=="true"');page.wait_for_function('''()=>{const i=document.querySelector('[data-work-current=true] img');return i.complete&&i.naturalWidth>0}''');return check(page)

with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome')
 context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:failed.append({'url':r.url.split('?')[0],'failure':r.failure}))
 page.goto(args.origin,wait_until='domcontentloaded');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(250)
 ids=page.locator('[data-work-card]').evaluate_all('(cards)=>cards.map(c=>c.dataset.workId)');assert len(ids)==len(set(ids))==len(expected) and set(ids)==set(expected),ids
 assert page.locator('#works').get_attribute('data-works-source')=='verified-combined';cases.append({'case':'one canonical SSR collection, exact source union without eight duplicate cards','count':len(ids),'ids':ids})
 order=[]
 for i in range(len(expected)):
  state=settled(page);order.append(state['id']);assert state['count']==f'{i+1} / {len(expected)}',state
  page.locator('[data-work-step="1"]').click()
 assert len(set(order))==len(expected) and settled(page)['id']==order[0];cases.append({'case':'complete randomized catalog cycle, actual decoded responsive media, exact titles/credits and one visit per photo','order':order})
 for master_id in sorted({item['masterId']for item in expected.values()}):
  page.locator(f'[data-work-master-tab="{master_id}"]').click();state=settled(page);count=sum(item['masterId']==master_id for item in expected.values());assert state['count']==f'1 / {count}',state
  assert page.locator('[data-work-card]:not([hidden])').evaluate_all('(cards,id)=>cards.every(c=>c.dataset.workMasterId===id)',master_id)
  page.locator('[data-work-current=true]').focus();page.keyboard.press('End');last=settled(page);assert last['masterId']==master_id and last['count']==f'{count} / {count}',last
  cases.append({'case':'master collection with real decoded first/last photo','masterId':master_id,'count':count,'first':state,'last':last})
 context.close()
 for theme in['light','dark']:
  context=browser.new_context(viewport={'width':390,'height':844},color_scheme=theme,reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(200)
  for width in[1440,1100,961,800,600,390,320]:
   page.set_viewport_size({'width':width,'height':844});page.locator('.works-fan').scroll_into_view_if_needed();page.wait_for_timeout(120);state=settled(page)
   geometry=page.locator('.works-fan').evaluate('''e=>{const f=e.getBoundingClientRect();return[...e.querySelectorAll('[data-work-card]:not([hidden])')].map(c=>{const b=c.getBoundingClientRect();return{id:c.dataset.workId,cut:b.left<f.left-1||b.right>f.right+1||b.top<f.top-1||b.bottom>f.bottom+1,opacity:+getComputedStyle(c).opacity}})}''');assert all(not c['cut']and c['opacity']==1 for c in geometry),geometry
   if width in[1440,390,320]:page.locator('#works').screenshot(path=str(OUT/f'{theme}-{width}.png'))
   cases.append({'case':'merged catalog actual fit','theme':theme,'width':width,'state':state,'visible':geometry})
   if width in[390,320]:
    longest=max(expected,key=lambda id:len(expected[id]['title']));page.locator(f'[data-work-id="{longest}"]').evaluate('e=>e.click()');long_state=settled(page);cases.append({'case':'longest factual caption geometry observation','theme':theme,'width':width,'before':state,'longest':long_state})
  context.close()
 context=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False);page=context.new_page();page.goto(args.origin,wait_until='domcontentloaded');assert page.locator('[data-work-card]').count()==len(expected);assert page.locator('[data-work-current=true]').get_attribute('data-work-id')==wall['photos'][0]['id'];assert page.locator('#works a,#works dialog').count()==0;cases.append({'case':'no-JS fixed first frame and complete catalog SSR without original navigation'});context.close();browser.close()
assert not errors,errors
assert not [r for r in failed if '/media/works/'in r['url']],failed
assert hashes()==before,'Catalog/UI source changed during verification'
(OUT/'verification.json').write_text(json.dumps({'cases':cases,'pageerrors':errors,'requestFailures':failed,'sourceHashes':before,'origin':args.origin},ensure_ascii=False,indent=2),encoding='utf8')
print('PASS',len(cases),'merged catalog groups;',len(expected),'canonical photos; errors0; source unchanged')
