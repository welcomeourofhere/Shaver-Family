"""Render SOYUZ social artwork and approved complete-logo icons with the browser."""
import base64,hashlib,json,re
from html import escape
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
OUTPUT=ROOT/'artifacts/iteration66/seo'
FAVICON_SOURCE=Path('J:/Brandbooks/brand book СОЮЗ Барбершоп 2025/01_Логотип/Растровые файлы/Логотип красный (круг).png')
FAVICON_SVG_SOURCE=Path('J:/Brandbooks/brand book СОЮЗ Барбершоп 2025/01_Логотип/Векторные файлы/Варианты логотипов/Логотип красный (круг).svg')
sha=lambda data:hashlib.sha256(data).hexdigest()

def data_url(path,mime):
 return 'data:'+mime+';base64,'+base64.b64encode((PUBLIC/path).read_bytes()).decode()

def artwork():
 site=json.loads((ROOT/'content/site.json').read_text(encoding='utf8'))
 design=json.loads((ROOT/'src/config/design.json').read_text(encoding='utf8'))
 domain=urlsplit(json.loads((ROOT/'deploy/production.json').read_text(encoding='utf8'))['origin']).netloc
 logo=data_url('brand/logo-paper.svg','image/svg+xml')
 photo=data_url('media/hero/soyuz-intro-poster.webp','image/webp')
 molot=data_url('fonts/Molot-UI.ttf','font/ttf')
 manrope=data_url('fonts/Manrope-Medium-UI.woff2','font/woff2')
 return ('''<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@font-face{font-family:Molot;src:url("'''+molot+'''") format("truetype");font-weight:400}
@font-face{font-family:Manrope;src:url("'''+manrope+'''") format("woff2");font-weight:500}
*{box-sizing:border-box}html,body{margin:0;width:1200px;height:630px;background:__RED__}
main{display:grid;grid-template-columns:__GOLDEN__fr 1fr;width:1200px;height:630px;overflow:hidden}
.copy{display:flex;flex-direction:column;align-items:flex-start;padding:52px 56px;color:__PAPER__}
.brand{width:304px;height:148px;object-fit:contain;object-position:left center}
h1{margin:32px 0 20px;font:400 64px/1.08 Molot;text-transform:uppercase}h1 span{display:block;white-space:nowrap}
.services{margin:0;font:500 24px/1.5 Manrope}
.address{margin:auto 0 0;font:500 24px/1.5 Manrope}.address span{display:block}
.photo{display:block;width:100%;height:630px;object-fit:cover;object-position:55% center}
</style></head><body><main><section class="copy"><img class="brand" alt="СОЮЗ Барбершоп" src="'''+logo+'''">
<h1><span>Стригут и бреют</span><span>прекрасные дамы</span></h1>
<p class="services">Мужские стрижки · борода · СПА</p>
<p class="address"><span>'''+escape(site['city']+', '+site['address'])+'''</span><span>'''+escape(domain)+'''</span></p></section>
<img class="photo" alt="Интерьер барбершопа СОЮЗ" src="'''+photo+'''"></main></body></html>''').replace('__RED__',design['base']['--red']).replace('__PAPER__',design['base']['--paper']).replace('__GOLDEN__',str(design['scale']['goldenRatio']))

