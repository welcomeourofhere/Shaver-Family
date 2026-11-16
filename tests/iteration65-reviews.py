"""Review batches, compact all-review rail and the two-unit desktop height limit."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('QA_URL', 'http://127.0.0.1:4321/')
OUT = ROOT / 'tmp/planning/iteration65/reviews.json'
OUT.parent.mkdir(parents=True, exist_ok=True)
COUNT = len(json.loads((ROOT / 'content/reviews.json').read_text(encoding='utf-8')))
NEWS = (ROOT / 'public/data/news.json').read_text(encoding='utf-8')
results, failures = [], []

def local_resources(route):
    # Reviews are local; unrelated feed requests use the committed public fixture, not an aborted cross-origin fetch.
    if route.request.url.endswith('/data/news.json'):
        route.fulfill(status=200, body=NEWS, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    elif route.request.url.startswith(URL):
        route.continue_()
    else:
        route.abort()

def state(page):
    return page.locator('#reviews-rail').evaluate("""rail=>({
      count:[...rail.children].filter(c=>!c.hidden&&getComputedStyle(c).display!=='none').length,
      compact:matchMedia('(max-width:960px)').matches,columns:Number(getComputedStyle(rail).getPropertyValue('--review-columns')),
      selected:Number(rail.dataset.railIndex),
      output:document.querySelector('[data-rail-controls="reviews-rail"] output').textContent.trim(),
      more:getComputedStyle(document.querySelector('[data-review-more]')).display!=='none',
      unit:parseFloat(getComputedStyle(rail).gridTemplateRows),gap:parseFloat(getComputedStyle(rail).rowGap),
      cards:[...rail.querySelectorAll('[data-review-card]')].filter(c=>!c.hidden).map(c=>({id:c.id,tone:c.dataset.reviewTone,x:c.style.getPropertyValue('--tile-x'),y:c.style.getPropertyValue('--tile-y'),w:Number(c.style.getPropertyValue('--tile-w')),h:Number(c.style.getPropertyValue('--tile-h')),height:c.getBoundingClientRect().height})),
      overflow:document.documentElement.scrollWidth>innerWidth+1
    })""")

with sync_playwright() as p:
    for engine in ['chromium', 'firefox', 'webkit']:
        browser = getattr(p, engine).launch(**({'channel': 'chrome'} if engine == 'chromium' else {}))
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        context.route('**/*', local_resources)
        page = context.new_page()
        page.set_default_timeout(15000)
        errors = []
        page.on('pageerror', lambda error: errors.append(error.stack))
        for width in [320, 390, 768, 960, 961, 1024, 1200, 1440]:
            page.goto('about:blank')
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(URL, wait_until='domcontentloaded')
            page.wait_for_function("document.querySelector('#reviews-rail').dataset.bentoReady==='true'")
            page.wait_for_function("()=>{const compact=matchMedia('(max-width:960px)').matches,rail=document.querySelector('#reviews-rail'),more=document.querySelector('[data-review-more]');return (rail.dataset.reviewLayout==='phone')===compact&&(getComputedStyle(more).display==='none')===compact}")
            page.locator('#reviews').scroll_into_view_if_needed()
            page.wait_for_timeout(100)
            before = state(page)
            assert not before['overflow'], (engine, width, before)
            if before['compact']:
                assert before['count'] == COUNT and not before['more'], (engine, width, before)
                assert before['output'].endswith(f'/ {COUNT:02}'), (engine, width, before)
                for index in range(1, COUNT):
                    page.locator('[data-rail-controls="reviews-rail"] [data-rail-step="1"]').click()
                    page.wait_for_function("index=>{const rail=document.querySelector('#reviews-rail');return Number(rail.dataset.railIndex)===index&&rail.dataset.railSettling!=='true'}", arg=index)
                assert state(page)['selected'] == COUNT - 1
                card = page.locator('#review-03')
                card.evaluate("e=>e.scrollIntoView({block:'center',inline:'start',behavior:'instant'})")
                page.wait_for_function("(()=>{const rail=document.querySelector('#reviews-rail');return rail.children[Number(rail.dataset.railIndex)]?.id==='review-03'&&rail.dataset.railSettling!=='true'})()")
                read = card.locator('[data-review-read]')
                assert read.is_visible(), (engine, width, 'individual reading missing')
                height = card.bounding_box()['height']
                read.click()
                page.wait_for_timeout(300)
                assert card.get_attribute('data-reading') == 'true'
                assert abs(card.bounding_box()['height'] - height) < 1
                read.click()
                page.wait_for_timeout(300)
                assert card.get_attribute('data-reading') == 'false'
            else:
                initial_count = 3 if before['columns'] == 3 else 4
                assert before['count'] == initial_count and before['more'], (engine, width, before)
                assert all(c['w'] <= 2 and c['h'] <= 2 and c['height'] <= before['unit'] * 2 + before['gap'] + 1 for c in before['cards']), (engine, width, before)
                page.locator('[data-review-more]').click()
                page.wait_for_function("document.querySelector('#reviews-rail').dataset.reviewExpanded==='true'")
                after = state(page)
                assert 6 <= after['count'] <= 8, (engine, width, after)
                if after['columns'] == 3:
                    assert after['count'] == 6
                if after['columns'] == 4:
                    assert after['count'] == 7
                assert all(c['w'] <= 2 and c['h'] <= 2 and c['height'] <= after['unit'] * 2 + after['gap'] + 1 for c in after['cards']), (engine, width, after)
                fixed = {c['id']: c for c in after['cards']}
                assert all(fixed[c['id']] == c for c in before['cards']), (engine, width, 'first group changed')
                page.locator('[data-review-more]').click()
                page.wait_for_function("document.querySelector('#reviews-rail').dataset.reviewExpanded==='false'")
                assert state(page)['count'] == initial_count
            results.append({'engine': engine, 'width': width, 'passed': True})
        # A real held mouse gesture changes the selected compact review without hiding the remaining cards.
        page.goto('about:blank')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(URL, wait_until='domcontentloaded')
        page.wait_for_function("document.querySelector('#reviews-rail').dataset.bentoReady==='true'")
        page.locator('#reviews-rail').evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})")
        box = page.locator('#reviews-rail').bounding_box()
        x, y = box['x'] + box['width'] * .8, box['y'] + box['height'] * .45
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(box['x'] + 12, y, steps=18)
        page.mouse.up()
        page.wait_for_function("Number(document.querySelector('#reviews-rail').dataset.railIndex)>0")
        assert state(page)['count'] == COUNT
        results.append({'engine': engine, 'mouseDrag': True})
        page.set_viewport_size({'width': 980, 'height': 1000})
        page.wait_for_function("document.querySelector('#reviews-rail').dataset.reviewLayout!=='phone'")
        assert state(page)['count'] == (3 if state(page)['columns'] == 3 else 4) and state(page)['more']
        page.set_viewport_size({'width': 960, 'height': 1000})
        page.wait_for_function("document.querySelector('#reviews-rail').dataset.reviewLayout==='phone'")
        assert state(page)['count'] == COUNT and not state(page)['more']
        results.append({'engine': engine, 'breakpointRoundTrip': True})
        page.set_viewport_size({'width': 961, 'height': 1000})
        page.wait_for_timeout(200)
        modes = page.evaluate("""()=>new Promise(resolve=>{const frames=[];function sample(){const rail=document.querySelector('#reviews-rail'),compact=matchMedia('(max-width:960px)').matches;frames.push({compact,layout:rail.dataset.reviewLayout});if(frames.length<20)requestAnimationFrame(sample);else resolve(frames)}requestAnimationFrame(sample)})""")
        assert len({(s['compact'], s['layout']) for s in modes}) == 1, (engine, 'scrollbar feedback at 961px', modes)
        assert all((s['layout'] == 'phone') == s['compact'] for s in modes), (engine, modes)
        results.append({'engine': engine, 'width': 961, 'stableBreakpointFrames': len(modes)})
        if errors:
            failures.append({'engine': engine, 'pageErrors': errors})
        context.close()
        # Progressive enhancement keeps every review available without any script.
        for width in [390, 1440]:
            context = browser.new_context(viewport={'width': width, 'height': 1000}, java_script_enabled=False)
            page = context.new_page()
            page.goto(URL, wait_until='domcontentloaded')
            visible = page.locator('#reviews-rail>[data-review-card]').evaluate_all("cards=>cards.filter(c=>getComputedStyle(c).display!=='none').length")
            assert visible == COUNT, (engine, width, 'no-JS review count', visible)
            results.append({'engine': engine, 'width': width, 'noJavaScript': True})
            context.close()
        browser.close()
        print(f'PASS {engine}: reviews, reading, held drag, no-JavaScript', flush=True)
OUT.write_text(json.dumps({'cases': results, 'failures': failures, 'published': False}, ensure_ascii=False, indent=2), encoding='utf-8')
assert not failures, failures
print(f'PASS {len(results)} real-browser review scenarios; {OUT}')
