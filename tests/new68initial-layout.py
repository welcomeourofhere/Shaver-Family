"""Pre/post module geometry; compiled files at a public-host fixture with an explicit evaluation gate."""
import argparse,hashlib,json,re,traceback
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--fixture',required=True,type=Path);p.add_argument('--label',required=True);p.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');p.add_argument('--single',action='store_true');a=p.parse_args();assert re.fullmatch(r'[\w-]+',a.label)
fixture=a.fixture.resolve();assert fixture.is_relative_to((ROOT/'tmp').resolve())and(fixture/'index.html').is_file()
OUT=ROOT/'artifacts/iteration68'/a.label;OUT.mkdir(parents=True,exist_ok=False)
files=['src/layouts/SiteFrame.astro','src/styles/hero.css','src/scripts/dock-surface.ts','src/components/MobileNav.astro'];hashes=lambda:{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in files}
POSE="""()=>{const hero=document.querySelector('.hero-heading-mobile'),copy=document.querySelector('.hero-mobile-copy'),nav=document.querySelector('[data-mobile-nav]'),notice=document.querySelector('[data-analytics-prompt]');return{hero:hero.getBoundingClientRect().toJSON(),copy:copy.getBoundingClientRect().toJSON(),nav:nav.getBoundingClientRect().toJSON(),noticeVisible:!notice.hidden&&getComputedStyle(notice).display!=='none',padding:getComputedStyle(document.querySelector('.hero-lead')).paddingBottom,liveHeight:document.documentElement.style.getPropertyValue('--dock-live-height'),fontStatus:document.fonts.status}}"""
report={'fixture':str(fixture),'engine':a.engine,'sourceStart':hashes(),'cases':[],'deliveryFixture':True,'moduleGate':'Delay HTML module entries with dynamic import; compiled module graph is unchanged','performanceClaim':False}
with sync_playwright()as pw:
 b=getattr(pw,a.engine).launch(**({'channel':'chrome','args':['--mute-audio']}if a.engine=='chromium'else{}))
 try:
  cases=[(390,'light',False)]if a.single else[(w,t,denied)for w in [320,390,600]for t in ['light','dark']for denied in [False,True]]
  for width,theme,denied in cases:
   c=b.new_context(viewport={'width':width,'height':844},is_mobile=a.engine!='firefox',has_touch=True,color_scheme=theme,reduced_motion='no-preference');page=c.new_page();page.set_default_timeout(12000);gated=[];errors=[]
   c.add_init_script('window.__initialModuleGate=new Promise(resolve=>{window.__releaseInitialModules=resolve})')
   c.add_init_script("localStorage.setItem('soyuz_theme',"+json.dumps(theme)+");"+("localStorage.setItem('soyuz.analytics.v1','denied');"if denied else''))
   def route(r):
    u=urlsplit(r.request.url)
    if u.hostname!='soyuz.hair':r.abort();return
    path=(fixture/(unquote(u.path).lstrip('/')or'index.html')).resolve()
    if not path.is_relative_to(fixture)or not path.is_file():r.abort();return
    mime={'.js':'application/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.ttf':'font/ttf','.webp':'image/webp','.html':'text/html','.mp4':'video/mp4','.wav':'audio/wav'}.get(path.suffix,'application/octet-stream')
    body=path.read_bytes()
    if path.suffix=='.html':
     def gate(m):
      if not re.search(r'type=[\"\x27]module[\"\x27]',m[1]):return m[0]
      src=re.search(r'\bsrc=[\"\x27]([^\"\x27]+)[\"\x27]',m[1]);assert src,'Expected external compiled entry'
      gated.append(src[1]);return '<script type="module">await globalThis.__initialModuleGate;await import('+json.dumps(src[1])+');</script>'
     body=re.sub(r'<script\b([^>]*)>(.*?)</script>',gate,body.decode('utf-8'),flags=re.S).encode('utf-8')
    r.fulfill(status=200,body=body,content_type=mime)
   c.route('**/*',route);page.on('pageerror',lambda e:errors.append(str(e)));row={'width':width,'theme':theme,'denied':denied,'pass':False,'errors':errors}
   try:
    print('stage navigation',a.engine,width,theme,denied,flush=True)
    page.goto('https://soyuz.hair/',wait_until='commit',timeout=15000);row['stage']='markup';print('stage markup',flush=True)
    page.locator('.footer').wait_for(state='visible');row['stage']='fonts';print('stage fonts',flush=True)
    page.wait_for_function("document.fonts.status==='loaded'",timeout=12000);row['stage']='bootstrap';print('stage bootstrap',flush=True)
    page.wait_for_function('document.documentElement.dataset.cookiePrompt!==undefined');page.wait_for_timeout(120)
    before=page.evaluate(POSE);assert before['noticeVisible']is(not denied);assert gated,'No modules gated';row['before']=before;row['gatedModules']=len(set(gated))
    page.evaluate('window.__releaseInitialModules()')
    page.wait_for_function("document.querySelector('.dock-toolbar').style.gridTemplateColumns!==''");page.wait_for_timeout(300);after=page.evaluate(POSE);row['after']=after
    row['heroYDelta']=after['hero']['y']-before['hero']['y'];row['copyYDelta']=after['copy']['y']-before['copy']['y'];assert abs(row['heroYDelta'])<=1 and abs(row['copyYDelta'])<=1,row
    assert after['noticeVisible']is(not denied)
    if not denied:
     page.evaluate("document.addEventListener('click',()=>{window.initialCloseHadFocus=document.querySelector('[data-analytics-prompt]').contains(document.activeElement)},{capture:true,once:true})")
     page.locator('[data-analytics-prompt] [data-analytics-choice="denied"]').click();page.wait_for_function("document.documentElement.dataset.cookiePrompt==='false'");page.wait_for_timeout(300);closed=page.evaluate(POSE);row['closed']=closed;assert abs(closed['hero']['y']-after['hero']['y'])<=1
     row['closeHadFocus']=page.evaluate('initialCloseHadFocus')
     assert page.evaluate("initialCloseHadFocus?document.querySelector('[data-open-menu]')===document.activeElement:document.activeElement.isConnected&&!document.querySelector('[data-analytics-prompt]').contains(document.activeElement)")
    assert not errors;row['pass']=True
   except Exception:row['failure']=traceback.format_exc()
   finally:
    try:page.screenshot(path=str(OUT/(str(width)+'-'+theme+'-'+str(denied)+'.png')),timeout=5000)
    except Exception as e:row['screenshotFailure']=str(e)
    c.close();report['cases'].append(row)
    (OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
   print(json.dumps({k:row.get(k)for k in ['width','theme','denied','pass','heroYDelta','copyYDelta']},ensure_ascii=False),flush=True)
 finally:b.close()
report['sourceEnd']=hashes();report['sourceUnchanged']=report['sourceStart']==report['sourceEnd'];report['browsersClosed']=True;(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');assert report['sourceUnchanged']and all(r['pass']for r in report['cases'])
print('PASS initial geometry; browserclosed END')
