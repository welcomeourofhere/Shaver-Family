import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync}from'node:fs';
import {touchBrowser}from'./touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',report=[];
mkdirSync('tmp/planning/iteration55',{recursive:true});
async function mouse(type,x,y,buttons=1){await b.send('Input.dispatchMouseEvent',{type,x,y,button:'left',buttons,clickCount:1})}
async function check(name,fn){try{const evidence=await fn();report.push({name,pass:true,evidence});console.log('PASS '+name)}catch(error){report.push({name,pass:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}}
try{
 await b.send('Page.bringToFront');
 for(const width of [390,768])for(const id of ['offers-rail','masters-rail','about-rail','gifts-rail','reviews-rail'])await check(`held mouse updates and reverses the shared indicator before release ${id} ${width}`,async()=>{
  await b.viewport(width,1000,false);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(base);await b.until(`document.querySelector('[data-review-bento]').dataset.bentoReady==='true'`);await b.center('#'+id);
  const state=()=>b.evaluate(`(()=>{const rail=document.getElementById('${id}'),controls=document.querySelector('[data-rail-controls="${id}"]');return{index:Number(rail.dataset.railIndex),output:controls.querySelector('output').textContent,current:[...controls.querySelectorAll('.rail-progress span')].findIndex(s=>s.dataset.current==='true'),settling:rail.dataset.railSettling,drag:rail.classList.contains('is-dragging'),left:rail.scrollLeft,selected:!!getSelection()?.toString(),errors:__touchErrors}})()`);
  const start=await state(),stride=await b.evaluate(`(()=>{const rail=document.getElementById('${id}'),cards=[...rail.children].filter(e=>!e.hidden&&!e.matches('script,style,template'));return cards[1].getBoundingClientRect().left-cards[0].getBoundingClientRect().left})()`),p=await b.point('#'+id,.88,.3);
  await mouse('mousePressed',p.x,p.y);await mouse('mouseMoved',p.x-12,p.y);await mouse('mouseMoved',p.x-stride*.62,p.y);await b.pause(35);
  const held=await state();assert.ok(held.drag);assert.equal(held.index,1);assert.equal(held.current,1);assert.match(held.output,/^02\s*\//);assert.notEqual(held.settling,'true');assert.equal(held.selected,false);
  await mouse('mouseMoved',p.x-stride*.2,p.y);await b.pause(35);const reverse=await state();assert.equal(reverse.index,0);assert.equal(reverse.current,0);assert.ok(reverse.drag);
  await mouse('mouseMoved',p.x-stride*.65,p.y);await b.pause(140);await mouse('mouseReleased',p.x-stride*.65,p.y,0);await b.pause(550);const end=await state();assert.equal(end.index,1);assert.equal(end.current,1);assert.ok(!end.drag);assert.deepEqual(end.errors,[]);return{start,stride,held,reverse,end};
 });
}finally{writeFileSync('tmp/planning/iteration55/live-rails.json',JSON.stringify({report,published:false},null,2));await b.close()}
assert.ok(report.every(row=>row.pass),'Live rail indicators failed');
