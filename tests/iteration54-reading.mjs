import assert from 'node:assert/strict';
import {writeFileSync,mkdirSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',report=[];
const iteration=process.env.QA_REPORT_PREFIX||'iteration54';mkdirSync('tmp/planning/'+iteration,{recursive:true});
async function check(name,run){try{const evidence=await run();report.push({name,pass:true,evidence});console.log('PASS '+name)}catch(error){report.push({name,pass:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}}
async function open(width){await b.viewport(width,1000,true);await b.open(base);await b.until(`document.querySelector('#reviews-rail').dataset.bentoReady==='true'`)}
async function edges(selector,position){return b.evaluate(`(()=>{const p=document.querySelector('${selector}');p.scrollTop=${position==='end'?'p.scrollHeight':position==='middle'?'(p.scrollHeight-p.clientHeight)/2':'0'};p.dispatchEvent(new Event('scroll'));const s=getComputedStyle(p);return{above:p.dataset.readingAbove,below:p.dataset.readingBelow,range:p.scrollHeight-p.clientHeight,behavior:s.overscrollBehaviorY,top:s.getPropertyValue('--reading-fade-top'),bottom:s.getPropertyValue('--reading-fade-bottom'),buttons:getComputedStyle(p,'::-webkit-scrollbar-button').display}})()`)}
try{
 await b.send('Page.bringToFront');
 for(const width of [320,390,600,768,960,961,1024,1440])await check('matching compact breakpoints '+width,async()=>{
  await open(width);
  const state=await b.evaluate(`(()=>{const r=document.querySelector('#reviews-rail'),a=document.querySelector('#about-rail');return{reviews:r.dataset.reviewFormat,reviewControls:getComputedStyle(r.nextElementSibling).display,about:getComputedStyle(a).overflowX,photoControls:getComputedStyle(r.querySelector('.slide-indicator')).display,cards:[...r.querySelectorAll('[data-review-card]')].map(c=>({id:c.id,short:c.dataset.reviewShort,shape:c.dataset.reviewShape,video:c.dataset.reviewVideo})),errors:__touchErrors}})()`);
  assert.equal(state.reviews,width<=960?'phone':'module');assert.equal(state.about==='auto',width<=960);assert.equal(state.reviewControls==='none',width>960);assert.equal(state.photoControls==='none',width<=960);
  const videos=state.cards.flatMap((c,i)=>c.video==='true'?[i]:[]);assert.ok(videos.every(i=>i<4));
  if(width>960){const counts={};for(const c of state.cards){if(c.short==='true')assert.equal(c.shape,'1x2');if(['1x2','2x1'].includes(c.shape))counts[c.shape]=(counts[c.shape]||0)+1;}assert.equal(Object.keys(counts).length,2);assert.ok(Math.max(...Object.values(counts))<=4)}
  assert.deepEqual(state.errors,[]);return state;
 });
 for(const width of [320,390,768,960])await check('review opening paragraphs and fixed reading height '+width,async()=>{
  await open(width);await b.center('#reviews');const collapsed=await b.evaluate(`(()=>{const c=document.querySelector('#review-03');return{h:c.offsetHeight,visible:[...c.querySelectorAll('blockquote p')].filter(p=>!p.hidden).length,button:c.querySelector('[data-review-read]').hidden,range:c.querySelector('.review-prose').scrollHeight-c.querySelector('.review-prose').clientHeight}})()`);
  assert.equal(collapsed.visible,1);assert.equal(collapsed.button,false);assert.equal(collapsed.h,600);assert.ok(collapsed.range<=8,JSON.stringify(collapsed));
  await b.evaluate(`document.querySelector('#review-03 [data-review-read]').click()`);await b.settle();
  const expanded=await b.evaluate(`(()=>{const c=document.querySelector('#review-03'),b=c.querySelector('[data-review-read]'),p=c.querySelector('.review-prose');return{h:c.offsetHeight,visible:[...c.querySelectorAll('blockquote p')].filter(p=>!p.hidden).length,label:b.textContent,photo:c.querySelector('.review-gallery').inert,range:p.scrollHeight-p.clientHeight,buttonWidth:b.offsetWidth,copyWidth:c.querySelector('.review-copy').clientWidth-40}})()`);
  assert.equal(expanded.h,collapsed.h);assert.equal(expanded.visible,7);assert.equal(expanded.photo,true);assert.equal(expanded.label,'Показать фото');assert.equal(expanded.buttonWidth,expanded.copyWidth);assert.ok(expanded.range>100);
  for(const [position,expected]of [['start',['false','true']],['middle',['true','true']],['end',['true','false']]]){const e=await edges('#review-03 .review-prose',position);assert.deepEqual([e.above,e.below],expected);assert.equal(e.behavior,'contain');assert.equal(e.buttons,'none')}
  await b.evaluate(`document.querySelector('#review-03 [data-review-read]').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('#review-03').offsetHeight`),600);return{collapsed,expanded};
 });
 for(const width of [320,390,768,960])await check('About has equal previews, bottom full-width controls and individual fixed-height reading '+width,async()=>{
  await open(width);await b.center('#about');
  const before=await b.evaluate(`[...document.querySelectorAll('[data-about-card]')].map(c=>{const r=c.getBoundingClientRect(),p=c.querySelector('.about-prose'),b=c.querySelector('button'),br=b.getBoundingClientRect(),m=c.querySelector('.about-media').getBoundingClientRect(),inner=c.querySelector('.about-copy-inner').getBoundingClientRect();return{h:r.height,photo:[m.width,m.height],preview:[...p.children].filter(p=>!p.hidden).map(p=>p.textContent.length),label:b.textContent,button:[br.width,inner.width],bottom:r.bottom-br.bottom}})`);
  assert.ok(before.every(c=>c.h===before[0].h));for(const c of before){assert.ok(Math.abs(c.photo[0]-c.photo[1])<1);assert.equal(c.preview.length,1);assert.ok(c.preview[0]>=190&&c.preview[0]<=240);assert.equal(c.label,'Читать полностью');assert.equal(c.button[0],c.button[1]);assert.ok(Math.abs(c.bottom-32)<1)}
  await b.evaluate(`document.querySelector('[data-about-more]').click()`);await b.settle();
  const after=await b.evaluate(`[...document.querySelectorAll('[data-about-card]')].map(c=>({h:c.offsetHeight,expanded:c.querySelector('button').getAttribute('aria-expanded'),photo:c.querySelector('.about-media').inert,visible:[...c.querySelector('.about-prose').children].filter(p=>!p.hidden).length,range:c.querySelector('.about-prose').scrollHeight-c.querySelector('.about-prose').clientHeight}))`);
  assert.equal(after[0].expanded,'true');assert.equal(after[0].photo,true);assert.equal(after[0].visible,3);assert.ok(after.every((c,i)=>Math.abs(c.h-before[i].h)<1));assert.ok(after.slice(1).every(c=>c.expanded==='false'&&c.visible===1));
  await b.evaluate(`document.querySelector('[data-about-more]').click()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('[data-about-card]').offsetHeight`),Math.round(before[0].h));assert.deepEqual(await b.evaluate('__touchErrors'),[]);return{before,after};
 });
 await check('a new native touch at either review boundary can move the page',async()=>{
  await open(390);await b.evaluate(`document.querySelector('#review-03').scrollIntoView({block:'center',inline:'start',behavior:'instant'});document.querySelector('#review-03 [data-review-read]').click()`);await b.settle();await b.center('#review-03 .review-prose');
  const evidence=[];for(const [position,dy]of [['start',140],['end',-140]]){await edges('#review-03 .review-prose',position);const before=await b.evaluate('scrollY');await b.swipe(await b.point('#review-03 .review-prose'),0,dy);const after=await b.evaluate('scrollY');assert.ok(Math.abs(after-before)>20,JSON.stringify({position,before,after}));evidence.push({position,before,after})}return evidence;
 });
 await check('contact hierarchy spacing and bottom personal links',async()=>{
  await open(1440);await b.center('#contacts');const state=await b.evaluate(`(()=>{const rows=[...document.querySelectorAll('.contact-business-lines>div')].map(e=>e.getBoundingClientRect()),current=document.querySelector('.contact-address').getBoundingClientRect(),future=document.querySelector('.contact-future').getBoundingClientRect();return{gaps:rows.slice(1).map((r,i)=>r.top-rows[i].bottom),futureGap:future.top-current.bottom,map:document.querySelector('.contact-map').offsetHeight,people:[...document.querySelectorAll('.contact-person')].map(c=>{const copy=c.querySelector('.contact-person-copy').getBoundingClientRect(),a=[...c.querySelectorAll('.contact-person-links a')].map(e=>e.getBoundingClientRect()),ranges=[...c.querySelectorAll('[data-action-label]')].map(e=>e.getBoundingClientRect());return{height:c.offsetHeight,bottom:copy.bottom-a[1].bottom,textGap:ranges[1].top-ranges[0].bottom}})}})()`);assert.deepEqual(state.gaps,[12,12]);assert.ok(Math.abs(state.futureGap)<1);assert.ok(state.map<640);for(const c of state.people){assert.ok(c.height<175);assert.ok(Math.abs(c.bottom)<1);assert.ok(c.textGap<=9)}return state;
 });
}finally{writeFileSync('tmp/planning/'+iteration+'/reading.json',JSON.stringify({base,report,published:false},null,2));await b.close()}
assert.ok(report.every(r=>r.pass),report.filter(r=>!r.pass).map(r=>r.name).join(', '));
