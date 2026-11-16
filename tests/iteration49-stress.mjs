import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
const report=[];
const click=async s=>{await b.center(s);await b.tap(await b.point(s));};
async function sample(name,run){const detail=await run();report.push({name,...detail});writeFileSync('tmp/planning/iteration49-stress.json',JSON.stringify({report,published:false},null,2));console.log('PASS '+name)}
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
 for(const width of [320,390,768,1440])await sample(`bento packs and reflows full reviews without overlaps ${width}`,async()=>{
  await b.viewport(width,1000,true);await b.open(base);await b.center('#reviews');
  const read=()=>b.evaluate(`(()=>{const rail=document.querySelector('#reviews-rail'),cards=[...rail.children].map(e=>{const r=e.getBoundingClientRect();return{id:e.id||e.querySelector('h3').textContent,x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}});return{cards,height:rail.offsetHeight,overflow:document.documentElement.scrollWidth>innerWidth+1}})()`);
  const first=await read();assert.equal(first.overflow,false);assert.equal(first.cards.length,10);await b.pause(700);assert.equal((await read()).height,first.height);
  const nonoverlap=state=>{for(const [i,a]of state.cards.entries())for(const c of state.cards.slice(i+1))assert.ok(a.right<=c.x+1||c.right<=a.x+1||a.bottom<=c.y+1||c.bottom<=a.y+1,JSON.stringify({width,a,c}));};
  nonoverlap(first);
  if(width>1100)assert.ok(new Set(first.cards.map(c=>c.w)).size>=2);
  await b.evaluate(`document.querySelector('#review-03 details').open=true`);await b.pause(250);const expanded=await read();nonoverlap(expanded);assert.equal(await b.evaluate(`document.querySelectorAll('#review-03 blockquote p').length`),7);
  await b.evaluate(`document.querySelector('#review-03 details').open=false`);await b.pause(250);const closed=await read();assert.equal(closed.height,first.height);
  await click('.review-platform-red button');assert.equal(await b.evaluate(`document.querySelector('#review-dialog').open`),true);await b.evaluate(`document.querySelector('#review-dialog [data-dismiss]').click()`);await b.settle();
  return {height:first.height,widths:first.cards.map(c=>Math.round(c.w))};
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
 await sample('local review MP4 plays with audio and can be sought and paused',async()=>{
  await b.viewport(390,900,true);await b.open(base);await click('#review-07 [data-review-video-play]');await b.until(`document.querySelector('#review-07 video')?.readyState>=2`);
  await b.until(`document.querySelector('#review-07 video').currentTime>.15`);
  const state=await b.evaluate(`(()=>{const v=document.querySelector('#review-07 video');v.pause();v.currentTime=4;return{source:v.currentSrc,width:v.videoWidth,height:v.videoHeight,duration:v.duration,muted:v.muted,controls:v.controls,audio:v.webkitAudioDecodedByteCount,paused:v.paused,error:v.error?.code}})()`);
  assert.match(state.source,/\/media\/reviews\/review-07-video\.mp4$/);assert.equal(state.width,720);assert.equal(state.height,1280);assert.ok(state.duration>8&&state.duration<9);assert.equal(state.muted,false);assert.equal(state.controls,true);assert.equal(state.paused,true);assert.equal(state.error,undefined);assert.ok(state.audio>0);return state;
 });
 await sample('video failure keeps an explicit retry and original link',async()=>{
  await b.viewport(390,900,true);await b.open(base);await b.evaluate(`document.querySelector('[data-review-video-play]').dataset.videoSrc='/missing-review-video.mp4'`);await click('[data-review-video-play]');await b.until(`!document.querySelector('.review-video-error').hidden`);assert.equal(await b.evaluate(`document.querySelector('[data-review-video-play]').hidden`),false);assert.match(await b.evaluate(`document.querySelector('.review-video-fallback').href`),/vk\.ru/);return {};
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
