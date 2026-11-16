"""Exercise the unified interview target and its dock consumer in real engines."""
import argparse
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--phase',type=int,default=61);phase=parser.parse_args().phase
spec=importlib.util.spec_from_file_location('regression',ROOT/'tests/device-regression.py')
regression=importlib.util.module_from_spec(spec);spec.loader.exec_module(regression)
server,url=regression.serve(ROOT/'dist');before=regression.digest(ROOT/'dist');source_before=regression.sources();rows=[]
out=ROOT/f'artifacts/iteration{phase}';out.mkdir(parents=True,exist_ok=True)
try:
 with sync_playwright() as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}))
   for width in [390,768,1440]:
    page=browser.new_page(viewport={'width':width,'height':900});errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url);page.evaluate('document.fonts.ready');page.locator('#masters').scroll_into_view_if_needed();page.wait_for_timeout(500)
    cards=page.locator('.team-card');assert cards.count()==6
    for i in range(cards.count()):
     card=cards.nth(i);portrait=card.locator('.team-portrait');label=card.locator('.team-discover')
     assert card.locator('button[data-team-open]').count()==1
     portrait.focus();page.wait_for_timeout(100);page.keyboard.press('Tab');assert card.locator('.team-book').evaluate('e=>e===document.activeElement')
     page.keyboard.press('Shift+Tab');assert portrait.evaluate('e=>e===document.activeElement')
     page.keyboard.press('Enter');dialog=page.locator('#'+portrait.get_attribute('aria-controls'));page.wait_for_timeout(300);assert dialog.get_attribute('open') is not None
     page.keyboard.press('Escape');page.wait_for_timeout(300);assert dialog.get_attribute('open') is None
     # The visible label is part of the same action and remains a usable pointer target.
     label.click();page.wait_for_timeout(300);assert dialog.get_attribute('open') is not None;page.keyboard.press('Escape');page.wait_for_timeout(300)
     if width<=960:
      portrait.focus();page.wait_for_timeout(250);dock=page.locator('[data-mobile-nav] button[aria-controls="'+portrait.get_attribute('aria-controls')+'"]')
      assert dock.count()==1;dock.click();page.wait_for_timeout(300);assert dialog.get_attribute('open') is not None;page.keyboard.press('Escape');page.wait_for_timeout(300)
    assert not errors,errors;rows.append({'engine':engine,'width':width,'masters':6,'keyboard':True,'labelClick':True,'dock':width<=960});page.close()
   browser.close()
finally:
 server.shutdown();server.server_close();after=regression.digest(ROOT/'dist')
 (out/'masters.json').write_text(json.dumps({'rows':rows,'buildHash':before,'unchanged':before==after,'sourcesUnchanged':source_before==regression.sources(),'published':False},indent=2),encoding='utf-8')
assert len(rows)==9 and before==after and source_before==regression.sources()
print('PASS 9 engine/viewport cases; 54 master keyboard/label cases and 36 dock cases')
