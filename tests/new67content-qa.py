"""Bounded Chromium content QA on a frozen compiled origin, never HMR or real booking.

Example: python -X utf8 tests/new67content-qa.py --origin http://127.0.0.1:PORT/
  --label NEW_LABEL --build BUILD_ID
The optional --provider-pin captures actual Yandex Maps evidence for human review; it
does not turn an iframe load, business name or HTTP200 into a verified map pin.
"""
import argparse
import hashlib
import json
import math
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ['titles', 'faq', 'reviews', 'back', 'posters', 'nojs', 'metadata', 'map']
SOURCE = ['src/components/Hero.astro', 'src/config/headlines.ts', 'src/components/FAQ.astro',
          'src/styles/faq.css', 'src/components/Reviews.astro', 'src/styles/reviews.css',
          'src/components/PageBack.astro', 'src/scripts/page-back.ts', 'src/components/Offers.astro',
          'src/scripts/offers.ts', 'src/components/Contacts.astro', 'src/scripts/contact-map.ts',
          'src/styles/contacts.css', 'src/layouts/Document.astro', 'content/site.json',
          'content/seo.json', 'content/offers.json', 'content/offer-poster-sources.json']


def hashes():
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE}


def plain(text):
    return re.sub(r'\s+%', '%', re.sub(r'\s+', ' ', text).strip())


def clean_url(url):
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))


def contrast(a, b):
    def luminance(rgb):
        values = [v / 255 for v in rgb[:3]]
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, [.2126, .7152, .0722]))
    first, second = sorted([luminance(a), luminance(b)])
    return (second + .05) / (first + .05)


