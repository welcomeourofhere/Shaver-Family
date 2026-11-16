import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
const report=[];
const click=async s=>{await b.center(s);await b.tap(await b.point(s));};
async function sample(name,run){const detail=await run();report.push({name,...detail});writeFileSync('tmp/planning/iteration50-stress.json',JSON.stringify({report,published:false},null,2));console.log('PASS '+name)}
try{
 await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 for(const width of [320,390,600,768,960])await sample(`service height remains intrinsic through repeated interactions ${width}`,async()=>{
  await b.viewport(width,900);await b.open(base);await b.center('.sd-stack');
  const reset=()=>b.evaluate(`(()=>{document.querySelectorAll('.sd-card').forEach(panel=>panel.querySelector('.sd-service').open=true);document.querySelectorAll('[data-sd-tab]')[0].click()})()`);
  await reset();await b.pause(500);await b.settle();
  const start=await b.evaluate(`document.querySelector('.sd-stack').offsetHeight`);
  for(let cycle=0;cycle<3;cycle++){
   for(let category=0;category<5;category++){
    await b.evaluate(`document.querySelectorAll('[data-sd-tab]')[${category}].click()`);
    await b.pause(60);
    await b.evaluate(`(()=>{const p=document.querySelector('.sd-card[aria-hidden="false"]');p.querySelectorAll('.sd-service').forEach(row=>row.open=true)})()`);
   }
   await reset();await b.pause(600);await b.settle();
   const height=await b.evaluate(`document.querySelector('.sd-stack').offsetHeight`);assert.ok(Math.abs(height-start)<=2,JSON.stringify({width,start,height,cycle}));
  }
  await b.center('.sd-tabs');await b.swipe(await b.point('.sd-stack',.75,.15),-160);await b.swipe(await b.point('.sd-stack',.65,.15),60,0,true);
  await reset();await b.pause(600);
  const end=await b.evaluate(`document.querySelector('.sd-stack').offsetHeight`);assert.ok(Math.abs(end-start)<=2,JSON.stringify({start,end}));
  assert.deepEqual(await b.evaluate(`__touchErrors`),[]);return {start,end};
 });
 for(const width of [320,390,768])await sample(`contact details survive 200 percent text ${width}`,async()=>{
  await b.viewport(width,1000,true);await b.open(base);await b.evaluate(`(()=>{for(const e of document.querySelectorAll('.contact-person h3,.contact-person p,.contact-person a'))e.style.fontSize=2*parseFloat(getComputedStyle(e).fontSize)+'px'})()`);await b.center('.contact-person');
  const details=await b.evaluate(`(()=>{const card=document.querySelector('.contact-person').getBoundingClientRect();return[...document.querySelectorAll('.contact-person a')].map(e=>{const r=e.getBoundingClientRect();return{label:e.textContent,width:e.clientWidth,scroll:e.scrollWidth,left:r.left,right:r.right,cardLeft:card.left,cardRight:card.right}})})()`);
  assert.ok(details.every(e=>e.scroll<=e.width+1&&e.left>=e.cardLeft&&e.right<=e.cardRight),JSON.stringify(details));return {details};
 });
 await sample('desktop hero edge fades after the pointer leaves its entire block',async()=>{
  await b.viewport(1440,1000);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(base);await b.center('.hero-scene');
  const r=await b.evaluate(`(()=>{const r=document.querySelector('.hero-slide[data-hero-active="true"] .hero-edge-prev').getBoundingClientRect();return{x:r.left+2,y:r.top+r.height*.3}})()`);
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...r});await b.pause(220);
  const read=()=>b.evaluate(`Number(getComputedStyle(document.querySelector('.hero-slide[data-hero-active="true"] .hero-edge-prev'),'::before').opacity)`);
  const before=await read();await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:2,y:r.y});await b.pause(35);const during=await read();await b.pause(220);const after=await read();
  assert.ok(before>.8&&during>0&&during<before&&after===0,JSON.stringify({before,during,after}));return {before,during,after};
 });
 await sample('footer and interview retain only the requested actions',async()=>{
  await b.viewport(390,900,true);await b.open(base);
  assert.equal(await b.evaluate(`!!document.querySelector('.footer-settings,.footer-top,.footer-booking svg')`),false);
  assert.equal(await b.evaluate(`[...document.querySelectorAll('.team-discover')].every(e=>e.textContent.trim()==='Интервью'&&!e.querySelector('svg'))`),true);
  assert.equal(await b.evaluate(`!!document.querySelector('a[href^="/masters/"]')`),false);
  await b.evaluate(`document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('dialog[open]').textContent.includes('Открыть статью')`),false);return {};
 });
}finally{await b.close()}
console.log(`${report.length} stress scenarios passed`);
