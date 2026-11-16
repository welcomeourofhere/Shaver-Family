"""Actual site controls gate vendor requests; third-party scripts are not executed in QA."""
import json,mimetypes
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/planning/iteration64';OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome');context=browser.new_context(viewport={'width':1440,'height':900});vendors=[]
 def own(route):
  from urllib.parse import urlsplit
  path=urlsplit(route.request.url).path;file=ROOT/'dist'/('index.html'if path=='/'else path.lstrip('/'))
  if file.is_dir():file=file/'index.html'
  if file.is_file():route.fulfill(path=str(file),content_type='application/javascript'if file.suffix=='.js'else mimetypes.guess_type(file.name)[0]or'application/octet-stream')
  else:route.abort()
 context.route('https://soyuz.hair/**',own)
 context.route('https://*.yclients.ru/**',lambda route:route.abort())
 def vendor(route):vendors.append(route.request.url);route.fulfill(content_type='application/javascript',body='/* Third-party vendor intentionally not executed by QA. */')
 context.route('https://www.googletagmanager.com/**',vendor);context.route('https://mc.yandex.ru/**',vendor)
 page=context.new_page();page.goto('https://soyuz.hair/',wait_until='domcontentloaded');page.wait_for_timeout(700)
 assert page.locator('[data-analytics-prompt]').is_visible(),'first public visit must offer a choice before analytics'
 assert vendors==[],vendors
 page.locator('[data-analytics-choice=denied]').click();page.wait_for_timeout(300);assert vendors==[]
 page.reload(wait_until='domcontentloaded');page.wait_for_timeout(350);assert not page.locator('[data-analytics-prompt]').is_visible();assert vendors==[]
 page.locator('[data-analytics-settings]').last.click();page.locator('[data-analytics-choice=granted]').click();page.wait_for_timeout(500)
 assert sum('googletagmanager.com/gtag/js?id=G-TF121LKSEQ'in url for url in vendors)==1,vendors
 assert sum('mc.yandex.ru/metrika/tag.js'in url for url in vendors)==1,vendors
 page.locator('.header-book').click();page.wait_for_timeout(350)
 commands=page.evaluate("()=>dataLayer.map(row=>Array.from(row))")
 assert any(row[0:2]==['event','booking_open']for row in commands),commands
 for row in commands:
  if row and row[0]=='event':assert all(key not in row[2]for key in ['phone','email','url','value'])
 page.keyboard.press('Escape');page.locator('[data-analytics-settings]').last.click();page.locator('[data-analytics-choice=denied]').click();page.wait_for_timeout(200)
 before=page.evaluate("()=>dataLayer.filter(row=>row[0]==='event').length")
 page.locator('.header-book').click();page.wait_for_timeout(350)
 after=page.evaluate("()=>dataLayer.filter(row=>row[0]==='event').length")
 assert before==after,'events continued after analytics refusal'
 queued=page.evaluate("()=>ym.a?.map(row=>Array.from(row))||[]")
 assert not any(row[1]in ['init','reachGoal']for row in queued),'an unloaded counter retained commands after withdrawal'
 context.close();browser.close()
(OUT/'analytics.json').write_text(json.dumps({'vendorScriptsRequestedOnlyAfterConsent':True,'vendorScriptsExecuted':False,'refusalPersisted':True,'revocationStopsCustomEvents':True,'bookingSubmitted':False,'purchaseSubmitted':False},indent=2),encoding='utf-8')
print('PASS analytics choice, request gate, persistence, safe event and withdrawal; vendors stubbed')
