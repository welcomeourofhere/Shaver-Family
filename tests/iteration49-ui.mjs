import assert from 'node:assert/strict';
import {writeFileSync,mkdirSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
const report={cases:[],failures:[],published:false};
async function check(name,run){try{const result=await run();report.cases.push({name,...result});writeFileSync('tmp/planning/iteration49/ui-progress.json',JSON.stringify(report,null,2));console.log('PASS '+name)}catch(error){report.failures.push({name,error:String(error)});writeFileSync('tmp/planning/iteration49/ui-progress.json',JSON.stringify(report,null,2));console.log('FAIL '+name+': '+error.message);throw error}}
const click=async selector=>{await b.center(selector);await b.tap(await b.point(selector));};
async function key(key,code=key){const windowsVirtualKeyCode={Escape:27,Enter:13,ArrowDown:40,ArrowUp:38,End:35,Home:36,Tab:9,' ':32}[key]||0;await b.send('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});await b.settle();}
async function shot(name){const image=await b.send('Page.captureScreenshot',{format:'png'});writeFileSync(`tmp/planning/iteration49/screens/${name}.png`,Buffer.from(image.data,'base64'));}
try{
 mkdirSync('tmp/planning/iteration49/screens',{recursive:true});
 await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 for(const width of [320,390,600,620,768,960,1024,1440])await check(`hero and service composition ${width}`,async()=>{
  await b.viewport(width,900);await b.open(base);
  const state=await b.evaluate(`(()=>{const r=s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,w:r.width,h:r.height}};return{videoSrc:document.querySelector('.hero-video').getAttribute('src'),brand:getComputedStyle(document.querySelector('.hero-brand')).display,title:document.querySelector('.hero-heading-mobile').textContent,copy:document.querySelector('.hero-mobile-copy').textContent,news:!!document.querySelector('.hero-news-toggle'),dots:r('.hero-nav'),scene:r('.hero-scene'),photo:getComputedStyle(document.querySelector('.sd-photo')).display,edge:getComputedStyle(document.querySelector('.hero-edge'),'::before').content,cashbackTag:document.querySelector('#cashback').tagName,clip:getComputedStyle(document.querySelector('#cashback')).clipPath,overflow:document.documentElement.scrollWidth>innerWidth+1,errors:__touchErrors}})()`);
  assert.equal(await b.evaluate(`!!document.querySelector('.hero-video-toggle')`),false);assert.equal(state.news,false);assert.equal(state.cashbackTag,'ASIDE');assert.equal(state.overflow,false);assert.deepEqual(state.errors,[]);
  if(width<=960){assert.equal(state.brand,'none');assert.equal(state.title,'Барбершоп СОЮЗ');assert.equal(state.copy.replace(/\s/g,' '),'Первый барбершоп в Кирове, где стригут и бреют только прекрасные дамы');assert.ok(Math.abs((state.dots.left+state.dots.right)/2-width/2)<1);assert.equal(state.photo,'none');assert.equal(state.edge,'none');await b.until(`document.querySelector('.hero-video').readyState>=2`);if(width>=620)assert.match(state.clip,/inset\(0px/);}
  else {assert.equal(state.videoSrc,null);assert.equal(state.photo,'block');}
  if(width===390)await shot('hero-final-390');
  return state;
 });
 await check('hero video pauses, resumes and stops offscreen',async()=>{
  await b.viewport(390,844);await b.open(base);await b.until(`document.querySelector('video').readyState>=2&&!document.querySelector('video').paused`);
  await b.tap(await b.point('.hero-rail',.5,.2));assert.equal(await b.evaluate(`document.querySelector('video').paused`),true);
  const time=await b.evaluate(`document.querySelector('video').currentTime`);await b.pause(220);assert.equal(await b.evaluate(`document.querySelector('video').currentTime`),time);
  await b.tap(await b.point('.hero-rail',.5,.2));await b.until(`!document.querySelector('video').paused`);
  await b.center('#services');await b.until(`document.querySelector('video').paused`);
  await b.viewport(390,844,true);await b.open(base);assert.equal(await b.evaluate(`document.querySelector('video').paused`),true);
 });
 await check('cashback only its details action navigates',async()=>{
  await b.viewport(390,844,true);await b.open(base);await b.center('#cashback');
  const before=await b.evaluate(`location.hash`);await click('.cashback h2');assert.equal(await b.evaluate(`location.hash`),before);
  assert.equal(await b.evaluate(`document.querySelectorAll('#cashback a, #cashback button').length`),1);
  await click('.cashback-link');await b.until(`document.querySelector('#offer-cashback').dataset.offerActive==='true'`);
 });
 await check('dock shortcuts work while menu content is parked outside its dialog',async()=>{
  await b.viewport(390,844,true);await b.open(base);await click('[data-action="services"]');await b.until(`location.hash==='#services'`);
  await b.center('#cashback');await b.until(`document.querySelector('[data-action="cashback-info"]')!==null`);await click('[data-action="cashback-info"]');await b.until(`document.querySelector('#offer-cashback').dataset.offerActive==='true'`);
 });
 await check('service photo catches up when moving from phone to desktop',async()=>{
  await b.viewport(390,844,true);await b.open(base);await b.evaluate(`document.querySelectorAll('.sd-card')[0].querySelectorAll('details')[1].open=true`);await b.pause(80);
  await b.viewport(1440,900,true);await b.until(`(()=>{const p=document.querySelector('.sd-card[aria-hidden="false"]');return p.querySelector('[data-photo-current="true"]').getAttribute('src')===p.querySelector('.sd-service[open]').dataset.photoSrc})()`);
 });
 await check('desktop edge feedback is progressive; phone master hover keeps its colour',async()=>{
  await b.viewport(1440,900);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(base);await b.center('.hero-scene');
  const rect=await b.evaluate(`(()=>{const r=document.querySelector('.hero-slide[data-hero-active="true"] .hero-edge-prev').getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}})()`),values=[];
  for(const part of [.9,.5,.05]){await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x+rect.w*part,y:Math.max(110,rect.y+rect.h/3)});await b.pause(200);values.push(await b.evaluate(`Number(getComputedStyle(document.querySelector('.hero-slide[data-hero-active="true"] .hero-edge-prev'),'::before').opacity)`));}
  assert.ok(values[0]<values[1]&&values[1]<values[2]&&values[2]>.9,JSON.stringify(values));
  for(const width of [390,768]){await b.viewport(width,844,true);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(base);await b.center('.team-grid');const colour=await b.evaluate(`getComputedStyle(document.querySelector('.team-card')).backgroundColor`);const p=await b.point('.team-card',.5,.3);await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.pause(180);assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('.team-card')).backgroundColor`),colour);}
  return {values};
 });
 for(const width of [320,390,768])await check(`review photos, full text, video and platform cards ${width}`,async()=>{
  await b.viewport(width,844,true);await b.open(base);await b.center('#reviews-rail');
  assert.equal(await b.evaluate(`document.querySelectorAll('.review-card').length`),10);
  assert.equal(await b.evaluate(`document.querySelectorAll('.review-card:not(.review-platform)').length`),7);
  await click('#review-01 [data-review-photo-select="1"]');assert.equal(await b.evaluate(`!document.querySelector('#review-01 [data-review-photo="1"]').hidden`),true);
  await b.evaluate(`document.querySelector('#review-03').scrollIntoView({block:'center',inline:'start',behavior:'instant'})`);await b.pause(100);await b.settle();
  await click('#review-03 summary');assert.equal(await b.evaluate(`document.querySelector('#review-03 details').open`),true);assert.equal(await b.evaluate(`document.querySelectorAll('#review-03 blockquote p').length`),7);
  assert.match(await b.evaluate(`document.querySelector('#review-03 blockquote').textContent.replace(/\\s/g,' ')`),/ветер в волосах/);
  await b.evaluate(`document.querySelector('#review-07').scrollIntoView({block:'center',inline:'start',behavior:'instant'})`);await b.settle();await b.pause(120);await b.center('[data-review-video-play]');await click('[data-review-video-play]');
  if(!await b.evaluate(`!!document.querySelector('.review-video-frame video')`))await click('[data-review-video-play]');
  assert.match(await b.evaluate(`document.querySelector('.review-video-frame video').src`),/\/media\/reviews\/review-07-video\.mp4$/);
  await b.until(`document.querySelector('.review-video-frame video').readyState>=2`);assert.equal(await b.evaluate(`document.querySelector('.review-video-frame video').error`),null);const sources=await b.evaluate(`Array.from(document.querySelectorAll('.review-platform:has(a)')).map(e=>({title:e.querySelector('h3').textContent,link:e.querySelector('a').href}))`);assert.equal(sources.length,2);assert.ok(sources.every(source=>source.title.startsWith('Больше отзывов')));
  assert.equal(await b.evaluate(`!!document.querySelector('.review-links,.reviews-intro,[data-review-example="true"]')`),false);
  return {sources};
 });
 for(const width of [320,390,620,768,960,1024,1440])for(const theme of ['light','dark'])await check(`contact layout ${width} ${theme}`,async()=>{
  await b.viewport(width,900,true);await b.open(base);await b.evaluate(`document.documentElement.dataset.theme='${theme}';document.querySelector('#contacts').scrollIntoView({block:'start',behavior:'instant'})`);await b.settle();
  const layout=await b.evaluate(`(()=>{const r=s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}};return{map:r('.contact-map'),business:r('.contact-visit'),person1:r('.contact-person'),section:r('#contacts'),people:document.querySelectorAll('.contact-person').length,phone:document.querySelector('.contact-phone').href,overflow:document.documentElement.scrollWidth>innerWidth+1}})()`);
  assert.equal(layout.people,1);assert.equal(layout.overflow,false);assert.match(layout.phone,/tel:\+79229090043/);
  if(layout.section.w>850){assert.ok(layout.map.right<layout.business.x&&layout.business.y<layout.person1.y);assert.ok(Math.abs(layout.person1.bottom-layout.map.bottom)<1);}
  else assert.ok(layout.business.y<layout.map.y&&layout.map.y<layout.person1.y);
  if((width===390||width===1440)&&theme==='light'){await b.pause(250);await shot(`contacts-final-${width}`);}
  return layout;
 });
 for(const width of [320,390,768])await check(`menu selection, settings layout, repeat trigger ${width}`,async()=>{
  await b.viewport(width,844,true);await b.open(base);await b.center('.sd-stack');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='services'`);await click('[data-open-menu]');
  const link=await b.evaluate(`(()=>{const e=document.querySelector('#mobile-menu nav [aria-current]'),s=getComputedStyle(e);return{background:s.backgroundColor,radius:s.borderRadius}})()`);assert.equal(link.background,'rgb(255, 204, 41)');assert.equal(link.radius,'12px');
  const before=await b.evaluate(`getComputedStyle(document.querySelector('#mobile-menu .fb-setting')).backgroundColor`);await click('#mobile-menu .fb-setting');const after=await b.evaluate(`getComputedStyle(document.querySelector('#mobile-menu .fb-setting')).backgroundColor`);assert.notEqual(before,after);
  await click('#mobile-menu .choice-trigger');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu .choice-list').matches(':popover-open')`),true);assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('#mobile-menu .choice-list')).borderWidth`),'0px');
  await click('#mobile-menu .choice-trigger');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu .choice-list').matches(':popover-open')`),false);
  await click('#mobile-menu .choice-trigger');await key('End');await key('Enter');assert.equal(await b.evaluate('document.documentElement.dataset.theme'),'dark');
  if(width===390)await shot('menu-final-390');await key('Escape');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),false);
 });
 await check('FAQ renders catalogue values and no template placeholders',async()=>{
  await b.viewport(390,844,true);await b.open(base);
  const answers=await b.evaluate(`Array.from(document.querySelectorAll('.faq-answer')).map(e=>e.textContent).join(' ')`);assert.ok(!answers.includes('{'));for(const value of ['1 500','2 300','60–90','1 100','1 200'])assert.ok(answers.includes(value),value);
  assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);
 });
 await check('offer notes belong to their card on phone and desktop',async()=>{
  for(const width of [390,1440]){
   await b.viewport(width,900,true);await b.open(base);await b.evaluate(`location.hash='#offer-first-visit'`);await b.until(`document.querySelector('#offer-first-visit').dataset.offerActive==='true'`);await b.center('#offer-first-visit');
   const placement=await b.evaluate(`(()=>{const card=document.querySelector('#offer-first-visit').getBoundingClientRect(),note=document.querySelector('#offer-first-visit .of-note').getBoundingClientRect();return{right:card.right-note.right,top:note.top-card.top,count:document.querySelectorAll('.of-note').length}})()`);assert.ok(Math.abs(placement.right-8)<1&&Math.abs(placement.top-8)<1&&placement.count===9,JSON.stringify(placement));
   await click('#offer-first-visit .info-trigger');assert.equal(await b.evaluate(`document.querySelector('#offer-first-visit .info-panel').matches(':popover-open')`),true);await key('Escape');
  }
 });
}finally{writeFileSync('tmp/planning/iteration49-ui.json',JSON.stringify(report,null,2));await b.close();}
assert.deepEqual(report.failures,[]);console.log(`${report.cases.length} iteration49 cases passed`);
