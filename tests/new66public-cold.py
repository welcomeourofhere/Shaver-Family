"""Read-only actual HTTPS SY-003/009 probe; six fresh contexts, no form submission."""
import argparse
import hashlib
import json
import re
import time
import traceback
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://soyuz.hair/'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--label', required=True)
parser.add_argument('--expected-build', default='5d36176754bbdd000991')
args = parser.parse_args()
assert re.fullmatch(r'[\w-]+', args.label)
assert re.fullmatch(r'[a-f0-9]{20}', args.expected_build)
OUT = ROOT / 'artifacts/iteration66/public-cold' / args.label
OUT.mkdir(parents=True, exist_ok=False)


def clean_url(value):
    try:
        u = urlsplit(value)
        return urlunsplit((u.scheme, u.netloc, u.path, '', ''))
    except Exception:
        return '[unparseable URL]'


def safe_text(value):
    text = str(value)
    if re.search(r'(?i)\b(cookie|token|authorization|session|secret|password|access[_-]?key|api[_-]?key|bearer|credential)s?\b', text):
        return '[message omitted: sensitive marker]'
    text = re.sub(r'https?://[^\s\]\)<>"\']+', lambda m: clean_url(m.group()), text)
    text = re.sub(r'\?[^\s<>"\']+', '?[query omitted]', text)
    return text[:1600]


def category(url):
    parsed = urlsplit(url)
    host = parsed.hostname or ''
    if host.endswith('.yclients.ru') or host == 'yclients.ru':
        return 'provider'
    if host in ['soyuz.hair', 'www.soyuz.hair'] or '/Soyuz/releases/' in parsed.path:
        return 'site'
    if host == 'raw.githubusercontent.com' and '/soyuz/' in parsed.path.lower():
        return 'feed'
    if 'tilda' in host:
        return 'platform'
    return 'third_party'


def product_hashes():
    return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['src', 'content'] for p in sorted((ROOT / folder).rglob('*')) if p.is_file()}


STATE = """()=>{
 const hero=document.querySelector('.hero-scene'),reviews=document.querySelector('[data-review-bento]'),drawer=document.querySelector('[data-booking-drawer]');
 const visible=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&parseFloat(s.opacity)!==0&&r.width>0&&r.height>0};
 const n=performance.getEntriesByType('navigation')[0];
 return{url:location.origin+location.pathname,readyState:document.readyState,now:performance.now(),nav:n?{responseStart:n.responseStart,responseEnd:n.responseEnd,domInteractive:n.domInteractive,dclStart:n.domContentLoadedEventStart,dclEnd:n.domContentLoadedEventEnd,loadEnd:n.loadEventEnd}:null,
  hero:hero?{state:hero.dataset.newsState,busy:hero.getAttribute('aria-busy'),postNodes:hero.querySelectorAll('[data-news-id]').length,loaderVisible:[...hero.querySelectorAll('.hero-news-state [data-loading-indicator]')].some(visible)}:null,
  reviews:reviews?{ready:reviews.dataset.bentoReady,busy:reviews.getAttribute('aria-busy'),visibleCards:[...reviews.querySelectorAll('[data-review-card]')].filter(visible).map(e=>({id:e.id,textLength:e.querySelector('blockquote')?.textContent.trim().length??0})),loaderVisible:[...document.querySelectorAll('.review-layout-loader')].some(visible)}:null,
  booking:document.documentElement.dataset.bookingState??null,drawer:drawer?{open:drawer.open,hidden:drawer.hidden}:null,fonts:document.fonts.status};
}"""
INSTRUMENT = """(()=>{
 if(window.top!==window||!['soyuz.hair','www.soyuz.hair'].includes(location.hostname))return;
 let dclAt=null;document.addEventListener('DOMContentLoaded',()=>{dclAt=performance.now()},{once:true});
 for(const type of ['pointerdown','click'])document.addEventListener(type,e=>{
  if(!(e.target instanceof Element)||!e.target.closest('.header-book[data-booking]'))return;
  const n=performance.getEntriesByType('navigation')[0];
  window.__coldRecord({event:type,trusted:e.isTrusted,readyState:document.readyState,now:performance.now(),dclAt,navDclStart:n?.domContentLoadedEventStart??0});
 },true);
})()"""


