# Actual public Tilda acceptance — iteration 65, candidate C

Current follow-up: the host-background finding below was subsequently fixed in exporter candidateD and passed18/18 actual-public cases plus the three-engine common-header smoke. See `docs/HOST_CANVAS_65D.md` for RED, D native GREEN, actual-public GREEN and unchanged-client provenance. This file retains the original C observations; they are not rewritten as if C had passed that background boundary.

Tested 16 November 2026 against `https://stay-tan-habanero.tilda.ws/`, after the 13-page publication reported by the release owner. This is actual Tilda HTML, CSS, scripts and external providers; no request interception, synthetic provider, external-script abort or network bypass was used. Production source was not changed during this audit.

## Result

**One confirmed Tilda-specific defect remains:** the dark theme changes its tokens, headings and component surfaces, while the Tilda page canvas remains light. In Chromium, Firefox and WebKit, the actual dark computed values were:

| Owner | background-color | inherited `--surface` |
|---|---|---|
| `html[data-theme=dark]` | `rgb(24, 25, 28)` | `#18191c` |
| `body.t-body` | `rgb(255, 252, 247)` | `#18191c` |
| `#allrecords.t-records` | `rgb(255, 252, 247)` | `#18191c` |

The source assigns the page background to `:root`; Tilda supplies opaque backgrounds on both host wrappers. The current exporter `HOST_CSS` normalizes width/overflow but does not bind these wrapper backgrounds to the site theme. This is a host-boundary issue, not an incorrect theme state. It was reported to the release owner; no local CSS patch was injected and no production edit was made by this audit. Evidence: `tmp/planning/iteration65/publicC/diagnostic.json` and the actual dark PNGs below. Final public visual acceptance remains conditional on correcting and rechecking this boundary.

## Coverage and passing observations

The main smoke completed **18 combinations**: Chromium (installed Chrome), Firefox and WebKit × 390/961/1440 px × light/dark, plus one real booking/map/certificate branch per engine. Viewport heights were 900 px, or 1200 px at 1440. Both actual compact and desktop CSS modes were followed. WebKit at nominal 961 uses the compact mode because of its native gutter; its `matchMedia(max-width:960px)` and component mode agreed.

- A single shared header and footer were present, with no root/contact/footer horizontal overflow in these 18 combinations. Both personal contact cards and all three full legal-link labels were present.
- The common More/phone/hours menus had the same `#252525` material background, `20px` radius and an approximately `8.24px` gap below the capsule. Messenger glyphs were visible inline SVG paths. Actual screenshots were inspected directly.
- Manrope 400/500/600 and Molot loaded. Desktop heading red in light theme and yellow in dark theme matched the intended tokens. The compact video-Hero title intentionally stays cream in both themes.
- The 390 px initial load did not request the news JSON. Desktop requested the real GitHub feed with HTTP 200 (one cached Firefox refresh returned 304). The 10 visible post IDs were 1962,1958,1954,1948,1933,1925,1923,1921,1919,1914: none of the nine excluded IDs appeared.
- Actual responsive photos used the feed's 1086w/1280w WebP resources, rather than widget thumbnails. The initial 1086w photo was selected for a 760 CSS-pixel `sizes` slot; the rendered width reached 753 CSS px at DPR 1. Chromium, Firefox and WebKit loaded the real next-slide 1280w resource with HTTP 200.
- The outer Hero control moved the same selected post and counter. A focused fresh-desktop chronology in all three engines recorded 01/10 and post1962 at 0/100ms, then 02/10 and post1958 at400/1500ms. This reflects the existing decode-before-show boundary on a cold network, rather than a failed control.
- The actual About stack heading remained at its expected 104px sticky position during a real wheel step in all six desktop theme/engine cases.
- The actual Tilda favicon SVG was fetched separately and contained the original mark inside `<circle ... fill="#c42f2a">`.
- Certificate anchors retained the exact `https://o16013.yclients.ru/certificates` URL and `target=_blank`; real new tabs opened this destination in all three engines. No payment was initiated.
- Booking's desktop dock and compact overlay switched correctly. A settled real Firefox provider page displayed СОЮЗ, ул.Владимирская132 and the service catalogue. No service, appointment time or submission was selected. This proves a rendered provider catalogue in that session, not an end-to-end booking.
- Real Yandex map tiles, controls and the СОЮЗ business balloon rendered; no CAPTCHA interaction was attempted.

## Network/provider boundaries

The workspace network and its VPN configuration were left unchanged. The main `https://soyuz.hair` TLS limitation is tracked separately by the release owner; the current browser evidence concerns the technical Tilda hostname.

The first real Chromium provider run had several Yclients API HTTP403 responses; the first WebKit provider document itself returned403. Firefox rendered the real catalogue after its SPA settled. The site iframe `load` event proves a document loaded and cannot certify that a cross-origin application is usable. Initial screenshots taken immediately after that event included a blank provider canvas; the later Firefox screenshot shows the catalogue. A400ms Firefox screenshot also shows this external blank interval; this audit does not claim the site's loader covers a provider SPA's complete internal initialization. The common loader animation and placement were separately verified in the exact C native fixture; they are not newly claimed from this public400ms frame.

WebKit reported20 cross-origin exceptions whose stacks belonged to Yandex advertising code (`yastatic.net` inside the map frame). No exception stack was attributed to `/Soyuz/releases/`. A third-party advertising request returned400 in Chromium. Request cancellation at context close and short feedback WAV cancellation are retained in the raw report; they are not classified as failed static-asset delivery. No non-cancelled site asset HTTP4xx/5xx appeared in this smoke.

## Harness corrections, preserved evidence

`result.json` preserves all16 original boolean failures:8 incorrectly expected red/yellow on the intended cream compact title,6 checked cold-photo selection after an unsuitable fixed100ms, and2 classified cancelled feedback WAV playback as asset failure. These original records were not deleted or rewritten. `diagnostic.json` adds the cause-specific observations and identifies the real host-background defect. A first focused helper timed out before its initialization precondition and was kept as `focused.py`/`focused.log`; the diagnostic explicitly awaited the shared runtime owner before observing the fresh desktop state. It then loaded the real feed in all three engines without a retry button or production change.

## Evidence

All artifacts are under `tmp/planning/iteration65/publicC/`:

- `smoke.py`, `run.log`, `result.json`: the18-combination actual-public smoke and raw transport/runtime ledger.
- `diagnostic.py`, `diagnostic.log`, `diagnostic.json`: fresh-desktop Hero chronology, three-engine computed theme boundary and settled real Firefox provider.
- `chromium-light-1440-popup-more.png`, `firefox-dark-1440-popup-phone.png`, `webkit-dark-1440-popup-hours.png`: actual common menu surfaces, personally inspected.
- `{engine}-{theme}-1440-footer.png` and `...contacts.png`: actual footer/contact captures, representative frames personally inspected.
- `firefox-provider-settled.png`: real rendered Yclients catalogue, personally inspected.
- `webkit-provider.png`: provider403 boundary, personally inspected.
- `{engine}-real-map.png`: real map; WebKit's rendered business balloon personally inspected.
- `actual-favicon.svg`: fetched actual red-circle favicon.

All Playwright browser instances created by this audit were closed, and **BROWSER-FREE** was sent to the release owner before account-UI work resumed. Physical phones and physical Safari were not tested, per the task's established scope. No production code, Tilda setting, network/VPN setting, booking or payment was changed by this audit.