def main():
 OUTPUT.mkdir(parents=True,exist_ok=True);(PUBLIC/'media/og').mkdir(parents=True,exist_ok=True)
 original=FAVICON_SOURCE.read_bytes()
 assert sha(original)=='fc706affe04c6c2a9c5ce15604245b6a589e9981dfaac9c4a3d2ecebf5d9e05e','Approved ready-made circle must remain unchanged'
 original_svg=FAVICON_SVG_SOURCE.read_bytes()
 assert sha(original_svg)=='2072188966a68d37eb0caeb6fed3e32595853fce10aa3020616747e26710c2be'
 clean_svg,removed=re.subn(rb'<image\b[^>]*?/>',b'',original_svg,flags=re.S)
 assert removed==1 and b'<image'not in clean_svg
 svg=PUBLIC/'brand/favicon-standard.svg';svg.write_bytes(clean_svg)
 favicon='data:image/png;base64,'+base64.b64encode(original).decode()
 html=artwork();assert not any(token in html for token in ['__RED__','__PAPER__','__GOLDEN__']);(OUTPUT/'social-preview-source.html').write_text(html,encoding='utf8',newline='')
 captures=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome')
  page=browser.new_page(viewport={'width':1200,'height':630},device_scale_factor=1)
  page.set_content(html);page.evaluate('document.fonts.ready')
  page.wait_for_function('[...document.images].every(image=>image.complete&&image.naturalWidth>0)')
  geometry=page.evaluate('''()=>({canvas:{width:innerWidth,height:innerHeight,background:getComputedStyle(document.body).backgroundColor,columns:[...document.querySelector('main').children].map(e=>e.getBoundingClientRect().width),photoTop:document.querySelector('.photo').getBoundingClientRect().top},text:[...document.querySelectorAll('h1 span,.services,.address span')].map(e=>{const b=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect();return {text:e.textContent,x:b.x,right:b.right,top:b.top,bottom:b.bottom,parentRight:p.right,overflow:e.scrollWidth>e.clientWidth}})})''')
  assert all(not row['overflow'] and row['right']<=1200 and row['bottom']<=630 for row in geometry['text'])
  assert geometry['canvas']['background']=='rgb(196, 47, 42)'and geometry['canvas']['photoTop']==0
  assert abs(geometry['canvas']['columns'][0]/geometry['canvas']['columns'][1]-1.61803398875)<.001
  social=PUBLIC/'media/og/soyuz-home.png';page.screenshot(path=str(social),animations='disabled')
  for size in [48,96,180]:
   page.set_viewport_size({'width':size,'height':size})
   background='#c42f2a'if size==180 else'transparent'
   page.set_content(f'<html><head><style>html,body{{margin:0;width:{size}px;height:{size}px;background:{background}}}img{{display:block;width:{size}px;height:{size}px}}</style></head><body><img src="{favicon}" width="{size}" height="{size}"></body></html>')
   page.wait_for_function('document.images[0].complete&&document.images[0].naturalWidth===1000')
   target=PUBLIC/f'brand/favicon-{size}.png';page.screenshot(path=str(target),omit_background=True,animations='disabled')
   captures.append({'path':target.relative_to(ROOT).as_posix(),'width':size,'height':size,'bytes':target.stat().st_size,'sha256':sha(target.read_bytes())})
  page.set_viewport_size({'width':1000,'height':450})
  icons=''.join(f'<figure><img src="{data_url(f"brand/favicon-{size}.png","image/png")}" width="{size}" height="{size}"><figcaption>{size} × {size}</figcaption></figure>'for size in [48,96,180])
  page.set_content('<html><head><style>body{margin:20px;background:#fffcf7;color:#4b4b4d;font:16px Arial;display:grid;grid-template-columns:600px 300px;gap:30px}figure{margin:0}figcaption{margin-top:10px}.icons{display:flex;gap:20px;align-items:center;margin-top:30px}.icons img{max-width:96px;max-height:96px}</style></head><body><figure><img src="'+data_url('media/og/soyuz-home.png','image/png')+'" width="600" height="315"><figcaption>Превью 1200 × 630</figcaption></figure><section><figure><img src="'+data_url('media/og/soyuz-home.png','image/png')+'" width="300" height="157.5"><figcaption>Миниатюра</figcaption></figure><div class="icons">'+icons+'</div></section></body></html>')
  page.wait_for_function('[...document.images].every(image=>image.complete&&image.naturalWidth>0)')
  page.screenshot(path=str(OUTPUT/'preview-board.png'),animations='disabled')
  page.set_viewport_size({'width':1100,'height':500})
  tiny=''.join(f'<figure><img src="{data_url("brand/favicon-96.png","image/png")}" width="{size}" height="{size}"><figcaption>{size} px</figcaption></figure>'for size in [16,24,32,48])
  page.set_content('<html><head><style>body{margin:32px;background:#fffcf7;color:#4b4b4d;font:16px Arial}h1{font-size:24px;margin:0 0 28px}.sizes{display:flex;align-items:center;gap:32px;margin-bottom:36px}figure{margin:0}figcaption{margin-top:12px}.dark{background:#191a1b;padding:24px;color:#f6e8d3;border-radius:16px}.apple{float:right;margin-right:60px}p{font-size:14px}</style></head><body><figure class="apple"><img src="'+data_url('brand/favicon-180.png','image/png')+'" width="180" height="180"><figcaption>Apple 180 px · тот же готовый круг</figcaption></figure><h1>СОЮЗ · готовый круг из брендбука</h1><div class="sizes">'+tiny+'</div><div class="sizes dark">'+tiny+'</div><p>16 / 24 / 32 / 48 px показаны без увеличения. Поля и буквы исходного кругового файла не менялись.</p></body></html>')
  page.wait_for_function('[...document.images].every(image=>image.complete&&image.naturalWidth>0)')
  page.screenshot(path=str(OUTPUT/'favicon-sizes-board.png'),animations='disabled')
  page.set_viewport_size({'width':850,'height':470})
  page.set_content('<html><head><style>body{margin:24px;background:#fffcf7;color:#4b4b4d;font:16px Arial;display:flex;align-items:center;gap:48px}figure{margin:0}figcaption{margin-top:12px;max-width:320px}.tiny{display:flex;align-items:center;gap:32px}</style></head><body><figure><img src="'+favicon+'" width="320" height="320"><figcaption>Готовый исходник · Логотип красный (круг).png<br>1000×1000 · без изменений композиции</figcaption></figure><div class="tiny">'+''.join(f'<figure><img src="{data_url("brand/favicon-96.png","image/png")}" width="{size}" height="{size}"><figcaption>{size} px</figcaption></figure>'for size in [16,32,48])+'</div></body></html>')
  page.wait_for_function('[...document.images].every(image=>image.complete&&image.naturalWidth>0)')
  page.screenshot(path=str(OUTPUT/'favicon-approved-circle-board.png'),animations='disabled')
  browser_version=browser.version;browser.close()
 inputs=['public/brand/logo-paper.svg','public/brand/favicon-red.svg','public/media/hero/soyuz-intro-poster.webp','public/fonts/Molot-UI.ttf','public/fonts/Manrope-Medium-UI.woff2','content/site.json','content/seo.json','deploy/production.json']
 # UI motion changes do not invalidate artwork. Record only the design inputs it uses.
 design=json.loads((ROOT/'src/config/design.json').read_text(encoding='utf8'))
 design_inputs={'source':'src/config/design.json','red':design['base']['--red'],'paper':design['base']['--paper'],'goldenRatio':design['scale']['goldenRatio']}
 manifest={'version':1,'generator':'scripts/prepare-social-preview.py','generatorSha256':sha(Path(__file__).read_bytes()),'method':'Native Chromium HTML/CSS screenshot; no photo pixels edited','browserVersion':browser_version,'composition':'golden ratio from design.json; original logo and actual interior','sources':[{'path':path,'sha256':sha((ROOT/path).read_bytes())}for path in inputs],'designInputs':design_inputs,'social':{'path':social.relative_to(ROOT).as_posix(),'width':1200,'height':630,'bytes':social.stat().st_size,'sha256':sha(social.read_bytes())},'favicon':{'originalGeometry':'Native square downscaling of the complete standard circle, woman in O and yellow BARBERSHOP preserved; no geometry, margins, positions or source colors changed','source':{'privatePath':FAVICON_SOURCE.as_posix(),'sha256':sha(original),'width':1000,'height':1000,'bytes':len(original)},'sourceColors':{'circle':'#c42f2a','wordmark':'#f6e8d3','signature':'#ffcc29'},'rasters':captures},'textGeometry':geometry}
 manifest['favicon']['svg']={'path':svg.relative_to(ROOT).as_posix(),'bytes':len(clean_svg),'sha256':sha(clean_svg),'sourcePrivatePath':FAVICON_SVG_SOURCE.as_posix(),'sourceSha256':sha(original_svg),'sourceBytes':len(original_svg),'operation':'Removed only the off-canvas Corel preview image under empty clipPath id1; all remaining bytes unchanged','imageCount':0,'scriptCount':0,'textCount':0,'fontDependencies':0}
 (ROOT/'content/seo-assets.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='')
 print(json.dumps({'status':'passed','socialBytes':social.stat().st_size,'icons':len(captures),'originalFaviconUnchanged':next(x['sha256']for x in manifest['sources']if x['path'].endswith('favicon-red.svg'))},ensure_ascii=True))

if __name__=='__main__':main()
