import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try {
 for(const width of [320,390,768,960]){
  await b.viewport(width,844,true);await b.open(base);await b.center('.sd-section');
  await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='services'`);
  await b.evaluate(`document.querySelector('[data-action="service-booking"]').focus()`);
  assert.equal(await b.evaluate('document.activeElement.dataset.action'),'service-booking');
  await b.center('.of-rail');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='offers'`);await b.settle();
  assert.equal(await b.evaluate(`document.activeElement===document.querySelector('[data-open-menu]')`),true,'focus transferred to an unrelated action');
  await b.evaluate(`document.querySelector('[data-action="offer-next"]').focus()`);
  await b.evaluate(`document.querySelector('[data-of-next]').click()`);await b.settle();
  assert.equal(await b.evaluate('document.activeElement.dataset.action'),'offer-next','focus should remain on the same action');
  assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);console.log(`PASS dock focus ${width}`);
 }
}finally{await b.close()}