class Probe:
    def __init__(self, page):
        self.page, self.started, self.phase = page, time.monotonic(), 'first_navigation'
        self.events, self.errors, self.responses, self.failures, self.provider_navigations = [], [], [], [], []
        self.builds = set()
        page.on('request', self.request)
        page.on('response', self.response)
        page.on('requestfailed', self.failed)
        page.on('pageerror', self.pageerror)
        page.on('console', self.console)
        page.on('domcontentloaded', lambda: self.events.append({'event': 'DCL', 'phase': self.phase, 'atMs': self.ms(), 'url': clean_url(page.url)}))
        page.on('framenavigated', lambda frame: self.events.append({'event': 'main-navigation', 'phase': self.phase, 'atMs': self.ms(), 'url': clean_url(frame.url)}) if frame == page.main_frame else None)

    def ms(self):
        return round((time.monotonic() - self.started) * 1000, 1)

    def request(self, request):
        match = re.search(r'/Soyuz/releases/([a-f0-9]{20})/', request.url)
        if match:
            self.builds.add(match.group(1))
        if category(request.url) == 'provider' and request.is_navigation_request() and request.frame == self.page.main_frame:
            self.provider_navigations.append({'url': clean_url(request.url), 'atMs': self.ms(), 'phase': self.phase})

    def response(self, response):
        kind = response.request.resource_type
        if kind in ['document', 'script', 'stylesheet'] or category(response.url) == 'feed' or response.status >= 400:
            self.responses.append({'url': clean_url(response.url), 'type': kind, 'category': category(response.url), 'status': response.status, 'atMs': self.ms(), 'phase': self.phase})

    def failed(self, request):
        self.failures.append({'url': clean_url(request.url), 'type': request.resource_type, 'category': category(request.url), 'failure': safe_text(request.failure), 'atMs': self.ms(), 'phase': self.phase})

    def pageerror(self, error):
        locations = re.findall(r'https?://[^\s\]\)<>"\']+', str(error.stack or ''))
        where = clean_url(locations[0]) if locations else clean_url(self.page.url)
        message = '[provider message omitted]' if category(where) == 'provider' else safe_text(error)
        self.errors.append({'kind': 'pageerror', 'message': message, 'source': where, 'category': category(where), 'atMs': self.ms(), 'phase': self.phase})

    def console(self, message):
        if message.type not in ['warning', 'error']:
            return
        where = clean_url(message.location.get('url', ''))
        text = '[provider message omitted]' if category(where) == 'provider' else safe_text(message.text)
        self.errors.append({'kind': 'console-' + message.type, 'message': text, 'source': where, 'category': category(where), 'atMs': self.ms(), 'phase': self.phase})

    def snapshot(self):
        return {'atMs': self.ms(), 'phase': self.phase, 'state': self.page.evaluate(STATE)}

    def record_press(self, source, event):
        # The page sends only a fixed scalar schema; no URL, DOM HTML, storage or cookie values.
        fields = ['event', 'trusted', 'readyState', 'now', 'dclAt', 'navDclStart']
        self.events.append({'event': 'booking-' + str(event['event']), 'phase': self.phase, 'atMs': self.ms(), **{k: event.get(k) for k in fields if k != 'event'}})

    def result(self):
        return {'events': self.events, 'errors': self.errors, 'responses': self.responses, 'requestFailures': self.failures,
                'providerMainNavigations': self.provider_navigations, 'observedReleaseBuilds': sorted(self.builds), 'durationMs': self.ms()}


def is_own_page(page):
    return urlsplit(page.url).hostname in ['soyuz.hair', 'www.soyuz.hair']


def close_drawer(page):
    drawer = page.locator('[data-booking-drawer]')
    if is_own_page(page) and drawer.count() and drawer.evaluate('e=>e.open'):
        page.locator('[data-booking-close]').click(timeout=5000)
        page.wait_for_function("!document.querySelector('[data-booking-drawer]').open", timeout=6000)


