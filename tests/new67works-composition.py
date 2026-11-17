"""Bounded real-layout check; run only against the agreed frozen candidate."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--origin', required=True)
parser.add_argument('--label', required=True)
args = parser.parse_args()
OUT = ROOT / 'artifacts/iteration67/works-composition' / args.label
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ['src/components/Works.astro', 'src/styles/works.css', 'src/scripts/works.ts',
          'src/scripts/works-layout.ts', 'src/components/Masters.astro', 'src/scripts/team.ts']
hashes = lambda: {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE}
before = hashes()
results, errors = [], []
WIDTHS = [320, 360, 390, 420, 540, 600, 601, 800, 801, 960, 1100, 1101, 1440]
STATE = """root=>{
 const box=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
 const cards=[...root.querySelectorAll('[data-work-card]')],current=cards.find(e=>e.dataset.workCurrent==='true');
 const neighbor=offset=>cards.find(e=>Math.abs(parseFloat(e.style.getPropertyValue('--work-offset'))-offset)<.001);
 const portrait=e=>{const m=new DOMMatrix(getComputedStyle(e).transform);return{...box(e),rawWidth:e.offsetWidth,angle:Math.atan2(m.b,m.a)*180/Math.PI,scale:Math.hypot(m.a,m.b)}};
 const caption=root.querySelector('.works-caption'),controls=root.querySelector('.works-controls');
 return{shell:box(root),center:portrait(current),left:portrait(neighbor(-1)),right:portrait(neighbor(1)),
  depth:+getComputedStyle(root).getPropertyValue('--works-neighbor-limit'),
  visible:cards.filter(e=>!e.hidden&&getComputedStyle(e).display!=='none'&&+getComputedStyle(e).opacity>.99).length,
  caption:box(caption),controls:box(controls),overflow:document.documentElement.scrollWidth-innerWidth,
  title:root.querySelector('.works-caption-current h3').textContent,expected:current.dataset.workCaption,
  author:root.querySelector('[data-work-author]').textContent,expectedAuthor:current.dataset.workMaster,
  order:[...document.querySelectorAll('.team-card .team-book')].map(e=>({id:e.dataset.master,href:e.href,dialog:e.closest('.team-card').querySelector('[data-team-open]').dataset.teamOpen}))};
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')
    try:
        for theme in ['light', 'dark']:
            for width, text_scale in [(width, 1) for width in WIDTHS] + [(width, 2) for width in [390, 600, 961, 1440]]:
                context = browser.new_context(viewport={'width': width, 'height': 900 if width > 960 else 844}, color_scheme=theme, reduced_motion='reduce')
                try:
                    page = context.new_page()
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(args.origin, wait_until='domcontentloaded')
                    page.wait_for_function('document.querySelector(".works-fan").hasAttribute("data-work-position")')
                    if text_scale == 2:
                        page.locator('#works').evaluate("""root=>{const nodes=[...root.querySelectorAll('h2,.sd-tab,.works-caption-current h3,.works-caption-current p,.works-caption-size,output')],sizes=nodes.map(e=>parseFloat(getComputedStyle(e).fontSize)*2);nodes.forEach((e,i)=>e.style.fontSize=sizes[i]+'px')}""")
                    page.locator('.works-fan').scroll_into_view_if_needed()
                    page.wait_for_timeout(80)
                    state = page.locator('#works').evaluate(STATE)
                    normal = lambda value: ' '.join(value.split())
                    assert state['overflow'] <= 1, state
                    assert normal(state['title']) == normal(state['expected']) and normal(state['author']) == normal(state['expectedAuthor']), state
                    assert abs(state['center']['width'] - state['center']['rawWidth']) <= 1, state
                    expected_depth = 1 if width <= 600 else 2 if width <= 800 else 3 if width <= 1100 else 4
                    assert state['depth'] == expected_depth and state['visible'] == expected_depth * 2 + 1, state
                    assert len(state['order']) == 6 and len({master['id'] for master in state['order']}) == 6, state
                    assert all(master['id'] == master['dialog'] for master in state['order']), state
                    if width <= 600:
                        scale, angle = (.78, 2) if width <= 360 else (.82, 3) if width <= 420 else (.86, 4)
                        assert abs(state['left']['left'] - state['shell']['left']) <= 1, state
                        assert abs(state['right']['right'] - state['shell']['right']) <= 1, state
                        assert abs(state['left']['scale'] - scale) < .001 and abs(state['right']['scale'] - scale) < .001, state
                        assert abs(state['left']['angle'] + angle) < .01 and abs(state['right']['angle'] - angle) < .01, state
                        assert 23 <= state['caption']['top'] - state['center']['bottom'] <= 25, state
                        assert 7 <= state['controls']['top'] - state['caption']['bottom'] <= 9, state
                    if text_scale == 1 and width in [390, 1440]:
                        current = page.locator('[data-work-current=true]')
                        current.focus()
                        page.keyboard.press('ArrowRight')
                        page.wait_for_function('document.querySelector(".works-fan").dataset.workIndex==="1"')
                        page.keyboard.press('Home')
                        page.wait_for_function('document.querySelector(".works-fan").dataset.workIndex==="0"')
                    if width in [320, 390, 600, 1440] and text_scale == 1:
                        page.locator('#works').screenshot(path=str(OUT / f'{width}-{theme}.png'))
                    results.append({'width': width, 'theme': theme, 'textScale': text_scale, 'state': state})
                finally:
                    context.close()
    finally:
        browser.close()

assert not errors, errors
assert hashes() == before, 'Source changed during the agreed frozen run'
assert len({tuple(master['id'] for master in row['state']['order']) for row in results}) > 1, 'Entry order never changed'
(OUT / 'report.json').write_text(json.dumps({'origin': args.origin, 'cases': results, 'pageerrors': errors, 'sourceHashes': before}, ensure_ascii=False, indent=2), encoding='utf8')
print('PASS', len(results), 'Works composition contexts; 0 pageerrors; source unchanged; browser closed')
