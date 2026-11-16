import assert from'node:assert/strict';import{mkdirSync,writeFileSync}from'node:fs';import{touchBrowser}from'./touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',report=[];mkdirSync('tmp/planning/iteration55',{recursive:true});
async function check(name,fn){try{const evidence=await fn();report.push({name,pass:true,evidence});console.log('PASS '+name)}catch(error){report.push({name,pass:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}}
const controls=id=>`[data-rail-controls="${id}"]`;
async function mouse(point,type,buttons=0){await b.send('Input.dispatchMouseEvent',{type,...point,button:type==='mouseMoved'?'none':'left',buttons,clickCount:type==='mouseMoved'?0:1})}
async function press(selector){const p=await b.point(selector);await mouse(p,'mousePressed',1);await mouse(p,'mouseReleased');}
async function state(id){return b.evaluate(`(()=>{const r=document.getElementById('${id}'),c=[...r.children].filter(e=>!e.hidden&&!e.matches('script,style,template')),i=Number(r.dataset.railIndex),q=document.querySelector('${controls(id)}');return{index:i,count:c.length,left:r.scrollLeft,aligned:c[i]?c[i].getBoundingClientRect().left-r.getBoundingClientRect().left:null,current:[...q.querySelectorAll('[data-current="true"]')].length,counter:q.querySelector('output').textContent,moving:r.dataset.railSettling,errors:__touchErrors}})()`)}
async function settled(id){await b.until(`(()=>{const r=document.getElementById('${id}'),c=[...r.children].filter(e=>!e.hidden&&!e.matches('script,style,template')),i=Number(r.dataset.railIndex);return c[i]&&r.dataset.railSettling!=='true'&&Math.abs(c[i].getBoundingClientRect().left-r.getBoundingClientRect().left)<1.2})()`);const s=await state(id);assert.equal(s.current,1);assert.deepEqual(s.errors,[]);return s;}
async function mouseDrag(id,dx,release=true){const p=await b.point('#'+id,.6,.3);await mouse(p,'mousePressed',1);for(let n=1;n<=7;n++){await mouse({x:p.x+dx*n/7,y:p.y},'mouseMoved',1);await b.pause(12)}if(release)await mouse({x:p.x+dx,y:p.y},'mouseReleased');return p;}
async function fastTouch(id,dx){const p=await b.point('#'+id,.65,.3),touch=(x,y)=>[{x,y,id:1,radiusX:5,radiusY:5,force:1}];await b.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:touch(p.x,p.y)});for(let i=1;i<=6;i++){await b.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:touch(p.x+dx*i/6,p.y)});await b.pause(12)}await b.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
try{
 await b.send('Page.bringToFront');
 for(const width of[390,768]){
  await b.viewport(width,1000,false);await b.open(base);
  for(const id of['offers-rail','masters-rail','about-rail','gifts-rail','reviews-rail']){
   await b.center('#'+id);
   await check(`rapid arrows use one stable index and left-aligned ends ${id} ${width}`,async()=>{
    await b.evaluate(`(()=>{window.__railIndices=[];const rail=document.getElementById('${id}');new MutationObserver(records=>{const i=Number(rail.dataset.railIndex);if(__railIndices.at(-1)!==i)__railIndices.push(i)}).observe(rail,{attributes:true,attributeFilter:['data-rail-index']})})()`);
    const start=await state(id);for(let i=0;i<start.count+2;i++){await press(controls(id)+' [data-rail-step="1"]');await b.pause(24)}
    const end=await settled(id);assert.equal(end.index,end.count-1);const trace=await b.evaluate('__railIndices');assert.ok(trace.every((v,i)=>!i||v>=trace[i-1]),JSON.stringify(trace));
    for(let i=0;i<start.count+2;i++){await press(controls(id)+' [data-rail-step="-1"]');await b.pause(24)}const first=await settled(id);assert.equal(first.index,0);assert.ok(Math.abs(first.left)<1.2);await press(controls(id)+' [data-rail-step="1"]');const next=await settled(id);assert.equal(next.index,1);return{end,first,next,trace};
   });
   await check(`mouse interrupts and repeats without teleport or frozen snap ${id} ${width}`,async()=>{
    await press(controls(id)+' [data-rail-step="1"]');await b.pause(45);const before=await state(id),p=await b.point('#'+id,.6,.3);await mouse(p,'mousePressed',1);const caught=await state(id);assert.ok(Math.abs(caught.left-before.left)<90,JSON.stringify({before,caught}));
    for(let i=1;i<=6;i++){await mouse({x:p.x-145*i/6,y:p.y},'mouseMoved',1);await b.pause(12)}await mouse({x:p.x-145,y:p.y},'mouseReleased');
    for(let i=0;i<4;i++){await b.pause(35);await mouseDrag(id,i===2?100:-130)}return settled(id);
   });
   await check(`native rapid swipes and reverse release settle at the same stops ${id} ${width}`,async()=>{for(let i=0;i<4;i++){await fastTouch(id,-150);await b.pause(35)}await settled(id);await fastTouch(id,150);return settled(id)});
  }
 }
 await check('CPU-constrained rail input has no application errors or abandoned transition',async()=>{
  await b.viewport(390,844,false);await b.open(base);await b.center('#masters-rail');await b.send('Emulation.setCPUThrottlingRate',{rate:4});
  const start=performance.now();for(let i=0;i<8;i++){await press(controls('masters-rail')+` [data-rail-step="${i<5?1:-1}"]`);await b.pause(35)}const final=await settled('masters-rail');await b.send('Emulation.setCPUThrottlingRate',{rate:1});return{elapsed:performance.now()-start,final};
 });
}finally{await b.send('Emulation.setCPUThrottlingRate',{rate:1});writeFileSync('tmp/planning/iteration55/rails.json',JSON.stringify({report,published:false},null,2));await b.close()}
assert.ok(report.every(r=>r.pass),'Rail stress scenarios failed');
