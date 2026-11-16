import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4325/',report=[];
async function sample(name,run){const detail=await run();report.push({name,...detail});console.log('PASS '+name);}
try{
 await b.viewport(1440,1000,true);await b.send('Page.navigate',{url:new URL('previews/review-extras/',base).href});await b.until(`document.readyState==='complete'&&document.querySelectorAll('.preview-grid').length===3`);await b.settle();
 await sample('twelve actual components show all three extra types and all four colours',async()=>{
  const cards=await b.evaluate(`[...document.querySelectorAll('[data-review-extra]')].map(c=>({id:c.id,tone:c.dataset.reviewTone,w:c.offsetWidth,h:c.offsetHeight}))`);assert.equal(cards.length,12);assert.equal(new Set(cards.map(c=>c.id)).size,12);assert.deepEqual([...new Set(cards.map(c=>c.tone))].sort(),['blue','ink','red','yellow']);return {cards};
 });
 for(let i=0;i<6;i++)await sample('all twelve components use preset '+i,async()=>{
  const chosen=await b.evaluate(`(()=>{const b=document.querySelector('[data-size="${i}"]');b.click();return{w:Number(b.dataset.width),h:Number(b.dataset.height),format:b.dataset.format}})()`);await b.settle();
  const cards=await b.evaluate(`[...document.querySelectorAll('[data-review-extra]')].map(c=>({w:c.offsetWidth,h:c.offsetHeight,font:getComputedStyle(c.querySelector('h3')).fontSize,overflow:c.querySelector('.btn').scrollWidth>c.querySelector('.btn').clientWidth+1}))`);assert.ok(cards.every(c=>c.w===chosen.w&&c.h===chosen.h&&!c.overflow));assert.ok(cards.every(c=>c.font===(chosen.format==='phone'?'40px':'28px')));return {chosen};
 });
 await sample('manual width and height accept keyboard adjustment',async()=>{
  await b.evaluate(`document.querySelector('[data-preview-width]').focus()`);await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowRight',windowsVirtualKeyCode:39});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowRight',windowsVirtualKeyCode:39});await b.settle();assert.equal(await b.evaluate(`document.querySelector('[data-review-extra]').offsetWidth`),401);
  await b.evaluate(`document.querySelector('[data-preview-height]').focus()`);await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowLeft',windowsVirtualKeyCode:37});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowLeft',windowsVirtualKeyCode:37});await b.settle();assert.equal(await b.evaluate(`document.querySelector('[data-review-extra]').offsetHeight`),599);return {};
 });
 for(const width of [390,1440])await sample('preview stays contained at viewport '+width+' and 200 percent text',async()=>{
  await b.viewport(width,1000,true);await b.evaluate(`document.querySelector('[data-size="1"]').click()`);await b.settle();
  await b.evaluate(`(()=>{const es=[...document.querySelectorAll('.review-extra h3,.review-extra p,.review-extra .btn')],sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=2*sizes[i]+'px')})()`);await b.pause(100);
  const bad=await b.evaluate(`[...document.querySelectorAll('.review-extra .btn')].filter(c=>c.scrollWidth>c.clientWidth+1).map(c=>c.textContent)`);assert.deepEqual(bad,[]);assert.equal(await b.evaluate(`document.documentElement.scrollWidth>innerWidth+1`),false);
  await b.evaluate(`document.querySelectorAll('.review-extra h3,.review-extra p,.review-extra .btn').forEach(e=>e.style.removeProperty('font-size'))`);return {};
 });
 await sample('coffee preview uses the shared live dialog; platform destinations are retained',async()=>{
  await b.evaluate(`document.querySelector('#reviews-coffee-red button').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('#review-dialog').open`),true);
  const links=await b.evaluate(`[...document.querySelectorAll('#review-dialog a')].map(a=>a.href)`);assert.ok(links.some(url=>url.includes('yandex.ru'))&&links.some(url=>url.includes('vk.')));
  await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',windowsVirtualKeyCode:27});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',windowsVirtualKeyCode:27});await b.settle();assert.equal(await b.evaluate(`document.querySelector('#review-dialog').open`),false);assert.deepEqual(await b.evaluate(`__touchErrors`),[]);return {links};
 });
}finally{writeFileSync('tmp/planning/iteration50-preview.json',JSON.stringify({report,published:false},null,2));await b.close();}