def normal_context(browser, index):
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page = context.new_page()
    page.set_default_timeout(10000)
    probe = Probe(page)
    context.expose_binding('__coldRecord', probe.record_press)
    context.add_init_script(INSTRUMENT)
    row = {'context': index, 'mode': 'normal_actual', 'requestInterception': False, 'snapshots': []}
    try:
        response = page.goto(ORIGIN, wait_until='commit', timeout=30000)
        row['mainStatus'] = response.status if response else None
        assert row['mainStatus'] == 200
        button = page.locator('.header-book[data-booking]')
        button.wait_for(state='visible', timeout=20000)
        row['snapshots'].append({'label': 'first-available-before-click', **probe.snapshot()})
        expected_href = button.get_attribute('href')
        row['nativeHref'] = clean_url(expected_href)
        row['nativeHrefHasQuery'] = bool(urlsplit(expected_href).query)
        assert urlsplit(expected_href).scheme == 'https' and category(expected_href) == 'provider'
        button.click(timeout=5000, no_wait_after=True)
        deadline = time.monotonic() + 2
        drawer_open = False
        while time.monotonic() < deadline:
            if probe.provider_navigations:
                break
            try:
                drawer_open = is_own_page(page) and page.locator('[data-booking-drawer]').evaluate('e=>e.open')
            except Exception:
                drawer_open = False
            if drawer_open:
                break
            page.wait_for_timeout(100)
        row['earlyClickOutcome'] = 'native-provider-navigation' if probe.provider_navigations else 'drawer-open' if drawer_open else 'no-action-observed'
        row['earlyClickAccepted'] = bool(probe.provider_navigations or drawer_open)
        presses = [e for e in probe.events if e['event'] == 'booking-click' and e['phase'] == 'first_navigation']
        row['actualTrustedClickState'] = presses[-1] if presses else None
        row['preDCLClickProven'] = bool(presses and presses[-1]['trusted'] and presses[-1]['readyState'] != 'complete' and presses[-1]['dclAt'] is None and presses[-1]['navDclStart'] == 0)
        if probe.provider_navigations:
            row['fallbackDestinationMatchesNativePath'] = probe.provider_navigations[0]['url'] == clean_url(expected_href)
            assert row['fallbackDestinationMatchesNativePath']
            probe.phase = 'second_navigation_after_native_fallback'
            page.goto(ORIGIN, wait_until='commit', timeout=30000)
            row['feedObservationNavigation'] = 'second_navigation_same_context_not_a_fresh_cold_load'
        else:
            close_drawer(page)
            row['feedObservationNavigation'] = 'original_fresh_context_navigation'
        row['readinessObservationStartMs'] = probe.ms()
        page.wait_for_load_state('domcontentloaded', timeout=25000)
        page.wait_for_function("document.querySelector('.hero-scene')?.dataset.newsState==='ready'&&document.querySelector('[data-review-bento]')?.dataset.bentoReady==='true'&&document.querySelector('[data-review-bento]')?.getAttribute('aria-busy')==='false'", timeout=25000)
        row['snapshots'].append({'label': 'feed-and-reviews-ready', **probe.snapshot()})
        page.screenshot(path=str(OUT / f'normal-{index}-top.png'))
        page.locator('#reviews').scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        snap = probe.snapshot()
        row['snapshots'].append({'label': 'reviews-in-view', **snap})
        assert snap['state']['reviews']['visibleCards'] and all(card['textLength'] for card in snap['state']['reviews']['visibleCards'])
        assert not snap['state']['reviews']['loaderVisible']
        page.screenshot(path=str(OUT / f'normal-{index}-reviews.png'))
        if index == 3:
            probe.phase = 'late_booking_after_feed_ready'
            row['lateBookingBefore'] = probe.snapshot()
            page.locator('.header-book[data-booking]').click(timeout=6000, no_wait_after=True)
            page.wait_for_function("document.querySelector('[data-booking-drawer]')?.open===true", timeout=8000)
            row['lateBookingOpen'] = probe.snapshot()
            frame = page.locator('[data-booking-frame]')
            row['lateBookingFrameUrl'] = clean_url(frame.get_attribute('src') or '')
            assert category(row['lateBookingFrameUrl']) == 'provider'
            close_drawer(page)
            row['lateBookingClosed'] = probe.snapshot()
            assert not row['lateBookingClosed']['state']['drawer']['open']
            row['lateBookingFocusReturned'] = page.locator('.header-book[data-booking]').evaluate('e=>e===document.activeElement')
            assert row['lateBookingFocusReturned']
        own_errors = [e for e in probe.errors if e['kind'] == 'pageerror' and e['category'] == 'site']
        bad_modules = [e for e in probe.responses if e['category'] == 'site' and e['type'] in ['script', 'stylesheet'] and e['status'] >= 400]
        row['intentionalNativeDepartureModuleAborts'] = [e for e in probe.failures if e['category'] == 'site' and e['type'] in ['script', 'stylesheet'] and 'ERR_ABORTED' in e['failure'] and row['earlyClickOutcome'] == 'native-provider-navigation' and e['atMs'] <= row['readinessObservationStartMs']]
        # A successful native departure may cancel an unfinished module from the page it leaves.
        # Keep those events in evidence; they are not failed delivery of the subsequent readiness observation.
        failed_modules = [e for e in probe.failures if e['category'] == 'site' and e['type'] in ['script', 'stylesheet'] and e not in row['intentionalNativeDepartureModuleAborts']]
        assert not own_errors and not bad_modules and not failed_modules
        assert args.expected_build in probe.builds
        assert row['earlyClickAccepted']
        row['pass'] = True
    except Exception:
        row['pass'] = False
        row['failure'] = safe_text(traceback.format_exc())
        if is_own_page(page):
            try:
                row['snapshots'].append({'label': 'failure', **probe.snapshot()})
                page.screenshot(path=str(OUT / f'normal-{index}-failure.png'))
            except Exception:
                pass
    finally:
        probe.phase = 'context_closure'
        context.close()
        row.update(probe.result())
        (OUT / f'normal-{index}.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'mode': row['mode'], 'context': index, 'pass': row['pass'], 'earlyOutcome': row.get('earlyClickOutcome'), 'preDCLProven': row.get('preDCLClickProven'), 'observationNavigation': row.get('feedObservationNavigation')}, ensure_ascii=False), flush=True)
    return row


def nojs_context(browser, index):
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, java_script_enabled=False)
    page = context.new_page()
    probe = Probe(page)
    row = {'context': index, 'mode': 'no_javascript_native_link', 'providerDocumentFixture': True, 'fixtureHits': []}
    try:
        response = page.goto(ORIGIN, wait_until='commit', timeout=30000)
        row['mainStatus'] = response.status if response else None
        assert row['mainStatus'] == 200
        button = page.locator('.header-book[data-booking]')
        button.wait_for(state='visible', timeout=20000)
        expected = button.get_attribute('href')
        row['beforeClick'] = {'atMs': probe.ms(), 'readyState': page.evaluate('document.readyState'), 'tag': button.evaluate('e=>e.tagName'), 'href': clean_url(expected), 'hasQuery': bool(urlsplit(expected).query)}
        assert row['beforeClick']['tag'] == 'A' and urlsplit(expected).scheme == 'https' and category(expected) == 'provider'

        def route_request(route):
            request = route.request
            if category(request.url) == 'provider':
                if request.is_navigation_request() and request.frame == page.main_frame:
                    row['fixtureHits'].append({'url': clean_url(request.url), 'navigation': True, 'matchesFullNativeHref': request.url == expected, 'atMs': probe.ms()})
                    route.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Read-only provider navigation fixture</title><p>Native link destination reached. No provider code or form.</p>')
                else:
                    route.abort()  # No provider code/resources run in the explicit no-JS destination fixture.
            else:
                route.continue_()

        # Only the destination provider document is replaced. The visited soyuz.hair HTML is real.
        context.route('**/*', route_request)
        row['clickStartedAtMs'] = probe.ms()
        with page.expect_navigation(wait_until='commit', timeout=12000):
            button.click(timeout=6000, no_wait_after=True)
        row['clickReturnedAtMs'] = probe.ms()
        row['destination'] = clean_url(page.url)
        assert category(page.url) == 'provider' and row['destination'] == clean_url(expected)
        assert len(row['fixtureHits']) == 1 and row['fixtureHits'][0]['matchesFullNativeHref']
        row['preDCLClickClaim'] = False
        row['preDCLNote'] = 'Readiness sampled before Playwright click; no injected trusted-event timestamp with JS disabled, so no pre-DCL claim.'
        row['pass'] = True
    except Exception:
        row['pass'] = False
        row['failure'] = safe_text(traceback.format_exc())
    finally:
        probe.phase = 'context_closure'
        context.close()
        row.update(probe.result())
        (OUT / f'nojs-{index}.json').write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'mode': row['mode'], 'context': index, 'pass': row['pass'], 'fixtureHits': len(row['fixtureHits'])}, ensure_ascii=False), flush=True)
    return row


