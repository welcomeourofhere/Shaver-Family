import assert from 'node:assert/strict';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
import {planReviews,reviewNeighbors} from '../src/scripts/review-layout.ts';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4325/',report={cases:[],failures:[],published:false};
const reviews=JSON.parse(readFileSync('content/reviews.json','utf8')),ids=reviews.map(r=>r.id),extras=['reviews-yandex','reviews-coffee','reviews-vk'];
mkdirSync('tmp/planning/iteration50',{recursive:true});mkdirSync('artifacts/iteration50',{recursive:true});
async function check(name,run){if(process.env.QA_REVIEW_FOCUS&&!new RegExp(process.env.QA_REVIEW_FOCUS).test(name))return;try{const detail=await run();report.cases.push({name,...detail});console.log('PASS '+name)}catch(error){report.failures.push({name,error:String(error)});console.log('FAIL '+name+': '+error.message);throw error}finally{writeFileSync(`tmp/planning/iteration50-reviews${process.env.QA_REVIEW_FOCUS?'-focused':''}.json`,JSON.stringify(report,null,2));}}
const visible=`[...document.querySelectorAll('#reviews-rail>[data-review-tile]')].filter(c=>!c.hidden)`;
async function key(key,code=key){const windowsVirtualKeyCode={Escape:27,Enter:13,ArrowDown:40,ArrowLeft:37,ArrowRight:39,ArrowUp:38,End:35,Home:36,Tab:9,' ':32}[key]||0;await b.send('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});}
async function click(selector){await b.center(selector);await b.tap(await b.point(selector));await b.pause(250);}
async function selectReview(id){await b.evaluate(`document.getElementById(${JSON.stringify(id)}).scrollIntoView({block:'center',inline:'start',behavior:'instant'})`);await b.pause(230);await b.settle();}
let initScript;
async function open(seed){
 if(initScript){await b.send('Page.removeScriptToEvaluateOnNewDocument',{identifier:initScript});initScript=undefined;}
 if(seed!==undefined){const r=await b.send('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const get=crypto.getRandomValues.bind(crypto);Object.defineProperty(crypto,'getRandomValues',{configurable:true,value:a=>{if(a instanceof Uint32Array&&a.length===1){a[0]=${seed};return a;}return get(a)}})})()`});initScript=r.identifier;}
 await b.open(base);await b.until(`document.querySelector('#reviews-rail').dataset.bentoReady==='true'`);
}
function seedFor(predicate){for(let seed=0;seed<2000;seed++)if(predicate(planReviews(ids,extras,4,seed)))return seed;throw new Error('No planner fixture');}
const shortFeature=seedFor(p=>p.tiles.some(t=>t.w===2&&t.h===2&&t.id==='review-04'));
const longFeature=seedFor(p=>p.tiles.some(t=>t.w===2&&t.h===2&&t.id==='review-03'));
const withCoffee=seedFor(p=>p.tiles.some(t=>t.id==='reviews-coffee'));
async function geometry(){return b.evaluate(`(()=>{const b=document.querySelector('#reviews-rail'),r=b.getBoundingClientRect(),s=getComputedStyle(b);return{columns:Number(s.getPropertyValue('--review-columns')),rows:Number(s.getPropertyValue('--review-rows')),gap:parseFloat(s.gap),unit:parseFloat(s.getPropertyValue('--size-260')),board:{x:r.x,y:r.y,w:r.width,h:r.height},cards:${visible}.map(c=>{const r=c.getBoundingClientRect();return{id:c.id,x:r.x,y:r.y,w:r.width,h:r.height,tone:c.dataset.reviewTone,extra:c.hasAttribute('data-review-extra'),composition:c.dataset.reviewComposition}}),overflow:document.documentElement.scrollWidth>innerWidth+1,errors:__touchErrors}})()`);}
function tiled(g){
 const cell=(g.board.w-(g.columns-1)*g.gap)/g.columns,cells=Array.from({length:g.rows},()=>Array(g.columns).fill(0)),rects=[];
 for(const card of g.cards){const x=Math.round((card.x-g.board.x)/(cell+g.gap)),y=Math.round((card.y-g.board.y)/(g.unit+g.gap)),w=Math.round((card.w+g.gap)/(cell+g.gap)),h=Math.round((card.h+g.gap)/(g.unit+g.gap));assert.ok(Math.abs(card.x-g.board.x-x*(cell+g.gap))<.6&&Math.abs(card.y-g.board.y-y*(g.unit+g.gap))<.6,JSON.stringify({board:g.board,card,x,y,cell,gap:g.gap,unit:g.unit}));assert.ok(Math.abs(card.w-(w*cell+(w-1)*g.gap))<.6&&Math.abs(card.h-(h*g.unit+(h-1)*g.gap))<.6);for(let dy=0;dy<h;dy++)for(let dx=0;dx<w;dx++)cells[y+dy][x+dx]++;rects.push({...card,x,y,w,h});}
 assert.ok(cells.flat().every(n=>n===1),JSON.stringify(g));assert.equal(g.board.h,g.rows*g.unit+(g.rows-1)*g.gap);
 assert.deepEqual(g.cards.filter(c=>!c.extra).map(c=>c.id).sort(),[...ids].sort());assert.deepEqual([...new Set(g.cards.map(c=>c.tone))].sort(),['blue','ink','red','yellow']);
 assert.equal(rects.filter(c=>!c.extra&&c.w>=2&&c.h>=2).length,g.columns===4?1:0);
 for(const a of rects)for(const c of rects)if(a!==c&&reviewNeighbors(a,c))assert.notEqual(a.tone,c.tone);
 assert.equal(g.overflow,false);assert.deepEqual(g.errors,[]);
}
try{
 await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 for(const width of [601,620,768,820,960,1024,1100,1440,1920])for(const theme of ['light','dark'])await check(`complete rectangular modules ${width} ${theme}`,async()=>{
  await b.viewport(width,1000,true);await open(50);await b.evaluate(`document.documentElement.dataset.theme='${theme}'`);await b.center('#reviews');const g=await geometry();tiled(g);
  const h=g.board.h;await b.pause(140);assert.equal((await geometry()).board.h,h);
  assert.equal(await b.evaluate(`!!document.querySelector('#reviews details,#reviews .review-reading,#reviews .review-video-fallback,#reviews [data-review-video-play],#reviews a:has(img)')`),false);
  for(const r of reviews)assert.equal((await b.evaluate(`document.querySelector('#${r.id} blockquote').textContent`)).replace(/\s+/gu,' '),r.text.join('').replace(/\s+/gu,' '));
  return {width,columns:g.columns,rows:g.rows,cards:g.cards.map(c=>({id:c.id,shape:[c.w,c.h],tone:c.tone}))};
 });
 await check('real page loads vary review order and palette; fillers can be absent',async()=>{
  await b.viewport(1440,1000,true);const orders=new Set(),colours=new Set(),fillers=new Set();
  for(let i=0;i<18;i++){await open();const g=await geometry();tiled(g);orders.add(g.cards.map(c=>c.id).join());colours.add(g.cards.map(c=>c.tone).join());fillers.add(g.cards.filter(c=>c.extra).length);}
  assert.ok(orders.size>1&&colours.size>1);return {orders:orders.size,palettes:colours.size,optionalFillCounts:[...fillers]};
 });
 await check('large cards follow measured text; labels sit on photos and colours stay still',async()=>{
  await b.viewport(1440,1000);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});
  const results=[];
  for(const [seed,id,expected]of [[shortFeature,'review-04','top'],[longFeature,'review-03','side']]){
   await open(seed);await b.center('#'+id);await b.until(`document.querySelector('#${id}').dataset.reviewComposition==='${expected}'`);
   const read=()=>b.evaluate(`(()=>{const c=document.querySelector('#${id}'),r=c.getBoundingClientRect(),g=c.querySelector('.review-gallery').getBoundingClientRect(),p=c.querySelector('.review-about').getBoundingClientRect();return{h:r.height,w:r.width,photoH:g.height,photoW:g.width,label:{x:p.x-g.x,y:p.y-g.y,right:p.right<=g.right,bottom:p.bottom<=g.bottom},tone:c.dataset.reviewTone,color:getComputedStyle(c).backgroundColor,scale:new DOMMatrix(getComputedStyle(c.querySelector('.review-slide[data-active="true"] img')).transform).a}})()`);
   const before=await read();await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...await b.point('#'+id+' .review-copy',.65,.5)});await b.pause(280);const after=await read();
   assert.equal(after.color,before.color);assert.equal(after.tone,before.tone);assert.ok(after.scale>1&&after.scale<1.1);
   assert.ok(before.label.x>=11&&before.label.y>=11&&before.label.right&&before.label.bottom);
   if(expected==='top')assert.ok(before.photoH>before.h/2&&before.photoW===before.w);else assert.ok(before.photoW<before.w/2&&before.photoH===before.h);
   assert.equal(await b.evaluate(`document.querySelector('#${id} .review-gallery a')`),null);results.push({id,expected,...after});
  }
  assert.equal((await b.evaluate(`document.querySelector('#review-04 .review-about').textContent`)).replace(/\s/gu,' '),'О барбере Соне');return {results};
 });
 await check('reading progress follows the photo seam; phone retains its normal scrollbar',async()=>{
  const sizes=[];for(const width of [390,1440]){await b.viewport(width,1000,true);await open(longFeature);await selectReview('review-03');const state=await b.evaluate(`(()=>{const c=document.querySelector('#review-03'),p=c.querySelector('.review-prose'),r=c.getBoundingClientRect(),q=p.getBoundingClientRect(),bar=c.querySelector('.review-reading-progress'),v=bar.getBoundingClientRect();return{right:r.right-q.right,scrollbar:getComputedStyle(p).scrollbarWidth,progress:getComputedStyle(bar).display,lineWidth:v.width,lineHeight:v.height,arrows:getComputedStyle(p,'::-webkit-scrollbar-button').display,font:getComputedStyle(p.querySelector('blockquote')).fontSize}})()`);assert.equal(state.arrows,'none');assert.equal(state.font,width<=600?'13px':'14px');if(width<=600){assert.equal(state.right,20);assert.equal(state.scrollbar,'thin');assert.equal(state.progress,'none');}else{assert.equal(state.scrollbar,'none');assert.equal(state.progress,'block');assert.equal(state.lineWidth,2);await b.evaluate(`document.querySelector('#review-03 .review-prose').scrollTop=500`);await b.pause(50);assert.ok(await b.evaluate(`Number(document.querySelector('#review-03').style.getPropertyValue('--review-scroll-progress'))>0`));}sizes.push(state);}return {sizes};
 });
 await check('desktop full review scrolls internally with no reading button',async()=>{
  await b.viewport(1440,1000,true);await open(longFeature);await b.center('#review-03 .review-prose');
  const before=await b.evaluate(`({y:scrollY,h:document.querySelector('#review-03').offsetHeight})`);const p=await b.point('#review-03 .review-prose');
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mouseWheel',...p,deltaX:0,deltaY:220});await b.pause(180);
  assert.ok(await b.evaluate(`document.querySelector('#review-03 .review-prose').scrollTop>100`));assert.equal(await b.evaluate(`document.querySelector('#review-03').offsetHeight`),before.h);assert.equal(await b.evaluate(`document.querySelector('#review-03 [data-review-read]').hidden`),true);
  await b.evaluate(`document.querySelector('#review-03 .review-prose').focus()`);await key('End');await b.pause(180);assert.match(await b.evaluate(`document.querySelector('#review-03 blockquote').lastElementChild.textContent`),/ветер в\sволосах/);return before;
 });
 for(const width of [320,390,540,600])await check(`phone sizing, arrows and fixed-height reader ${width}`,async()=>{
  await b.viewport(width,900);await open(withCoffee);await selectReview('review-04');
  assert.equal(await b.evaluate(`document.querySelector('#reviews-rail').dataset.reviewLayout`),'phone');
  const compact=await b.evaluate(`(()=>{const c=document.querySelector('#review-04');return{h:c.offsetHeight,photo:c.querySelector('.review-gallery').offsetHeight,text:c.querySelector('.review-prose').scrollHeight,copy:c.querySelector('.review-copy').offsetHeight,button:c.querySelector('[data-review-read]').hidden}})()`);
  assert.equal(compact.h,600);assert.ok(compact.photo>300&&compact.copy<300);assert.equal(compact.button,true);
  await selectReview('review-03');const initial=await b.evaluate(`({h:document.querySelector('#review-03').offsetHeight,i:document.querySelector('#reviews-rail').dataset.railIndex,photo:document.querySelector('#review-03 .review-gallery').offsetHeight})`);
  await click('#review-03 [data-review-read]');await b.until(`document.querySelector('#review-03 .review-gallery').offsetHeight<1`);
  const reading=await b.evaluate(`(()=>{const c=document.querySelector('#review-03'),p=c.querySelector('.review-prose'),a=c.querySelector('[data-review-read]');return{h:c.offsetHeight,p:p.clientHeight,scroll:p.scrollHeight,buttonW:a.clientWidth,copyW:c.querySelector('.review-copy').clientWidth-40,label:a.textContent,hidden:c.querySelector('.review-gallery').inert,expanded:a.getAttribute('aria-expanded')}})()`);
  assert.equal(reading.h,initial.h);assert.equal(reading.buttonW,reading.copyW);assert.equal(reading.hidden,true);assert.equal(reading.expanded,'true');assert.equal(reading.label,'Показать фото');
  await click('#review-03 [data-review-read]');await b.until(`document.querySelector('#review-03 .review-gallery').offsetHeight>200`);assert.equal(await b.evaluate(`document.querySelector('#review-03').offsetHeight`),initial.h);
  const n=await b.evaluate(`${visible}.length`);await click('[data-rail-controls="reviews-rail"] [data-rail-step="1"]');await b.pause(450);
  assert.equal(Number(await b.evaluate(`document.querySelector('#reviews-rail').dataset.railIndex`)),Math.min(n-1,Number(initial.i)+1));
  const count=await b.evaluate(`document.querySelector('[data-rail-controls="reviews-rail"] output').textContent`);assert.ok(count.endsWith(String(n).padStart(2,'0')));
  await b.evaluate(`(()=>{const r=document.querySelector('#reviews-rail');r.scrollLeft=r.scrollWidth})()`);await b.pause(200);assert.equal(await b.evaluate(`document.querySelector('[data-rail-controls="reviews-rail"] [data-rail-step="1"]').disabled`),true);
  const tones=await b.evaluate(`${visible}.map(c=>c.dataset.reviewTone)`);for(let i=1;i<tones.length;i++)assert.notEqual(tones[i],tones[i-1]);return {compact,reading,count};
 });
 for(const width of [320,390,540,600])await check(`short quotes fit entirely before their photos grow ${width}`,async()=>{
  await b.viewport(width,900,true);await open(withCoffee);const states=[];
  for(const id of ['review-01','review-04','review-05','review-06','review-07']){await selectReview(id);const state=await b.evaluate(`(()=>{const c=document.querySelector('#${id}'),p=c.querySelector('.review-prose');return{id:c.id,h:p.clientHeight,scroll:p.scrollHeight,top:p.scrollTop,photo:c.querySelector('.review-gallery').offsetHeight,read:c.querySelector('[data-review-read]').hidden}})()`);assert.ok(state.scroll<=state.h+1,JSON.stringify(state));assert.equal(state.top,0);assert.equal(state.read,true);assert.ok(state.photo>=270);states.push(state);}return {states};
 });
 await check('phone gallery swipes belong exclusively to the review rail',async()=>{
  await b.viewport(390,900);await open(withCoffee);await selectReview('review-01');
  const index=await b.evaluate(`Number(document.querySelector('#reviews-rail').dataset.railIndex)`);
  assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').hasAttribute('data-rail-nested')`),false);assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('#review-01 .slide-indicator')).display`),'none');
  await b.swipe(await b.point('#review-01 .review-gallery',.75,.4),-180);assert.equal(await b.evaluate(`Number(document.querySelector('#reviews-rail').dataset.railIndex)`),index+1);assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'0');assert.equal(await b.evaluate(`String(getSelection())`),'');return {};
 });
 await check('desktop media follow the finger and cancel cleanly',async()=>{
  await b.viewport(1440,1000);await open(withCoffee);await b.center('#review-01 .review-gallery');const start=await b.point('#review-01 .review-gallery',.75,.4);
  await b.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...start,id:1}]});await b.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:start.x-70,y:start.y,id:1}]});await b.pause(60);
  const during=await b.evaluate(`(()=>{const g=document.querySelector('#review-01 .review-gallery');return{pose:new DOMMatrix(getComputedStyle(g.querySelector('.review-slide[data-active="true"]')).transform).m41,other:getComputedStyle(g.querySelector('.review-slide:not([data-active="true"])')).opacity,selection:String(getSelection())}})()`);assert.ok(during.pose<-35&&during.pose>-100&&during.other==='1',JSON.stringify(during));assert.equal(during.selection,'');await b.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});await b.pause(380);assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'0');return during;
 });
 await check('phone photos advance automatically without indicators and pause when not visible',async()=>{
  await b.viewport(390,900);await open(withCoffee);await selectReview('review-01');const outer=await b.evaluate(`document.querySelector('#reviews-rail').dataset.railIndex`);await b.until(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex==='1'`);assert.equal(await b.evaluate(`document.querySelector('#reviews-rail').dataset.railIndex`),outer);
  await selectReview('review-04');const index=await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`);await b.pause(4400);assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),index);
  await b.viewport(390,900,true);await open(withCoffee);await selectReview('review-01');await b.pause(4400);assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'0');await b.evaluate(`document.querySelector('#review-01 .review-gallery').focus()`);await key('ArrowRight');assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'1');return {};
 });
 await check('mouse drag, keyboard media controls and resize preserve their selected owner',async()=>{
  await b.viewport(390,900);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await open(withCoffee);await selectReview('review-01');
  let p=await b.point('#review-01 .review-copy',.75,.5);const index=await b.evaluate(`Number(document.querySelector('#reviews-rail').dataset.railIndex)`);
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',clickCount:1});for(let i=1;i<=8;i++)await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-i*24,y:p.y,button:'left',buttons:1});await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x-192,y:p.y,button:'left',clickCount:1});await b.pause(450);
  assert.equal(await b.evaluate(`Number(document.querySelector('#reviews-rail').dataset.railIndex)`),index+1);assert.equal(await b.evaluate(`String(getSelection())`),'');
  await selectReview('review-01');const selected='review-01';await b.viewport(1440,1000,true);await b.center('#review-01 .review-gallery');await b.evaluate(`document.querySelector('#review-01 .review-gallery').focus()`);await key('ArrowRight');assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'1');
  await b.viewport(1440,1000,true);await b.pause(150);tiled(await geometry());await b.viewport(390,900,true);await b.pause(200);assert.equal(await b.evaluate(`${visible}[Number(document.querySelector('#reviews-rail').dataset.railIndex)].id`),selected);return {selected};
 });
 await check('video is the first looping slide, pauses offscreen and respects reduced motion',async()=>{
  await b.viewport(390,900);await open(withCoffee);await selectReview('review-07');await b.until(`document.querySelector('#review-07 video').currentTime>.15`);
  const state=await b.evaluate(`(()=>{const v=document.querySelector('#review-07 video');return{source:v.currentSrc,w:v.videoWidth,h:v.videoHeight,loop:v.loop,muted:v.muted,controls:v.controls,index:v.closest('[data-review-gallery]').dataset.slideIndex,duration:v.duration}})()`);
  assert.match(state.source,/review-07-video\.mp4$/);assert.equal(state.w,720);assert.equal(state.h,1280);assert.ok(state.loop&&state.muted&&!state.controls&&state.index==='0');
  await b.evaluate(`document.querySelector('#review-07 video').currentTime=8.3`);await b.pause(400);assert.ok(await b.evaluate(`document.querySelector('#review-07 video').currentTime<2`));
  await b.center('#services');await b.until(`document.querySelector('#review-07 video').paused`);
  await b.viewport(390,900,true);await open(withCoffee);await selectReview('review-07');assert.equal(await b.evaluate(`document.querySelector('#review-07 video').getAttribute('src')`),null);
  await b.evaluate(`document.querySelector('#review-07 .review-gallery').focus()`);await key(' ','Space');await b.until(`document.querySelector('#review-07 video').currentTime>.1`);await key(' ','Space');assert.equal(await b.evaluate(`document.querySelector('#review-07 video').paused`),true);return state;
 });
 await check('failed video selects its photo and a media indicator can retry without an original link',async()=>{
  await b.viewport(1440,1000,true);await open(withCoffee);await b.evaluate(`document.querySelector('#review-07 video').dataset.videoSrc='/missing-review-video.mp4'`);await selectReview('review-07');await b.evaluate(`document.querySelector('#review-07 .review-gallery').focus()`);await key(' ','Space');
  await b.until(`document.querySelector('#review-07 .review-gallery').dataset.slideIndex==='1'`);assert.match(await b.evaluate(`document.querySelector('#review-07 [role="status"]').textContent`),/Показываем фотографию/);
  await b.evaluate(`document.querySelector('#review-07 video').dataset.videoSrc='/media/reviews/review-07-video.mp4'`);await click('#review-07 [data-slide-index="0"]');await b.until(`document.querySelector('#review-07 video').readyState>=2`);return {};
 });
 await check('all optional cards share one structure and their actions still work',async()=>{
  await b.viewport(1440,1000,true);await open(withCoffee);
  const structural=await b.evaluate(`[...document.querySelectorAll('[data-review-extra]')].map(c=>({children:[...c.children].map(e=>e.className),action:c.querySelector('.btn').textContent.trim(),href:c.querySelector('a')?.href,display:getComputedStyle(c).display}))`);
  assert.ok(structural.every(c=>c.children.join()==='review-extra-body,btn review-extra-action'));await b.evaluate(`document.querySelector('#reviews-coffee button').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('#review-dialog').open`),true);await b.evaluate(`document.querySelector('#review-dialog [data-dismiss]').click()`);return {structural};
 });
 for(const width of [320,390,768,1440])await check(`200 percent text and button labels ${width}`,async()=>{
  await b.viewport(width,1000,true);await open(withCoffee);
  await b.evaluate(`(()=>{const es=[...document.querySelectorAll('#reviews .review-about,#reviews blockquote,#reviews .review-extra h3,#reviews .review-extra p,#reviews .review-card .btn')],sizes=es.map(e=>parseFloat(getComputedStyle(e).fontSize));es.forEach((e,i)=>e.style.fontSize=sizes[i]*2+'px')})()`);await selectReview('review-03');await b.pause(250);
  const bad=await b.evaluate(`(()=>{const bad=[];for(const e of document.querySelectorAll('#reviews .btn')){if(!e.getClientRects().length||e.closest('[hidden]'))continue;const r=e.getBoundingClientRect(),s=getComputedStyle(e),range=document.createRange();range.selectNodeContents(e);if(e.scrollWidth>e.clientWidth+1||r.height<44||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push(e.textContent);const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);while(w.nextNode()){range.selectNodeContents(w.currentNode);if(range.getClientRects().length>1)bad.push('wrap:'+e.textContent)}}return bad})()`);
  assert.deepEqual(bad,[]);assert.equal(await b.evaluate(`document.documentElement.scrollWidth>innerWidth+1`),false);if(width>600)tiled(await geometry());else{await click('#review-03 [data-review-read]');assert.equal(await b.evaluate(`document.querySelector('#review-03').offsetHeight`),600);}return {};
 });
 await check('hero and review media indicators use identical geometry and keyboard selection',async()=>{
  await b.viewport(1440,1000,true);await open(withCoffee);await selectReview('review-01');
  const state=await b.evaluate(`['.hero-nav','#review-01 .slide-indicator'].map(s=>{const e=document.querySelector(s),d=e.querySelector('.slide-dot[aria-current="true"]'),dot=getComputedStyle(d,'::after');return{height:e.offsetHeight,active:d.offsetWidth,dot:dot.height,radius:dot.borderRadius,gap:getComputedStyle(e).columnGap}})`);assert.deepEqual(state[0],state[1]);
  await b.evaluate(`document.querySelector('#review-01 .slide-dot').focus()`);await key('End');assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'1');await key('Home');assert.equal(await b.evaluate(`document.querySelector('#review-01 .review-gallery').dataset.slideIndex`),'0');return {state};
 });
}finally{await b.close();}
console.log(`${report.cases.length} review scenarios passed`);
