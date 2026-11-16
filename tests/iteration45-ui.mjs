import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try{
 for(const width of [320,390,768]){
  for(const [rail,card,controls] of [['.of-rail','.of-card','offers-rail'],['.team-grid','.team-card','masters-rail'],['.about-stack','.about-layer','about-rail'],['.gifts-grid','.gift','gifts-rail']]){
   await b.viewport(width,844,true);await b.open(base);await b.center(rail);
   const point=await b.evaluate(`(()=>{const rail=document.querySelector('${rail}'),r=rail.getBoundingClientRect(),c=rail.querySelectorAll('${card}')[1].getBoundingClientRect(),left=Math.max(r.left,c.left),right=Math.min(r.right,c.right);return{x:(left+right)/2,y:Math.max(60,Math.min(innerHeight-120,c.top+Math.min(60,c.height/3))),visible:right-left}})()`);
   assert.ok(point.visible>3,`${width} ${rail}: no visible neighbour`);await b.tap({x:point.x,y:point.y});
   await b.until(`document.querySelector('[data-rail-controls="${controls}"] output').textContent.startsWith('02')`);
   assert.equal(await b.evaluate('!!document.querySelector("dialog:modal")'),false,`${rail} activated a control while selecting the card`);
   console.log(`PASS neighbour ${width} ${controls}`);
  }
  await b.viewport(width,844,true);await b.open(base);await b.center('.certificate-scene');
  const certificate=await b.evaluate(`(()=>{const e=document.querySelector('.certificate-scene'),r=e.getBoundingClientRect(),cards=[...e.querySelectorAll('.certificate-art')].map(x=>{const p=x.getBoundingClientRect();return{left:p.left,right:p.right}});return{overflow:getComputedStyle(e).overflowX,cards,width:innerWidth}})()`);
  assert.equal(certificate.overflow,'visible');assert.ok(certificate.cards.every(card=>card.left>=-1&&card.right<=width+1),JSON.stringify(certificate));
  for(let i=0;i<4;i++){
   await b.evaluate(`document.querySelectorAll('[data-certificate]')[${i}].click()`);await b.settle();
   const bounds=await b.evaluate(`(()=>{const r=document.querySelectorAll('.certificate-art')[${i}].getBoundingClientRect();return {left:r.left,right:r.right}})()`);
   assert.ok(bounds.left>=-1&&bounds.right<=width+1,JSON.stringify({width,i,bounds}));
  }
  console.log(`PASS certificate bounds ${width}`);
 }
 await b.viewport(390,844,true);await b.open(base);
 const gift='.gifts-grid .gift-visual[data-has-photo="true"]';
 await b.center(gift);await b.tap(await b.point(gift));
 if(await b.evaluate(`document.querySelector('${gift}').getAttribute('aria-pressed')`)!=='true')await b.tap(await b.point(gift));
 assert.equal(await b.evaluate(`document.querySelector('${gift}').getAttribute('aria-pressed')`),'true','A selected gift must activate on the second tap at the latest');
 await b.open(base);
 assert.equal(await b.evaluate(`document.querySelectorAll('.of-info,.section-info').length`),0);
 for(const [selector,expected] of [['#offer-first-visit .of-note .info-trigger','не суммируются'],['#offer-father-son .of-note .info-trigger','от 4 до 18 лет']]){
  await b.center(selector);await b.tap(await b.point(selector));
  const state=await b.evaluate(`(()=>{const button=document.querySelector('${selector}'),panel=document.getElementById(button.getAttribute('aria-describedby')),r=panel.getBoundingClientRect();return{open:panel.matches(':popover-open'),text:panel.textContent,left:r.left,right:r.right,top:r.top,bottom:r.bottom}})()`);
  assert.ok(state.open&&state.text.replace(/\s+/g,' ').includes(expected)&&state.left>=0&&state.right<=390&&state.top>=0&&state.bottom<=844,JSON.stringify(state));
  await b.tap(await b.point(selector));assert.equal(await b.evaluate(`document.getElementById(document.querySelector('${selector}').getAttribute('aria-describedby')).matches(':popover-open')`),false);
 }
 await b.center('#faq');await b.evaluate(`document.querySelector('#faq-price summary').click()`);
 const faq=await b.evaluate(`(()=>{const e=document.querySelector('#faq-price summary'),p=document.querySelector('#faq-price .faq-answer');return{weight:getComputedStyle(e).fontWeight,text:p.textContent,unresolved:p.textContent.includes('{')}})()`);
 assert.equal(faq.weight,'600');assert.ok(faq.text.includes('онлайн-записи')&&!faq.unresolved);
 assert.equal(await b.evaluate(`!!document.querySelector('.reviews-intro')`),false);
 await b.center('#reviews');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='reviews'`);await b.evaluate(`document.querySelector('[data-action="review-write"]').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('#review-dialog').open`),true);
 const scroll=await b.evaluate(`getComputedStyle(document.querySelector('#review-dialog .surface-content'),'::-webkit-scrollbar-button').display`);assert.equal(scroll,'none');
 assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);console.log('PASS tooltips, FAQ, review action and scrollbar');
}finally{await b.close()}
