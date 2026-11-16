"""Native rail keyboard visibility and delayed release after a cancelled real drag."""
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
try:
 with sync_playwright() as p:
  for engine in ['chromium','firefox','webkit']:
   browser=getattr(p,engine).launch(**({'channel':'chrome'}if engine=='chromium'else{}))
   page=browser.new_page(viewport={'width':390,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.evaluate('document.fonts.ready')
   for selector in ['.of-rail','.team-grid','.about-stack','.gifts-grid','#reviews-rail']:
    rail=page.locator(selector);rail.evaluate("e=>{e.scrollIntoView({block:'center',behavior:'instant'});e.scrollLeft=0}");page.wait_for_timeout(450)
    target=rail.locator('button:not([disabled]),a[href],[tabindex="0"]').filter(visible=True).first
    expected=set(rail.evaluate("e=>[...e.children].flatMap((card,index)=>[...card.querySelectorAll('button,a[href],[tabindex]')].some(c=>c.tabIndex>=0&&!c.disabled&&c.getClientRects().length&&!c.closest('[hidden],[inert],[aria-hidden=\"true\"]')&&getComputedStyle(c).visibility!=='hidden')?[index]:[])"))
    target.focus();seen=set()
    for step in range(36):
     state=rail.evaluate("e=>{const a=document.activeElement,c=[...e.children].find(c=>c.contains(a));if(!c)return null;const r=e.getBoundingClientRect(),b=a.getBoundingClientRect();return{index:[...e.children].indexOf(c),x:b.left-r.left,right:b.right-r.right,w:b.width}}")
     if state is None:break
     assert state['x']>=-1 and state['right']<=1,(engine,selector,state)
     seen.add(state['index']);page.keyboard.press('Tab');page.wait_for_timeout(35)
    assert seen==expected and seen,(engine,selector,seen,expected);rows.append({'engine':engine,'rail':selector,'keyboardCards':len(seen)})
   page.set_viewport_size({'width':1440,'height':1000});page.goto(url);page.wait_for_timeout(500)
   action=page.locator('[data-offer-active="true"] .of-action');action.scroll_into_view_if_needed();page.wait_for_timeout(500);r=action.bounding_box();x=r['x']+r['width']*.65;y=r['y']+r['height']/2
   page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-65,y,steps=10);page.set_viewport_size({'width':1438,'height':1000});page.wait_for_timeout(650);page.mouse.up();page.wait_for_timeout(350);assert page.locator('dialog[open]').count()==0
   action.click();page.wait_for_timeout(300);assert page.locator('dialog[open]').count()==1,'a fresh click must work';page.keyboard.press('Escape');page.wait_for_timeout(300)
   page.set_viewport_size({'width':768,'height':900});page.goto(url);page.wait_for_timeout(500);rail=page.locator('[data-of-rail]');rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(500);r=rail.bounding_box();x=650;y=max(150,min(650,r['y']+210))
   page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-100,y,steps=10);rail.focus();page.keyboard.press('ArrowRight');chosen=page.locator('[data-offers]').get_attribute('data-offer-index');page.mouse.move(x-120,y,steps=3);page.wait_for_timeout(500);page.mouse.up();page.wait_for_timeout(700)
   assert page.locator('[data-offers]').get_attribute('data-offer-index')==chosen
   assert not rail.evaluate("e=>e.classList.contains('is-dragging')");assert not errors,errors
   # Firefox omits pointerup outside the viewport. Its stale guard must not consume a new desktop click.
   page.goto(url);page.wait_for_timeout(500);rail=page.locator('[data-of-rail]');rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(500)
   r=rail.bounding_box();x=650;y=max(100,min(650,r['y']+210))
   page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-100,y,steps=8);page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(700)
   page.mouse.move(-100,-100);page.mouse.up();page.wait_for_timeout(700)
   page.locator('[data-offer-active="true"] .of-action').click();page.wait_for_timeout(300);assert page.locator('dialog[open]').count()==1,'a new primary press starts a fresh sequence after an unobserved release'
   page.keyboard.press('Escape');page.wait_for_timeout(300)
   rows.append({'engine':engine,'delayedCancelledRelease':True,'freshClick':True,'nativeKeyboardInterruption':True,'freshClickAfterOutsideRelease':True});page.close();browser.close()
finally:
 server.shutdown();server.server_close();after=regression.digest(ROOT/'dist')
 (ROOT/f'artifacts/iteration{phase}/interruptions.json').write_text(json.dumps({'rows':rows,'hash':before,'unchanged':before==after,'sourcesUnchanged':source_before==regression.sources(),'published':False},indent=2),encoding='utf-8')
assert len(rows)==18 and before==after and source_before==regression.sources()
print('PASS 15 native-rail keyboard cases and 3 delayed-release/keyboard-interruption cases')
