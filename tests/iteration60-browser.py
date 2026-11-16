"""Regressions for interrupted drags and hoverable hours/offer tips, without external actions."""
from pathlib import Path
import json
import os
from playwright.sync_api import sync_playwright

engine=os.environ.get('QA_ENGINE','chromium')
out=Path(os.environ.get('QA_ARTIFACT_ROOT','artifacts/iteration60'))/engine;out.mkdir(parents=True,exist_ok=True)
url=os.environ.get('QA_URL','http://127.0.0.1:4321/')
results=[]
with sync_playwright() as p:
    browser=getattr(p,engine).launch(**({'channel':'chrome'} if engine=='chromium' else {}))
    for fallback in [False,True]:
        context=browser.new_context(viewport={'width':1440,'height':1000})
        context.add_init_script("document.addEventListener('pointerdown',e=>window.__qaMouseId=e.pointerId,true)")
        if fallback:context.add_init_script('HTMLElement.prototype.showPopover=undefined;HTMLElement.prototype.hidePopover=undefined')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url);page.evaluate('document.fonts.ready');page.wait_for_timeout(550)
        button=page.locator('.header-hours button');panel=page.locator('#'+button.get_attribute('aria-describedby'))
        button.hover();page.wait_for_timeout(350);assert button.get_attribute('aria-expanded')=='true'
        bounds=panel.bounding_box();page.mouse.move(bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2,steps=12)
        page.wait_for_timeout(250);assert button.get_attribute('aria-expanded')=='true','hover panel must stay open'
        page.screenshot(path=str(out/f'hours-hover-{fallback}.png'))
        page.mouse.move(20,300,steps=10);page.wait_for_timeout(250);assert button.get_attribute('aria-expanded')=='false'
        button.click();assert button.get_attribute('aria-expanded')=='true';page.keyboard.press('Escape');assert button.get_attribute('aria-expanded')=='false'
        button.click();assert button.get_attribute('aria-expanded')=='true';button.click();assert button.get_attribute('aria-expanded')=='false'
        # A short visit must not leave a delayed tooltip behind.
        page.mouse.click(20,300);page.wait_for_timeout(550);button.hover();page.wait_for_timeout(30);page.mouse.move(20,300);page.wait_for_timeout(350)
        assert button.get_attribute('aria-expanded')=='false'
        results.append({'tips':'hover, leave, repeat click, Escape, cancelled hover','fallback':fallback})
        rail=page.locator('[data-of-rail]');section=page.locator('[data-offers]')
        rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(550)
        def held():
            bounds=rail.bounding_box();x=min(1300,bounds['x']+bounds['width']-70);y=max(150,min(700,bounds['y']+210))
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-100,y,steps=10)
            assert rail.evaluate("e=>e.classList.contains('is-dragging')")
            assert isinstance(page.evaluate('window.__qaMouseId'),int),'read the browser-assigned pointer ID'
            return x,y
        def settled():
            page.wait_for_timeout(500)
            assert not rail.evaluate("e=>e.classList.contains('is-dragging')")
            assert section.get_attribute('data-offers-moving')=='false'
        before=section.get_attribute('data-offer-index');x,y=held();page.evaluate("window.dispatchEvent(new Event('blur'))");settled()
        page.mouse.move(x-400,y,steps=10);page.mouse.up();settled();assert section.get_attribute('data-offer-index')==before
        x,y=held();rail.dispatch_event('pointermove',{'pointerId':page.evaluate('window.__qaMouseId'),'pointerType':'mouse','isPrimary':True,'buttons':0,'clientX':x-300,'clientY':y});settled();page.mouse.up();assert section.get_attribute('data-offer-index')==before
        x,y=held();page.set_viewport_size({'width':1200,'height':1000});settled();page.mouse.up();assert section.get_attribute('data-offer-index')==before
        page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(350)
        x,y=held();rail.dispatch_event('pointercancel',{'pointerId':page.evaluate('window.__qaMouseId')+100});assert rail.evaluate("e=>e.classList.contains('is-dragging')"),'another pointer must not cancel this gesture'
        rail.dispatch_event('pointercancel',{'pointerId':page.evaluate('window.__qaMouseId')});page.mouse.up();settled();assert section.get_attribute('data-offer-index')==before
        # A keyboard command while held owns the final choice; stale pointerup cannot advance again.
        x,y=held();rail.focus();page.keyboard.press('ArrowRight');chosen=section.get_attribute('data-offer-index');page.mouse.up();settled();assert section.get_attribute('data-offer-index')==chosen and chosen!=before
        # Both methods keep the approved outgoing card below the incoming card.
        page.locator('[data-of-next]').evaluate("e=>e.addEventListener('click',()=>document.querySelectorAll('[data-offer-id]').forEach(card=>card.getAnimations().forEach(a=>{a.pause();a.currentTime=96})),{once:true})")
        page.locator('[data-of-next]').click();page.wait_for_timeout(60)
        leaving=section.locator('[data-offer-leaving="true"]');active=section.locator('[data-offer-active="true"]')
        assert leaving.count() and int(leaving.first.evaluate('e=>getComputedStyle(e).zIndex'))<int(active.evaluate('e=>getComputedStyle(e).zIndex'))
        page.screenshot(path=str(out/f'offer-deal-{fallback}.png'));section.evaluate("e=>e.querySelectorAll('[data-offer-id]').forEach(card=>card.getAnimations().forEach(a=>a.play()))");page.wait_for_timeout(500)
        results.append({'drag':'blur, released button, resize, unrelated cancel, own cancel, keyboard interruption, stacking','fallback':fallback})
        # Long real offer conditions stay reachable in landscape with 200% text.
        page.set_viewport_size({'width':1000,'height':320});page.evaluate("location.hash='offer-premium'");page.wait_for_timeout(500)
        info=page.locator('[data-offer-active="true"] [data-info-tip] button');long_panel=page.locator('#'+info.get_attribute('aria-describedby'))
        long_panel.evaluate("e=>e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'");info.click();page.wait_for_timeout(200)
        bounds=long_panel.bounding_box();assert bounds['y']>=15 and bounds['y']+bounds['height']<=305,bounds
        assert long_panel.evaluate('e=>e.scrollHeight>e.clientHeight')
        assert long_panel.evaluate('e=>e.scrollWidth<=e.clientWidth+1'),'long words must stay inside the text area'
        # Pointer focus differs by engine; keyboard navigation starts from the trigger.
        info.focus();page.keyboard.press('ArrowDown');assert long_panel.evaluate('e=>document.activeElement===e')
        page.keyboard.press('End');page.wait_for_timeout(200);assert long_panel.evaluate('e=>e.scrollTop>0')
        assert info.get_attribute('aria-expanded')=='true';page.screenshot(path=str(out/f'long-tip-{fallback}.png'));page.keyboard.press('Escape')
        assert info.get_attribute('aria-expanded')=='false',info.evaluate("e=>({expanded:e.getAttribute('aria-expanded'),focus:document.activeElement?.outerHTML.slice(0,150),rootHover:e.parentElement.matches(':hover'),panelHover:document.getElementById(e.getAttribute('aria-describedby')).matches(':hover')})")
        results.append({'long-tip':'landscape, doubled text, keyboard scrolling, Escape','fallback':fallback})
        page.set_viewport_size({'width':1440,'height':1000});rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(500)
        info=page.locator('[data-offer-active="true"] [data-info-tip] button');info.click();page.wait_for_timeout(200)
        nested=page.locator('#'+info.get_attribute('aria-describedby'));bounds=nested.bounding_box();x=bounds['x']+50;y=bounds['y']+40
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y,steps=10)
        assert not rail.evaluate("e=>e.classList.contains('is-dragging')"),'reading/selecting text must not drag the carousel'
        page.mouse.up();page.keyboard.press('Escape');results.append({'nested-pointer':'tooltip text does not start a carousel drag','fallback':fallback})
        # Compact native rails must also stop when a mouse button was released outside the window.
        page.set_viewport_size({'width':768,'height':900});page.evaluate("location.hash='offer-coffee'");page.wait_for_timeout(500)
        rail.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");page.wait_for_timeout(500)
        bounds=rail.bounding_box();x=650;y=max(150,min(650,bounds['y']+210));page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-120,y,steps=12)
        assert rail.evaluate("e=>e.classList.contains('is-dragging')")
        rail.dispatch_event('pointermove',{'pointerId':page.evaluate('window.__qaMouseId'),'pointerType':'mouse','isPrimary':True,'buttons':0,'clientX':x-240,'clientY':y});page.mouse.up();page.wait_for_timeout(700)
        assert not rail.evaluate("e=>e.classList.contains('is-dragging')")
        assert rail.evaluate("e=>e.style.scrollSnapType!=='none'")
        results.append({'native-drag':'released button restores snap','fallback':fallback})
        assert not errors,errors;context.close()
    browser.close()
(out/'browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',engine,len(results),'interaction groups')
