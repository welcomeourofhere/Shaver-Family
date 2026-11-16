"""Real desktop text-resize regression for the certificate flow and FAQ columns."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--origin',default='http://127.0.0.1:4321');parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--legacy',action='store_true');args=parser.parse_args()
OUT=ROOT/'tmp/planning/iteration65/visual-audit-desktop/fit';OUT.mkdir(parents=True,exist_ok=True)
legacy='@media(min-width:961px){.certificates{contain:size}.certificate-scene{flex:1 1 var(--certificate-scene-height);min-height:0}.faq-layout{grid-template-columns:var(--split-columns)}}'
rows=[];errors=[]
with sync_playwright()as p:
 browser=getattr(p,args.engine).launch(**({'channel':'chrome'}if args.engine=='chromium'else{}))
 for width,height in [(961,600),(1024,720),(1280,720),(1440,900),(1920,1080)]:
  for theme in ['light','dark']:
   context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,reduced_motion='reduce');context.add_init_script("localStorage.setItem('soyuz_theme',%s)"%json.dumps(theme))
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.origin,wait_until='domcontentloaded');page.wait_for_function("getComputedStyle(document.querySelector('.certificates')).contain===(matchMedia('(max-width:960px)').matches?'none':'inline-size')");page.evaluate('document.fonts.ready');page.wait_for_timeout(200)
   compact=page.evaluate("matchMedia('(max-width:960px)').matches")
   def sizes():return page.evaluate("""()=>Object.fromEntries(['.gifts-layout','.certificates','.certificate-scene','.faq-title','.faq-list'].map(sel=>{const e=document.querySelector(sel),r=e.getBoundingClientRect();return[sel,{width:r.width,height:r.height,left:r.left}]}))""")
   previous=page.add_style_tag(content=legacy);normal_before=sizes();previous.evaluate('(e)=>e.remove()');normal_after=sizes()
   for selector in normal_before:
    for field in ['width','height','left']:assert abs(normal_before[selector][field]-normal_after[selector][field])<=1,(width,theme,selector,field,normal_before,normal_after)
   if args.legacy:page.add_style_tag(content=legacy)
   for text_scale in [1,2]:
    if text_scale==2:page.evaluate("""()=>{const es=[...document.querySelectorAll('body *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));const sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')}""")
    page.locator('#certificates').evaluate('e=>scrollTo({top:e.getBoundingClientRect().bottom+scrollY-innerHeight+160,behavior:"instant"})');page.wait_for_timeout(180)
    result=page.evaluate("""()=>{const cert=document.querySelector('#certificates'),r=cert.getBoundingClientRect(),buy=cert.querySelector('.certificate-buy'),br=buy.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(buy);const text=range.getBoundingClientRect(),s=getComputedStyle(buy);return{card:r.toJSON(),textBottom:Math.max(...[...cert.querySelectorAll('.certificate-copy,.certificate-description,.certificate-buy')].map(e=>e.getBoundingClientRect().bottom)),button:br.toJSON(),buttonText:text.toJSON(),paddingLeft:parseFloat(s.paddingLeft),paddingRight:parseFloat(s.paddingRight),textRects:range.getClientRects().length,sceneHeight:cert.querySelector('.certificate-scene').getBoundingClientRect().height,scrollWidth:cert.scrollWidth,clientWidth:cert.clientWidth,nextHeadingTop:document.querySelector('#reviews .section-title').getBoundingClientRect().top}}""")
    page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-{theme}-{text_scale}x-certificate.png'))
    assert result['textBottom']<=result['card']['bottom']-20,(width,theme,text_scale,'certificate text escaped its background',result)
    assert result['nextHeadingTop']>=result['textBottom']+32,(width,theme,text_scale,'certificate overlaps reviews',result)
    assert result['sceneHeight']>=95 and result['scrollWidth']<=result['clientWidth']+1,(width,theme,text_scale,result)
    assert result['textRects']==1 and result['buttonText']['width']<=result['button']['width']-result['paddingLeft']-result['paddingRight']+1,(width,theme,text_scale,'certificate button label clipped',result)
    page.locator('#faq').evaluate('e=>scrollTo({top:e.getBoundingClientRect().top+scrollY-96,behavior:"instant"})');page.wait_for_timeout(120)
    faq=page.evaluate("""()=>{const title=document.querySelector('#faq-title'),list=document.querySelector('.faq-list'),r=list.getBoundingClientRect();const lines=[...title.querySelectorAll('.headline-desktop>span')].filter(e=>e.getClientRects().length).map(e=>{const range=document.createRange();range.selectNodeContents(e);return range.getBoundingClientRect().toJSON()});return{list:r.toJSON(),title:title.getBoundingClientRect().toJSON(),maxTextRight:Math.max(...lines.map(r=>r.right)),overflow:[...list.querySelectorAll('.faq-item:not([hidden])')].some(e=>e.scrollWidth>e.clientWidth+1)}}""")
    page.screenshot(path=str(OUT/f'{args.engine}-{width}x{height}-{theme}-{text_scale}x-faq.png'))
    if compact:assert faq['title']['bottom']+12<=faq['list']['top'],(width,theme,text_scale,'compact FAQ heading overlaps questions',faq)
    else:assert faq['maxTextRight']+12<=faq['list']['left'],(width,theme,text_scale,'FAQ heading overlaps questions',faq)
    assert not faq['overflow'],(width,theme,text_scale,'FAQ question clipped',faq)
    page.locator('.faq-item:not([hidden]) summary').first.click();page.wait_for_timeout(100)
    assert page.locator('.faq-item[open]').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'),(width,theme,text_scale,'FAQ answer clipped')
    page.locator('.faq-item[open] summary').click()
    rows.append({'width':width,'height':height,'theme':theme,'textScale':text_scale,'compactMedia':compact,'certificate':result,'faq':faq,'normalGeometryPreserved':True})
   context.close()
 browser.close()
assert not errors,errors
(OUT/f'{args.engine}.json').write_text(json.dumps({'engine':args.engine,'legacy':args.legacy,'rows':rows,'pageErrors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',args.engine,len(rows),'certificate/FAQ normal and 200% text states, both themes, original geometry within1px')
