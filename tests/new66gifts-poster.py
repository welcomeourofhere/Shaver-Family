"""Focused local poster/certificate/arrow QA; external providers never execute."""
import argparse
import hashlib
import json
import re
import traceback
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--origin', default='http://127.0.0.1:4321/')
parser.add_argument('--label', required=True)
args = parser.parse_args()
assert re.fullmatch(r'[\w-]+', args.label)
host = urlsplit(args.origin).netloc
assert urlsplit(args.origin).hostname in ['127.0.0.1', 'localhost']
OUT = ROOT / 'tmp/planning/iteration66/gifts-poster' / args.label
OUT.mkdir(parents=True, exist_ok=False)


def source_hashes():
    paths = [*sorted((ROOT / 'src').rglob('*')), ROOT / 'content/construction-poster.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


report = {'origin': args.origin, 'engine': 'Chrome', 'sourceStart': source_hashes(),
          'cases': [], 'pageErrors': [], 'vendorCodeExecuted': False,
          'boundary': 'Local browser QA; no real booking/purchase, physical-device, benchmark or publication claim.'}


def route_local(route):
    if urlsplit(route.request.url).netloc == host:
        route.continue_()
    else:
        route.abort()


STYLE = """e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{background:s.backgroundColor,color:s.color,radius:s.borderRadius,width:r.width,height:r.height,disabled:e.disabled}}"""
GEOMETRY = """async e=>{
 const image=e.querySelector('img'),r=e.getBoundingClientRect(),ir=image.getBoundingClientRect(),s=getComputedStyle(e);
 await image.decode();
 const canvas=document.createElement('canvas');canvas.width=Math.ceil(r.width);canvas.height=Math.ceil(r.height);const ctx=canvas.getContext('2d');
 const scale=Math.max(r.width/image.naturalWidth,r.height/image.naturalHeight),w=image.naturalWidth*scale,h=image.naturalHeight*scale;
 ctx.drawImage(image,(r.width-w)/2,(r.height-h)/2,w,h);
 const chroma=[];
 for(let y=0;y<12;y++)for(let x=0;x<16;x++){
  const px=Math.min(canvas.width-1,Math.round((x+.5)*canvas.width/16)),py=Math.min(canvas.height-1,Math.round((y+.5)*canvas.height/12));
  const rgb=[...ctx.getImageData(px,py,1,1).data].slice(0,3);chroma.push(Math.max(...rgb)-Math.min(...rgb));
 }
 const corners=[[r.left+1,r.top+1],[r.right-1,r.top+1],[r.left+1,r.bottom-1],[r.right-1,r.bottom-1]].map(([x,y])=>{if(y<0||y>=innerHeight)return null;return document.elementFromPoint(x,y)?.closest('.gifts-placeholder')===e});
 return{bounds:r.toJSON(),image:ir.toJSON(),text:e.textContent.trim(),labelCount:e.querySelectorAll('p').length,overflow:s.overflow,radius:parseFloat(s.borderTopLeftRadius),objectFit:getComputedStyle(image).objectFit,natural:[image.naturalWidth,image.naturalHeight],currentSrc:image.currentSrc,cornerHitsInside:corners,graySamples:chroma.length,maxSampledChroma:Math.max(...chroma)};
}"""


def certificates(page, compact):
    page.locator('#certificates').scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    cards = page.locator('[data-certificate]')
    assert cards.count() == 4
    lefts = cards.evaluate_all('es=>es.map(e=>e.getBoundingClientRect().left)')
    assert all((lefts[i] < lefts[i+1]) if compact else (lefts[i] > lefts[i+1]) for i in range(3)), lefts
    for index in [0, 1, 2, 3, 0]:
        cards.nth(index).focus()
        page.wait_for_timeout(50)
        assert cards.nth(index).get_attribute('aria-pressed') == 'true'
    buy = page.locator('.certificate-buy')
    value = buy.evaluate("""e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),t=document.createRange();t.selectNodeContents(e);return{href:e.href,target:e.target,rel:e.rel,width:r.width,height:r.height,padding:parseFloat(s.paddingInlineStart),rects:t.getClientRects().length,fit:t.getBoundingClientRect().width<=r.width-parseFloat(s.paddingInlineStart)-parseFloat(s.paddingInlineEnd)+1}}""")
    assert value['href'] == 'https://o16013.yclients.ru/certificates' and value['target'] == '_blank' and 'noopener' in value['rel'], value
    assert value['height'] >= 44 and value['padding'] >= 12 and value['rects'] == 1 and value['fit'], value
    return {'cardLefts': lefts, 'keyboardSelectionCycle': True, 'buy': value}


with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', args=['--mute-audio'])
    for width in [961, 1100, 1440, 390, 800, 960]:
        for theme in ['light', 'dark']:
            context = browser.new_context(viewport={'width': width, 'height': 1000}, color_scheme=theme,
                                          reduced_motion='reduce')
            context.route('**/*', route_local)
            context.add_init_script('if(window.top===window){localStorage.setItem("soyuz_theme",'+json.dumps(theme)+');localStorage.setItem("soyuz_feedback_enabled","false")}')
            page = context.new_page()
            requests = []
            page.on('request', lambda request: requests.append(request.url) if re.search(r'construction-(?:poster|worker)-', request.url) else None)
            page.on('pageerror', lambda error: report['pageErrors'].append(str(error)))
            row = {'width': width, 'theme': theme, 'compact': width <= 960}
            try:
                page.goto(args.origin, wait_until='domcontentloaded')
                page.evaluate('document.fonts.ready')
                page.wait_for_timeout(250)
                poster = page.locator('.gifts-placeholder')
                if width <= 960:
                    assert not poster.is_visible()
                    steps = 0
                    while steps < 80:
                        at_bottom = page.evaluate('scrollY+innerHeight>=document.documentElement.scrollHeight-1')
                        if at_bottom:
                            break
                        page.evaluate('scrollTo({top:scrollY+innerHeight*.8,behavior:"instant"})')
                        page.wait_for_timeout(75)
                        steps += 1
                    page.wait_for_timeout(500)
                    assert page.evaluate('scrollY+innerHeight>=document.documentElement.scrollHeight-1'), 'did not reach footer'
                    assert requests == [], requests
                    assert poster.evaluate('e=>getComputedStyle(e).display') == 'none'
                    row.update(posterRequests=requests, scrollSteps=steps, reachedFooter=True)
                else:
                    page.wait_for_function('document.querySelector(".hero-scene").dataset.newsState==="ready"', timeout=12000)
                    arrows = []
                    for direction in ['prev', 'next']:
                        pair = {}
                        for kind, selector in [('hero', '[data-rail-controls="hero-news-rail"] [data-rail-step="'+('-1' if direction == 'prev' else '1')+'"]'),
                                               ('offer', '[data-of-'+direction+']')]:
                            control = page.locator(selector)
                            control.scroll_into_view_if_needed()
                            page.mouse.move(0, 0)
                            page.wait_for_timeout(200)
                            idle = control.evaluate(STYLE)
                            assert not idle['disabled'], (kind, idle)
                            control.hover()
                            page.wait_for_timeout(220)
                            hover = control.evaluate(STYLE)
                            pair[kind] = {'idle': idle, 'hover': hover}
                        for state in ['idle', 'hover']:
                            for key in ['background', 'color', 'radius', 'width', 'height']:
                                assert pair['hero'][state][key] == pair['offer'][state][key], (direction, state, key, pair)
                        assert pair['hero']['idle']['background'] != pair['hero']['hover']['background'], pair
                        arrows.append({'direction': direction, **pair})
                    page.mouse.move(0, 0)
                    poster.scroll_into_view_if_needed()
                    page.wait_for_function('document.querySelector(".gifts-placeholder-art").complete&&document.querySelector(".gifts-placeholder-art").naturalWidth>0')
                    geometry = poster.evaluate(GEOMETRY)
                    assert geometry['text'] == '' and geometry['labelCount'] == 0, geometry
                    assert '/construction-worker-' in geometry['currentSrc'] and geometry['maxSampledChroma'] <= 12, geometry
                    assert geometry['overflow'] == 'hidden' and geometry['radius'] > 0 and geometry['objectFit'] == 'cover', geometry
                    assert all(hit is not True for hit in geometry['cornerHitsInside']), geometry
                    for key in ['x', 'y', 'width', 'height']:
                        assert abs(geometry['bounds'][key]-geometry['image'][key]) <= 1, geometry
                    row.update(poster=geometry, arrows=arrows, posterRequests=requests)
                row['certificates'] = certificates(page, width <= 960)
                page.locator('#gifts').screenshot(path=str(OUT/f'{width}-{theme}.png'))
                row['pass'] = True
            except Exception:
                row.update(pass_=False, failure=traceback.format_exc(), posterRequests=requests)
                page.screenshot(path=str(OUT/f'failure-{width}-{theme}.png'))
            finally:
                report['cases'].append(row)
                context.close()
    browser.close()

report['sourceEnd'] = source_hashes()
report['unchanged'] = report['sourceStart'] == report['sourceEnd']
report['passed'] = sum(row.get('pass', False) for row in report['cases'])
report['failed'] = len(report['cases'])-report['passed']
(OUT/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'failed': report['failed'], 'pageErrors': report['pageErrors'],
                  'unchanged': report['unchanged'], 'results': str(OUT/'results.json')}, ensure_ascii=False))
assert report['failed'] == 0 and report['pageErrors'] == [] and report['unchanged']
