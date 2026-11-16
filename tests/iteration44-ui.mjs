import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try {
 for(const width of [320,360,390,540,600,601,768,960]){
  await b.viewport(width,900,true);await b.open(base);
  const result=await b.evaluate(`(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,heads:[...document.querySelectorAll('.section-title[data-headline]')].map(e=>{const m=e.querySelector('.headline-mobile'),t=e.querySelector('.headline-tablet'),s=getComputedStyle(m).display!=='none'?m:t;return{id:e.dataset.headline,text:s.innerText,lines:[...s.children].map(c=>({h:c.getBoundingClientRect().height,line:parseFloat(getComputedStyle(c).lineHeight)}))}})}))()`);
  assert.equal(result.overflow,false,`overflow ${width}`);
  if(width<=600)for(const h of result.heads){assert.ok(h.lines.length<=2&&h.lines.every(l=>l.h<=l.line+.5),`${width} ${h.id}: ${h.text}`);const words=h.text.trim().split(/\s+/).filter(word=>word!=='—');assert.ok(words.length>=2&&words.length<=4,`${h.id}: ${h.text}`);}
  else assert.match(result.heads.find(h=>h.id==='offers').text,/ТОВАРИЩУ/i);
  console.log(`PASS headline and layout ${width}`);
 }
 await b.viewport(390,900,true);await b.open(base);await b.center('#faq');
 await b.evaluate(`document.querySelector('#faq-price summary').click()`);assert.equal(await b.evaluate(`document.querySelector('#faq-price').open`),true);
 await b.evaluate(`document.querySelector('#faq-beard summary').click()`);assert.equal(await b.evaluate(`document.querySelector('#faq-price').open`),false);
 await b.center('#reviews');assert.equal(await b.evaluate(`document.querySelectorAll('.review-card').length`),3);
 assert.equal(await b.evaluate(`document.querySelectorAll('.review-card[data-review-example="true"] small').length`),3);
 assert.equal(await b.evaluate(`document.querySelector('.contact-map-link').href.startsWith('https://yandex.ru/maps/')`),true);
 await b.evaluate(`document.querySelector('[data-rail-controls="reviews-rail"] [data-rail-step="1"]').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('[data-rail-controls="reviews-rail"] output').textContent`),'02 / 03');
 await b.center('#reviews-rail');await b.swipe(await b.point('#reviews-rail',.8,.4),-140);await b.until(`document.querySelector('[data-rail-controls="reviews-rail"] output').textContent==='03 / 03'`);
 await b.evaluate(`document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();
 const story=await b.evaluate(`(()=>{const d=document.querySelector('#team-dialog-souz-sofya-shalaginova'),r=e=>e.getBoundingClientRect();return{open:d.open,quotes:d.querySelectorAll('blockquote').length,width:r(d.querySelector('.story-cover')).width,body:r(d.querySelector('.story-body')).width,book:d.querySelector('.team-dialog-actions button').textContent.trim(),head:r(d.querySelector('.story-dialog-head')).height,photo:r(d.querySelector('.story-cover img')).height}})()`);
 assert.ok(story.open&&story.quotes>10);assert.ok(Math.abs(story.width-story.body)<1);assert.match(story.book,/Софье/);assert.ok(story.head<2&&story.photo<900);
 assert.equal(await b.evaluate(`document.querySelector('.story-heading').children.length`),1,'article title must not have an overline');
 await b.evaluate(`document.querySelector('#team-dialog-souz-sofya-shalaginova [data-dismiss]').click()`);await b.settle();
 await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle();
 assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('.dock-shell')).backgroundColor`),'rgb(255, 252, 247)');
 const choice='.dock-content .choice-trigger';await b.center(choice);const p=await b.point(choice);await b.tap(p);assert.equal(await b.evaluate(`document.querySelector('.dock-content .choice-list').matches(':popover-open')`),true);
 await b.tap(p);assert.equal(await b.evaluate(`document.querySelector('.dock-content .choice-list').matches(':popover-open')`),false);
 assert.equal(await b.evaluate(`document.querySelectorAll('.choice-check').length`),0);assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);
 console.log('PASS faq, reviews, article, theme toggle');
}finally{await b.close()}