before = product_hashes()
rows = []
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', args=['--mute-audio'])
        version = browser.version
        try:
            for index in range(1, 4):
                rows.append(normal_context(browser, index))
            for index in range(1, 4):
                rows.append(nojs_context(browser, index))
        finally:
            browser.close()
finally:
    after = product_hashes()
    summary = {'origin': ORIGIN, 'expectedBuild': args.expected_build, 'browser': locals().get('version'), 'engine': 'Chrome on Windows', 'freshContexts': len(rows), 'passed': sum(row['pass'] for row in rows), 'failed': sum(not row['pass'] for row in rows), 'sourceStart': before, 'sourceEnd': after, 'sourceUnchanged': before == after,
               'contexts': [{'context': row['context'], 'mode': row['mode'], 'pass': row['pass'], 'earlyOutcome': row.get('earlyClickOutcome'), 'preDCLProven': row.get('preDCLClickProven'), 'feedObservationNavigation': row.get('feedObservationNavigation')} for row in rows],
               'boundary': 'Real HTTPS, real soyuz.hair HTML. Three fresh normal contexts without interception; early native navigation may require an explicitly labelled second navigation for readiness observation. Three separate no-JS contexts click real native hrefs; destination provider document only is an explicit fixture. Browser process/OS network stack shared. No cookie/storage/header/body values retained, URLs omit query/fragment. No forms, real booking, purchase, physical-device or benchmark claim.', 'browsersClosed': True}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': summary['passed'], 'failed': summary['failed'], 'sourceUnchanged': summary['sourceUnchanged'], 'summary': str(OUT / 'summary.json')}, ensure_ascii=False), flush=True)
assert len(rows) == 6 and all(row['pass'] for row in rows) and before == after