TEXT_GEOMETRY = r"""e=>{const r=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect(),s=getComputedStyle(e),walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let n;const rects=[];while(n=walker.nextNode()){if(!n.textContent.trim())continue;const range=document.createRange();range.selectNodeContents(n);for(const b of range.getClientRects())if(b.width&&b.height)rects.push(b.toJSON());}return{text:e.innerText,bounds:r.toJSON(),parent:p.toJSON(),font:s.font,fontSize:parseFloat(s.fontSize),color:s.color,overflow:e.scrollWidth>e.clientWidth+1,rects,pageOverflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1}}"""
LINK_COLORS = r"""e=>{const item=e.closest('.faq-item'),p=e.closest('p'),s=getComputedStyle(e),canvas=document.createElement('canvas');canvas.width=canvas.height=1;const c=canvas.getContext('2d'),rgb=value=>{c.clearRect(0,0,1,1);c.fillStyle=value;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data]};return{text:e.innerText,href:e.href,target:e.target,rel:e.rel,tone:item.dataset.faqTone,color:rgb(s.color),paragraph:rgb(getComputedStyle(p).color),background:rgb(getComputedStyle(item).backgroundColor),decoration:s.textDecorationLine}}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin')
    parser.add_argument('--label')
    parser.add_argument('--build', help='Declared frozen package identity; observed URL identities are recorded separately')
    parser.add_argument('--only', default=','.join(SECTIONS))
    parser.add_argument('--provider-pin', action='store_true', help='Actual-provider read-only capture; human pin review remains explicit')
    parser.add_argument('--self-check', action='store_true', help='Pure helper checks only; starts no browser')
    args = parser.parse_args()
    if args.self_check:
        assert plain('Первый\nвизит со скидкой\u00a030%') == 'Первый визит со скидкой 30%'
        assert clean_url('https://example.org/a?token=hidden#fragment') == 'https://example.org/a'
        assert math.isclose(contrast([0, 0, 0], [255, 255, 255]), 21)
        assert math.isclose(contrast([64, 64, 64], [64, 64, 64]), 1)
        print('PASS 4 pure checks; browserRuns=0')
        return
    assert args.origin and args.label, '--origin and a fresh --label are required'
    parsed_origin = urlsplit(args.origin)
    assert parsed_origin.scheme in ['http', 'https'] and parsed_origin.netloc and not parsed_origin.query
    assert re.fullmatch(r'[\w-]+', args.label), 'Use a simple new immutable evidence label'
    sections = args.only.split(',')
    assert sections and set(sections) <= set(SECTIONS), sections
    out = ROOT / 'artifacts/iteration67/content-qa' / args.label
    out.mkdir(parents=True, exist_ok=False)
    site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
    offers = json.loads((ROOT / 'content/offers.json').read_text(encoding='utf-8'))['offers']
    poster_sources = json.loads((ROOT / 'content/offer-poster-sources.json').read_text(encoding='utf-8'))['images']
    legal = json.loads((ROOT / 'content/legal/pages.json').read_text(encoding='utf-8'))['pages']
    social = json.loads((ROOT / 'content/seo-assets.json').read_text(encoding='utf-8'))
    offer_ids = [offer['id'] for offer in offers]
    poster_ids = {Path(urlsplit(v['url']).path).name: item['id'] for item in poster_sources for v in item['variants']}
    report = {'origin': args.origin, 'declaredBuild': args.build, 'utc': datetime.now(timezone.utc).isoformat(),
              'engine': 'Chromium/channel=chrome', 'sections': sections, 'sourceStart': hashes(),
              'cases': [], 'pageErrors': [], 'providerChecks': [], 'frozenRejected': False,
              'boundary': 'Frozen compiled DOM and trusted Chromium input; no response fixtures, own asset replacement, booking, payment, calls, messages, physical-phone or performance claim.'}

    def save():
        (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def is_own(url):
        part = urlsplit(url)
        return part.netloc == parsed_origin.netloc or part.hostname == 'storage.yandexcloud.net' and '/Soyuz/' in part.path

    def run(browser, name, action, width=1440, theme='light', js=True, touch=False, actual_provider=False):
        row = {'name': name, 'width': width, 'theme': theme, 'javaScript': js, 'touch': touch,
               'pass': False, 'pageErrors': [], 'ownRequestFailures': [], 'blockedProviders': [], 'posterRequests': [], 'documents': []}
        context = browser.new_context(viewport={'width': width, 'height': 1000}, color_scheme=theme,
                                      reduced_motion='reduce', java_script_enabled=js, is_mobile=touch, has_touch=touch)
        def guard(route):
            host = urlsplit(route.request.url).hostname or ''
            if host == 'yclients.ru' or host.endswith('.yclients.ru') or host == 'yclients.com' or host.endswith('.yclients.com'):
                row['blockedProviders'].append(clean_url(route.request.url));route.abort()
            else:
                route.continue_()
        # The optional stationary Yandex view retains browser caching and its native Referer.
        if not actual_provider:context.route('**/*', guard)
        page = context.new_page();page.set_default_timeout(20000)
        page.on('pageerror', lambda error: row['pageErrors'].append(str(error)))
        def requested(request):
            basename = Path(urlsplit(request.url).path).name
            if '/media/offers/' in urlsplit(request.url).path and basename in poster_ids:row['posterRequests'].append({'id': poster_ids[basename], 'url': clean_url(request.url)})
        page.on('request', requested)
        page.on('requestfailed', lambda request: row['ownRequestFailures'].append({'url': clean_url(request.url), 'type': request.resource_type, 'error': request.failure}) if is_own(request.url) else None)

        def ready(url=args.origin):
            response = page.goto(url, wait_until='domcontentloaded', timeout=35000)
            assert response and response.status == 200, (url, response.status if response else None)
            body = response.body();html = body.decode('utf-8')
            if '/@vite/client' in html or 'vite:beforeUpdate' in html:
                report['frozenRejected'] = True
                raise AssertionError('HMR origin rejected; use the frozen compiled release')
            identities = sorted(set(re.findall(r'/Soyuz/releases/([a-f0-9]{20})/_astro/', html)))
            if args.build and identities:assert identities == [args.build], identities
            row['documents'].append({'url': clean_url(response.url), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'observedModuleBuilds': identities})
            page.evaluate('document.fonts.ready')
            if js:
                page.wait_for_function('(t)=>document.documentElement.dataset.theme===t', arg=theme)
                page.wait_for_function('document.documentElement.dataset.cookiePrompt!==undefined')
                prompt = page.locator('[data-analytics-prompt]')
                if prompt.is_visible():
                    prompt.locator('[data-analytics-settings]').click()
                    page.locator('#cookie-settings').wait_for(state='visible')
                    page.locator('#cookie-settings [data-analytics-withdraw]').click()
                    page.wait_for_function('!document.querySelector("#cookie-settings").open')
                    prompt.wait_for(state='hidden')
        try:
            action(page, context, row, ready)
            assert not row['pageErrors'], row['pageErrors']
            assert not row['blockedProviders'], ('Unexpected booking/purchase request', row['blockedProviders'])
            bad = [item for item in row['ownRequestFailures'] if 'ABORTED' not in str(item['error']).upper()]
            assert not bad, bad
            row['pass'] = True
        except Exception:
            row['failure'] = traceback.format_exc()
            try:page.screenshot(path=str(out / f'{name}-failure.png'), timeout=5000)
            except Exception as error:row['screenshotFailure'] = str(error)
        finally:
            try:context.close()
            except Exception as error:row.update(closeFailure=str(error), **{'pass': False})
            report['pageErrors'].extend({'case': name, 'error': value} for value in row['pageErrors'])
            report['cases'].append(row);save()
        if report['frozenRejected']:raise RuntimeError('Stopped after rejecting HMR origin')

    def title_case(scale):
        def check(page, context, row, ready):
            ready()
            if scale == 2:
                page.locator('#welcome-offer').evaluate("""e=>{const es=[...e.querySelectorAll('.headline,p,.promo-code,.btn,small')],sizes=es.map(n=>parseFloat(getComputedStyle(n).fontSize));es.forEach((n,i)=>n.style.fontSize=sizes[i]*2+'px')}""")
            title = page.locator('#first-title');value = title.evaluate(TEXT_GEOMETRY)
            assert plain(value['text']).casefold() == f'Первый визит со скидкой {site["firstVisitPercent"]}%'.casefold(), value
            assert not value['overflow'] and not value['pageOverflow'] and value['rects'], value
            assert 'Molot' in value['font'] and value['fontSize'] >= 26, value
            if scale == 1:
                assert len({round(rect['top'], 1) for rect in value['rects']}) <= 2, value
            for rect in value['rects']:
                assert rect['left'] >= value['parent']['left'] - 1 and rect['right'] <= value['parent']['right'] + 1, value
                assert rect['top'] >= value['parent']['top'] - 1 and rect['bottom'] <= value['parent']['bottom'] + 1, value
            page.locator('#welcome-offer').screenshot(path=str(out / f'{row["name"]}.png'))
            row.update(title=value, textScale=scale, textScaleScope='promo heading, body, code, action and note')
        return check

    def faq_case(page, context, row, ready):
        ready();more = page.locator('#faq [data-faq-more]')
        if more.is_visible():more.click()
        links = []
        for details in page.locator('#faq .faq-item').all():
            if not details.locator('.faq-answer a').count():continue
            summary = details.locator('summary');summary.focus();summary.press('Enter')
            assert details.get_attribute('open') is not None
            for link in details.locator('.faq-answer a').all():
                value = link.evaluate(LINK_COLORS);value['contrast'] = contrast(value['color'], value['background'])
                assert value['contrast'] >= 4.5, value
                assert value['color'][:3] != value['paragraph'][:3] and 'underline' in value['decoration'], value
                assert value['href'].startswith(('tel:', 'mailto:', 'https://')), value
                link.focus();focus = link.evaluate(LINK_COLORS);focus['contrast'] = contrast(focus['color'], focus['background']);assert focus['contrast'] >= 4.5, focus
                value['focus'] = focus;links.append(value)
            summary.focus();summary.press('Enter')
        assert any(link['href'] == 'tel:' + site['phoneLink'] for link in links), links
        maps = [link for link in links if urlsplit(link['href']).hostname == 'yandex.ru']
        assert any(site['address'] in parse_qs(urlsplit(link['href']).query).get('text', [''])[0] or '/org/soyuz/116019915414/' in link['href'] for link in maps), maps
        row['links'] = links

    def reviews_case(page, context, row, ready):
        ready();page.locator('#reviews').scroll_into_view_if_needed()
        values = page.locator('#reviews .review-prose blockquote').evaluate_all("""es=>es.map(e=>({style:getComputedStyle(e).fontStyle,opening:getComputedStyle(e.firstElementChild,'::before').content,closing:getComputedStyle(e.lastElementChild,'::after').content,text:e.textContent.trim().length}))""")
        assert values and all(v['style'] == 'italic' and '«' in v['opening'] and '»' in v['closing'] and v['text'] for v in values), values
        page.locator('#reviews .review-card').first.screenshot(path=str(out / f'{row["name"]}.png'));row['quotes'] = values

    def back_case(slug, direct=False):
        def check(page, context, row, ready):
            if direct:
                ready(urljoin(args.origin, slug + '/'));link = page.locator('[data-page-back]');href = link.get_attribute('href')
                assert href == '/#contacts', href
                link.click();page.wait_for_url(lambda url: urlsplit(url).path == '/' and urlsplit(url).fragment == 'contacts')
                row.update(fallback=href, finalUrl=page.url)
            else:
                ready();home = page.url
                page.locator(f'#footer a[href="/{slug}/"]').click()
                page.wait_for_url(lambda url: urlsplit(url).path.rstrip('/') == '/' + slug)
                page.locator('[data-page-back]').wait_for(state='visible');page.evaluate('document.fonts.ready')
                row['previous'] = page.evaluate('({referrer:document.referrer,length:history.length})')
                assert urlsplit(row['previous']['referrer']).netloc == parsed_origin.netloc and row['previous']['length'] > 1
                page.locator('[data-page-back]').click();page.wait_for_url(home)
                row.update(home=home, returnedUrl=page.url)
        return check

    def posters_case(page, context, row, ready):
        ready();page.locator('#offers').scroll_into_view_if_needed()
        page.wait_for_function('document.querySelector("[data-offers]").dataset.offerIndex!==undefined')
        page.wait_for_timeout(350)
        before = page.locator('[data-offers]').evaluate("""e=>{const r=e.querySelector('[data-of-rail]'),cards=[...r.querySelectorAll('[data-offer-id]')];return{selected:Number(e.dataset.offerIndex),reach:innerWidth<=960?1:Math.ceil(r.clientWidth/cards[0].clientWidth),assigned:cards.filter(c=>!c.querySelector('.of-photo>img').dataset.offerSrc).map(c=>c.dataset.offerId)}}""")
        compact = row['width'] <= 960
        allowed = {offer_ids[0], offer_ids[1]}
        for index, offer_id in enumerate(offer_ids):
            distance = abs(index - before['selected']) if compact else min((index - before['selected']) % len(offer_ids), (before['selected'] - index) % len(offer_ids))
            if distance <= before['reach']:allowed.add(offer_id)
        requested = {item['id'] for item in row['posterRequests']}
        assert requested and len(requested) < len(offer_ids) and requested <= allowed, (requested, allowed, before)
        assert set(before['assigned']) <= allowed, before
        target = 2
        if compact:
            rail = page.locator('[data-of-rail]');rect = rail.bounding_box();assert rect
            x, y = rect['x'] + min(rect['width'] * .65, 250), rect['y'] + min(rect['height'] * .4, 180)
            cdp = context.new_cdp_session(page)
            for unused in range(2):
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y, 'id': 1}]})
                for step in range(1, 13):
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x - min(rect['width'] * .8, 260) * step / 12, 'y': y, 'id': 1}]});page.wait_for_timeout(16)
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []});page.wait_for_timeout(400)
            cdp.detach()
            selected = int(page.locator('[data-offers]').get_attribute('data-offer-index'));assert selected >= 1, selected
            target = selected
        else:
            page.locator('[data-of-next]').click();page.locator('[data-of-next]').click()
            page.wait_for_function('document.querySelector("[data-offers]").dataset.offerIndex==="2"')
        card = page.locator(f'[data-offer-id="{offer_ids[target]}"]');image = card.locator('.of-photo>img')
        page.wait_for_function('(id)=>{const e=document.querySelector(`[data-offer-id="${id}"] .of-photo>img`);return e.complete&&e.naturalWidth>1&&!e.dataset.offerSrc}', arg=offer_ids[target])
        assert Path(urlsplit(image.get_attribute('src')).path).name in poster_ids
        assert offer_ids[target] in {item['id'] for item in row['posterRequests']}, row['posterRequests']
        row.update(initial=before, initialRequested=sorted(requested), allowedInitial=sorted(allowed), selectedAfterInput=target, selectedSrc=image.get_attribute('src'))

    def nojs_case(page, context, row, ready):
        ready()
        cards = page.locator('#offers [data-offer-id]');assert cards.count() == len(offer_ids) == 11
        sources = []
        for card in cards.all():
            urls = card.locator('.of-photo img').evaluate_all('es=>es.map(e=>e.getAttribute("src")).filter(src=>src&&!src.startsWith("data:"))')
            assert urls and any(Path(urlsplit(url).path).name in poster_ids for url in urls), (card.get_attribute('data-offer-id'), urls)
            sources.append({'id': card.get_attribute('data-offer-id'), 'realPosterURLs': urls})
        details = page.locator('#faq .faq-item');assert details.count() > 5 and all(item.is_visible() for item in details.all())
        assert not page.locator('#faq .faq-more').is_visible() and not page.locator('#reviews .reviews-more').is_visible()
        review_values = page.locator('#reviews .review-card').evaluate_all('es=>es.map(e=>({display:getComputedStyle(e).display,visibility:getComputedStyle(e).visibility,text:e.textContent.trim().length}))')
        assert review_values and all(v['display'] == 'grid' and v['visibility'] == 'visible' and v['text'] for v in review_values), review_values
        row.update(posters=sources, noJSPosterClaim='All eleven real source URLs exist; offscreen lazy downloads and all-card visual access are not claimed', faqCount=details.count(), reviews=review_values)

    def metadata_case(page, context, row, ready):
        ready()
        values = page.evaluate("""()=>({images:[...document.querySelectorAll('meta[property="og:image"]')].map(e=>e.content),widths:[...document.querySelectorAll('meta[property="og:image:width"]')].map(e=>e.content),heights:[...document.querySelectorAll('meta[property="og:image:height"]')].map(e=>e.content),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>JSON.parse(e.textContent)),icons:[...document.querySelectorAll('link[rel="icon"]')].map(e=>e.href)})""")
        row['metadata'] = values
        assert values['images'] and '1000' in values['widths'] and '1000' in values['heights'], values
        row['resolvedSocialURL'] = urljoin(page.url, values['images'][0])
        body = context.request.get(row['resolvedSocialURL'], timeout=25000);assert body.status == 200
        image = body.body();assert image[:8] == b'\x89PNG\r\n\x1a\n' and [int.from_bytes(image[16:20], 'big'), int.from_bytes(image[20:24], 'big')] == [1000, 1000]
        assert hashlib.sha256(image).hexdigest() == social['social']['sha256']
        row.update(socialBytes=len(image), socialSha256=hashlib.sha256(image).hexdigest())
        structured = [node for item in values['schema'] for node in (item.get('@graph', []) if isinstance(item, dict) and '@graph' in item else [item])]
        business = next(item for item in structured if item.get('@type') == 'HairSalon')
        assert business['logo']['@type'] == 'ImageObject' and business['logo']['width'] == business['logo']['height'] == 512
        assert urlsplit(business['logo']['url']).path.endswith('/brand/logo-square-512.png') and business['image'] in values['images'], business
        row['businessLogo'] = business['logo']
        if parsed_origin.hostname in ['127.0.0.1', 'localhost']:
            row.update(nativeFaviconChecked=False, nativeFaviconBoundary='Frozen export omits the native Tilda favicon owner; public delivery is checked separately')
        else:
            assert values['icons'], 'Public document must expose its native favicon'
            allowed = {item['sha256'] for item in social['favicon']['rasters']}
            allowed.update([social['favicon']['svg']['sha256'], social['favicon']['svg']['sourceSha256'], social['favicon']['source']['sha256'], hashlib.sha256((ROOT / 'public/brand/favicon-red.svg').read_bytes()).hexdigest()])
            observed = []
            for icon in set(values['icons']):
                response = context.request.get(urljoin(page.url, icon), timeout=20000)
                observed.append({'url': icon, 'status': response.status, 'sha256': hashlib.sha256(response.body()).hexdigest()})
            row['nativeFavicons'] = observed
            assert any(item['status'] == 200 and item['sha256'] in allowed for item in observed), observed
            row['nativeFaviconChecked'] = True

    def map_case(page, context, row, ready):
        ready();host = page.locator('.contact-map');host.scroll_into_view_if_needed()
        page.wait_for_function('Boolean(document.querySelector(".contact-map>iframe[data-map-src]").getAttribute("src"))')
        frame = host.locator(':scope>iframe');src = frame.get_attribute('src');query = parse_qs(urlsplit(src).query)
        assert urlsplit(src).hostname == 'yandex.ru' and urlsplit(src).path == '/map-widget/v1/', src
        assert query.get('oid') == ['116019915414'] and query.get('ol') == ['biz'] and query.get('ll') == ['49.669973,58.588674'], query
        assert frame.get_attribute('referrerpolicy') == 'strict-origin-when-cross-origin'
        assert frame.evaluate('e=>getComputedStyle(e).pointerEvents') == 'none' and frame.get_attribute('tabindex') == '-1'
        assert page.locator('.contact-address').get_attribute('href') == 'https://yandex.ru/maps/org/soyuz/116019915414/'
        rect = host.bounding_box();assert rect
        x, y = rect['x'] + rect['width'] / 2, max(140, min(780, rect['y'] + rect['height'] / 2))
        assert page.evaluate('p=>Boolean(document.elementFromPoint(p.x,p.y)?.closest(".contact-map"))', {'x': x, 'y': y})
        cdp = context.new_cdp_session(page);before = page.evaluate('scrollY')
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y, 'id': 1}]})
        for step in range(1, 11):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y - 160 * step / 10, 'id': 1}]});page.wait_for_timeout(20)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []});page.wait_for_timeout(250)
        after = page.evaluate('scrollY');assert after > before + 40, (before, after)
        host.scroll_into_view_if_needed();rect = host.bounding_box();x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        scale = page.evaluate('visualViewport.scale')
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x - 30, 'y': y, 'id': 1}, {'x': x + 30, 'y': y, 'id': 2}]})
        for step in range(1, 9):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x - 30 - step * 6, 'y': y, 'id': 1}, {'x': x + 30 + step * 6, 'y': y, 'id': 2}]});page.wait_for_timeout(20)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []});page.wait_for_timeout(150)
        after_scale = page.evaluate('visualViewport.scale');assert after_scale > scale + .1, (scale, after_scale)
        cdp.detach();row.update(embed=src, providerState=host.get_attribute('data-map-state'), scrollTravel=after-before, pageScaleBefore=scale, pageScaleAfter=after_scale, actualProviderPinVerified=False)

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', args=['--mute-audio'])
            if 'titles' in sections:
                for width in [320, 390, 600, 800, 960, 1100, 1440]:
                    for theme in ['light', 'dark']:run(browser, f'title-{width}-{theme}', title_case(1), width, theme)
                for width in [320, 800, 1440]:
                    for theme in ['light', 'dark']:run(browser, f'title-text200-{width}-{theme}', title_case(2), width, theme)
            for theme in ['light', 'dark']:
                if 'faq' in sections:run(browser, f'faq-links-{theme}', faq_case, 1100, theme)
                if 'reviews' in sections:run(browser, f'review-quotes-{theme}', reviews_case, 1100, theme)
            if 'back' in sections:
                for item in legal:
                    run(browser, 'back-history-' + item['slug'], back_case(item['slug']))
                    run(browser, 'back-nojs-' + item['slug'], back_case(item['slug'], True), 390, js=False)
            for width in [390, 1440]:
                if 'posters' in sections:run(browser, f'poster-window-{width}', posters_case, width, touch=width <= 960)
                if 'nojs' in sections:run(browser, f'nojs-content-{width}', nojs_case, width, js=False)
            if 'metadata' in sections:run(browser, 'square-metadata', metadata_case)
            if 'map' in sections:
                for width in [390, 800]:run(browser, f'map-touch-{width}', map_case, width, touch=True)
            if args.provider_pin:
                def provider(page, context, row, ready):
                    ready();host = page.locator('.contact-map');host.scroll_into_view_if_needed()
                    page.wait_for_function('Boolean(document.querySelector(".contact-map>iframe[data-map-src]").getAttribute("src"))')
                    page.wait_for_function('["ready","error"].includes(document.querySelector(".contact-map").dataset.mapState)', timeout=26000)
                    frame = host.locator(':scope>iframe').element_handle().content_frame()
                    text = frame.locator('body').inner_text(timeout=5000) if frame else ''
                    blocked = bool(re.search('captcha|капч|робот|доступ ограничен|access denied', text, re.I)) or host.get_attribute('data-map-state') == 'error'
                    host.screenshot(path=str(out / 'actual-provider-pin-review.png'))
                    report['providerChecks'].append({'status':'blocked' if blocked else 'needs-visual-review','providerState':host.get_attribute('data-map-state'),'provider':'yandex','pinVerified':False,'evidence':'actual-provider-pin-review.png','reason':'Actual Yandex business widget requires a visual check of the organisation marker. Document load alone does not verify it.'})
                run(browser, 'provider-pin-observation', provider, 390, touch=True, actual_provider=True)
            browser.close();browser = None
    except Exception:
        report['fatal'] = traceback.format_exc()
    finally:
        if browser:
            try:browser.close();browser = None
            except Exception as error:report['browserCloseFailure'] = str(error)
        report['sourceEnd'] = hashes();report['sourceUnchanged'] = report['sourceStart'] == report['sourceEnd']
        report['browsersClosed'] = browser is None
        report['functionalPass'] = bool(report['cases']) and all(row['pass'] for row in report['cases']) and not report['pageErrors'] and not report.get('fatal') and report['sourceUnchanged'] and report['browsersClosed']
        report['providerPinVerified'] = False
        report['allRequestedChecksPass'] = report['functionalPass'] and not args.provider_pin
        save()
    print(json.dumps({'functionalPass': report['functionalPass'], 'cases': len(report['cases']), 'pageErrors': len(report['pageErrors']), 'providerPinVerified': False, 'report': str(out / 'verification.json')}, ensure_ascii=False))
    raise SystemExit(0 if report['allRequestedChecksPass'] else 2 if report['functionalPass'] else 1)


if __name__ == '__main__':
    main()
