import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),report={cases:[],failures:[],published:false};
const base=process.env.QA_URL||'http://127.0.0.1:4321/';
async function check(name,run){if(process.env.QA_MOTION_ONLY&&!name.includes(process.env.QA_MOTION_ONLY))return;try{const row=await run();report.cases.push({name,...row});console.log('PASS '+name)}catch(error){report.failures.push({name,error:error.message});console.log('FAIL '+name+': '+error.message)}}
// Sample elapsed time rather than frame count: the browser can run at 60 or 120 Hz.
async function sample(expression,duration=850){return b.evaluate(`(async()=>{const rows=[],end=performance.now()+${duration};do{rows.push(${expression});await new Promise(r=>requestAnimationFrame(r))}while(performance.now()<end);return rows})()`)}
const pose=selector=>`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),s=getComputedStyle(e);return{x:new DOMMatrix(s.transform).m41,opacity:Number(s.opacity),visible:s.visibility,overflow:document.documentElement.scrollWidth>innerWidth+1}})()`;
const dockPose=`(()=>{const e=document.querySelector('[data-mobile-nav]'),s=e.querySelector('.dock-shell'),r=s.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,opacity:Number(getComputedStyle(s).opacity),suppressed:e.dataset.suppressed,expanded:e.dataset.expanded,count:e.dataset.actionCount}})()`;
async function point(selector){await b.center(selector);return b.point(selector,.78,.35);}
async function start(p,touch=true){if(touch)await b.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...p,id:1}]});else{await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});}}
async function move(p,dx,dy=0,touch=true,steps=12){for(let i=1;i<=steps;i++){const q={x:p.x+dx*i/steps,y:p.y+dy*i/steps};if(touch)await b.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...q,id:1}]});else await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...q,button:'left',buttons:1});await b.pause(16);}}
async function end(p,dx,touch=true,cancel=false){if(touch)await b.send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]});else await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x+dx,y:p.y,button:'left',buttons:0,clickCount:1});}
async function clickRaw(selector){const p=await b.point(selector);await start(p,false);await end(p,0,false);}
try{
 for(const width of [320,390,768]){
  await b.viewport(width,844,false);await b.open(base);
  for(const direction of [-1,1])await check(`stack ${width} throw ${direction}`,async()=>{
   const active=await b.evaluate(`document.querySelector('.sd-card[aria-hidden=false]').id`),next=await b.evaluate(`document.querySelector('.sd-card[style*="--card-level:1"],.sd-card[style*="--card-level: 1"]').id`);
   const p=await point('.sd-stack'),dx=direction*Math.min(140,width*.4);await start(p);await move(p,dx);
   const middle=await b.evaluate(pose('#'+active));assert.ok(Math.abs(middle.x)>60,'card did not follow touch');
   await end(p,dx);const frames=await sample(pose('#'+active));assert.ok(Math.abs(frames[0].x-middle.x)<50,'release teleported');
   assert.ok(frames.some(row=>Math.sign(row.x)===direction&&Math.abs(row.x)>Math.abs(dx)+20),'card did not leave in swipe direction');
   assert.ok(frames.every(row=>!row.overflow),'swipe expanded document');
   if(width<=600)assert.equal(await b.evaluate(`document.querySelector('.sd-card[aria-hidden=false]').id`),next,'did not reveal the card under the front');
   assert.equal(await b.evaluate(`!!document.querySelector('dialog:modal')`),false);return{active,next,middle,frames};
  });
  await check(`stack ${width} cancelled return`,async()=>{
   const active=await b.evaluate(`document.querySelector('.sd-card[aria-hidden=false]').id`),p=await point('.sd-stack');await start(p);await move(p,-110);const middle=await b.evaluate(pose('#'+active));await end(p,-110,true,true);
   const frames=await sample(pose('#'+active));assert.ok(Math.abs(frames[0].x-middle.x)<50);assert.ok(Math.abs(frames.at(-1).x)<.5);assert.equal(await b.evaluate(`document.querySelector('.sd-card[aria-hidden=false]').id`),active);return{middle,frames};
  });
  await check(`offers ${width} native drag and magnet`,async()=>{
   const p=await point('.of-rail'),dx=-Math.min(140,width*.4),before=await b.evaluate(`document.querySelector('.of-rail').scrollLeft`);await start(p);await move(p,dx);const middle=await b.evaluate(`document.querySelector('.of-rail').scrollLeft`);assert.ok(middle>before+50);await end(p,dx);
   const frames=await sample(`document.querySelector('.of-rail').scrollLeft`,1200);assert.ok(Math.abs(frames[0]-middle)<80,'release jumped');
   const aligned=await b.evaluate(`(()=>{const e=document.querySelector('.of-rail'),r=e.getBoundingClientRect();return Math.abs(e.scrollLeft-(e.scrollWidth-e.clientWidth))<2||[...e.children].some(c=>Math.abs(c.getBoundingClientRect().left-r.left)<2)})()`);assert.ok(aligned,'native rail did not snap');return{before,middle,frames};
  });
  for(const [name,rail,active] of [['hero','.hero-rail','.hero-slide[data-hero-active=true]']])await check(`${name} ${width} live drag and magnet`,async()=>{
   const p=await point(rail),dx=-Math.min(140,width*.4),before=await b.evaluate(pose(active));await start(p);await move(p,dx);const middle=await b.evaluate(pose(active));assert.ok(middle.x<before.x-50);
   await end(p,dx);const frames=await sample(pose(active));assert.ok(Math.abs(frames[0].x)>2,'new card appeared at its final position');assert.ok(Math.abs(frames.at(-1).x)<1,'magnet did not settle');assert.ok(frames.every(row=>!row.overflow));return{before,middle,frames};
  });
  for(const rail of ['.team-grid','.about-stack'])await check(`mouse magnet ${width} ${rail}`,async()=>{
   await b.evaluate(`document.querySelector('${rail}').scrollTo({left:0,behavior:'instant'})`);const p=await point(rail),dx=-Math.min(190,width*.5);await start(p,false);await move(p,dx,0,false);
   const middle=await b.evaluate(`document.querySelector('${rail}').scrollLeft`);await end(p,dx,false);const frames=await sample(`document.querySelector('${rail}').scrollLeft`);
   assert.ok(Math.abs(frames[0]-middle)<25,'release snapped instantly');assert.ok(new Set(frames.map(Math.round)).size>5,'no magnetic settling');assert.equal(await b.evaluate(`document.querySelector('${rail}').dataset.railSettling`),'false');return{middle,frames};
  });
  await check(`trusted touch and local browser errors ${width}`,async()=>{assert.ok(await b.evaluate(`window.__touchTrace.some(row=>row.pointer==='touch'&&row.trusted)`));assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);return{};});
 }
 await b.viewport(390,844,false);await b.open(base);
 await check('certificate translation and rotation return from their actual pose',async()=>{
  const p=await point('[data-certificate-scene]');await start(p);await move(p,-140);
  const expression=`(()=>{const e=document.querySelector('.certificate-art'),s=getComputedStyle(e);return{x:parseFloat(s.translate)||0,angle:parseFloat(s.rotate)||0}})()`,middle=await b.evaluate(expression);
  assert.ok(Math.abs(middle.x)>20&&Math.abs(middle.angle)>1);await end(p,-140,true,true);const frames=await sample(expression);
  assert.ok(Math.abs(frames[0].x-middle.x)<10&&Math.abs(frames[0].angle-middle.angle)<.5);assert.ok(Math.abs(frames.at(-1).x)<.1&&Math.abs(frames.at(-1).angle)<.1);return{middle,frames};
 });
 await check('a pending hero image cannot commit during a new gesture',async()=>{
  await b.center('.hero-rail');const before=await b.evaluate(`document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsId`);
  await b.evaluate(`window.__originalDecode=HTMLImageElement.prototype.decode;HTMLImageElement.prototype.decode=async function(){await new Promise(r=>setTimeout(r,250));return window.__originalDecode.call(this)}`);
  const p=await point('.hero-rail');await start(p);await move(p,-130);await end(p,-130);await b.pause(25);await start(p);await move(p,-20);await b.pause(300);
  assert.equal(await b.evaluate(`document.querySelector('.hero-slide[data-hero-active=true]').dataset.newsId`),before);await end(p,-20,true,true);await b.settle();await b.evaluate(`HTMLImageElement.prototype.decode=window.__originalDecode;delete window.__originalDecode`);return{};
 });
 await check('dock material expands and contracts without replacing its node',async()=>{
  await b.evaluate(`window.__dockNode=document.querySelector('[data-mobile-nav]')`);const before=await b.evaluate(dockPose);await clickRaw('[data-open-menu]');const opening=await sample(dockPose);await b.settle();
  assert.ok(Math.abs(opening[0].h-before.h)<80,'opening jumped');assert.ok(new Set(opening.map(row=>Math.round(row.h))).size>8);assert.ok(opening.every(row=>row.opacity===1&&row.suppressed==='false'));
  const expanded=await b.evaluate(dockPose);await clickRaw('[data-open-menu]');const closing=await sample(dockPose);await b.settle();assert.ok(Math.abs(closing[0].h-expanded.h)<80,'closing jumped');assert.ok(closing.every(row=>row.opacity===1&&row.suppressed==='false'));
  assert.equal(await b.evaluate(`window.__dockNode===document.querySelector('[data-mobile-nav]')`),true);return{before,opening,closing};
 });
 await check('dock interruptions retain the visible material pose',async()=>{
  await clickRaw('[data-open-menu]');await b.pause(80);const before=await b.evaluate(dockPose);await clickRaw('[data-open-menu]');const after=await b.evaluate(dockPose);assert.ok(Math.abs(before.h-after.h)<55,'close interrupted from a different pose');
  await b.pause(70);const closing=await b.evaluate(dockPose);await clickRaw('[data-open-menu]');const reopened=await b.evaluate(dockPose);assert.ok(Math.abs(closing.h-reopened.h)<55,'reopen interrupted from a different pose');await b.settle();
  assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),true);await clickRaw('[data-open-menu]');await b.settle();return{before,after,closing,reopened};
 });
 await check('dock dragged close keeps the material continuous',async()=>{
  await clickRaw('[data-open-menu]');await b.settle();const p=await b.point('.menu-grip');await start(p);await move(p,0,100);const before=await b.evaluate(dockPose);await end(p,0);const frames=await sample(dockPose);
  const bottoms=frames.map(row=>row.y+row.h);assert.ok(Math.abs(bottoms[0]-(before.y+before.h))<30);assert.ok(bottoms.slice(1).every((bottom,i)=>Math.abs(bottom-bottoms[i])<30),'material jumped after a dragged close');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),false);return{before,frames};
 });
 await check('dock local browser errors',async()=>{assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);return{};});
}finally{await writeFile(`tmp/planning/${process.env.QA_REPORT_PREFIX||'iteration39'}-motion.json`,JSON.stringify(report,null,2));await b.close();}
assert.deepEqual(report.failures,[]);console.log(`${report.cases.length} motion cases passed`);
