import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',report={cases:[],failures:[],published:false};
async function check(name,run){try{report.cases.push({name,...await run()});console.log('PASS '+name)}catch(error){report.failures.push({name,error:error.message});console.log('FAIL '+name+': '+error.message)}}
async function click(selector){await b.evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);await b.settle();}
async function key(key){const code={Escape:27,Tab:9,Enter:13}[key];await b.send('Input.dispatchKeyEvent',{type:'keyDown',key,windowsVirtualKeyCode:code});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key,windowsVirtualKeyCode:code});await b.settle();}
async function context(selector,id){await b.center(selector);await b.until(`document.querySelector('[data-mobile-nav]').dataset.section===${JSON.stringify(id)}`);}
async function close(){await key('Escape');assert.equal(await b.evaluate(`!!document.querySelector('dialog:modal')`),false);}
function contrast(a,b){const luminance=s=>s.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0),x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
try{
 await b.viewport(390,844,true);await b.open(base);
 for(const [selector,id] of [['.hero-scene','top'],['.of-rail','offers'],['.sd-stack','services'],['.team-grid','masters'],['.visit-ticket','first-visit'],['.about-stack','about'],['#certificates','certificates'],['#reviews','reviews'],['#faq','faq'],['#contacts','contacts'],['footer','footer']])await check('context actions '+id,async()=>{
  await context(selector,id);return await b.evaluate(`({count:Number(document.querySelector('[data-mobile-nav]').dataset.actionCount),actions:[...document.querySelectorAll('[data-dock-slot]:not([hidden])')].map(e=>e.dataset.action)})`);
 });
 for(const [selector,id] of [['.visit-ticket','first-visit'],['.team-grid','masters']])await check('personal booking '+id,async()=>{
  await context(selector,id);const selectors=id==='first-visit'?['[data-action="visit-sonya"]','[data-action="visit-sveta"]']:['[data-action="master-booking"]'];
  const results=[];for(const action of selectors){
   const expected=await b.evaluate(id==='first-visit'?`document.querySelector('.visit-actions [data-master="souz-${action.includes('sonya')?'sonya-kid':'svetlana'}"]').dataset.bookingUrl`:`document.querySelector('.team-card[data-mobile-current=true] .team-book').dataset.bookingUrl`);
   await click(action);const row=await b.evaluate(`({open:document.querySelector('[data-booking-drawer]').open,url:document.querySelector('[data-booking-drawer]').dataset.bookingUrl,suppressed:document.querySelector('[data-mobile-nav]').dataset.suppressed})`);
   assert.equal(row.open,true);assert.equal(new URL(row.url).hostname,new URL(expected).hostname.replace(/^n/,'b'));assert.equal(row.suppressed,'true');await close();results.push(row);
  }return{results};
 });
 await check('categories use the existing selection owner',async()=>{await context('.sd-stack','services');await click('[data-action="categories"]');await click('[data-dock-category="3"]');assert.equal(await b.evaluate(`document.querySelector('[data-sd-tab="3"]').getAttribute('aria-selected')`),'true');return{};});
 for(let i=0;i<5;i++)await check('selected service contrast '+i,async()=>{
  await click(`[data-sd-tab="${i}"]`);const row=await b.evaluate(`(()=>{const p=document.querySelector('.sd-card[aria-hidden=false]'),d=p.querySelector('details[open]'),s=getComputedStyle(d),t=getComputedStyle(d.querySelector('.sd-description')),v=getComputedStyle(d.querySelector('.sd-duration'));return{background:s.backgroundColor,color:s.color,description:t.color,opacity:t.opacity,duration:v.color,durationOpacity:v.opacity}})()`);
  assert.ok(contrast(row.background,row.color)>=4.5,JSON.stringify(row));assert.ok(contrast(row.background,row.description)>=4.5);assert.ok(contrast(row.background,row.duration)>=4.5);assert.equal(row.opacity,'1');assert.equal(row.durationOpacity,'1');return row;
 });
 await check('offers previous and next keep the active action synchronized',async()=>{
  await context('.of-rail','offers');const first=await b.evaluate(`Number(document.querySelector('[data-offers]').dataset.offerIndex)`);await click('[data-action="offer-next"]');await click('[data-action="offer-prev"]');assert.equal(await b.evaluate(`Number(document.querySelector('[data-offers]').dataset.offerIndex)`),first);
  const ids=[];for(let i=0;i<11;i++){
   const row=await b.evaluate(`(()=>{const e=document.querySelector('.of-card[data-offer-active=true] .of-action'),b=document.querySelector('[data-action="offer-action"]');return{id:e.closest('.of-card').dataset.offerId,expected:e.hasAttribute('data-booking')?'booking-drawer':e.hasAttribute('data-contact')?'contact-dialog':e.getAttribute('aria-controls'),actual:b.getAttribute('aria-controls')}})()`);assert.equal(row.actual,row.expected);ids.push(row.id);await click('[data-action="offer-next"]');
  }assert.equal(new Set(ids).size,11);return{ids};
 });
 await check('certificate action and menu booking use their original dialogs',async()=>{
  await context('#certificates','certificates');await click('[data-action="certificate-next"]');assert.ok(await b.evaluate(`!!document.querySelector('[data-certificate][aria-pressed=true]')`));await click('[data-action="certificate-buy"]');assert.equal(await b.evaluate(`document.querySelector('#contact-dialog').open`),true);await close();
  await click('[data-open-menu]');await click('#mobile-menu [data-action="booking"]');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),false);assert.equal(await b.evaluate(`document.querySelector('[data-booking-drawer]').open`),true);await close();return{};
 });
 for(const [width,height] of [[390,844],[844,390]])await check(`safe areas and menu ${width}`,async()=>{
  await b.viewport(width,height,true);await b.evaluate(`for(const [key,value] of Object.entries({'--safe-top':'24px','--safe-bottom':'34px','--safe-left':'24px','--safe-right':'24px'}))document.documentElement.style.setProperty(key,value)`);await b.settle();await click('[data-open-menu]');
  const row=await b.evaluate(`(()=>{const e=document.querySelector('[data-mobile-nav]'),r=e.getBoundingClientRect(),c=e.querySelector('.surface-content'),s=document.querySelector('.visit-section').getBoundingClientRect(),t=e.querySelector('.dock-toolbar').getBoundingClientRect();return{x:r.x,y:r.y,right:r.right,bottom:r.bottom,siteX:s.x,siteRight:s.right,controlsLeft:t.left,controlsRight:t.right,scroll:c.scrollHeight>c.clientHeight}})()`);assert.ok(row.x<=row.siteX&&row.right>=row.siteRight&&row.controlsLeft>=24&&row.controlsRight<=width-24&&row.y>=24&&row.bottom<=height-34);await key('Tab');assert.ok(await b.evaluate(`document.activeElement.closest('#mobile-menu')!==null`));await close();return row;
 });
 await check('fine-pointer mouse drags from actions without accidental activation',async()=>{
  await b.viewport(390,844,true);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});assert.ok(await b.evaluate(`matchMedia('(pointer:fine)').matches`));
  const rows=[];for(const [rail,action] of [['.team-grid','.team-card:first-child .team-book'],['.about-stack','.about-layer:first-child [data-about-more]']]){
   await b.evaluate(`document.querySelector('${rail}').scrollTo({left:0,behavior:'instant'})`);await b.center(action);const p=await b.point(action,.8,.5);await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
   for(let i=1;i<=12;i++){await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-140*i/12,y:p.y,button:'left',buttons:1});await b.pause(16);}
   const middle=await b.evaluate(`document.querySelector('${rail}').scrollLeft`);await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x-140,y:p.y,button:'left',buttons:0,clickCount:1});await b.until(`document.querySelector('${rail}').dataset.railSettling==='false'`);
   // A short drag from a small button may magnet back; it must still track and suppress activation.
   const left=await b.evaluate(`document.querySelector('${rail}').scrollLeft`);assert.ok(middle>100&&Math.abs(left-middle)>2,JSON.stringify({rail,p,middle,left,trace:await b.evaluate('window.__touchTrace.slice(-6)')}));assert.equal(await b.evaluate(`!!document.querySelector('dialog:modal')`),false);if(rail==='.about-stack')assert.equal(await b.evaluate(`document.querySelector('${action}').getAttribute('aria-expanded')`),'false');rows.push({rail,middle,left});
  }return{rows};
 });
 await check('article heading, menu and personal booking',async()=>{
  await b.viewport(390,844,true);await b.send('Page.navigate',{url:base+'masters/sofya-shalaginova/'});await b.until(`document.readyState==='complete'&&!!document.querySelector('[data-mobile-nav][data-section="article"]')`);await b.settle();
  assert.deepEqual(await b.evaluate(`(()=>{const s=getComputedStyle(document.querySelector('.story-heading h1'));return[s.fontSize,s.textAlign]})()`),['32px','center']);await click('[data-open-menu]');await key('Escape');await click('[data-action="article-booking"]');
  const row=await b.evaluate(`({open:document.querySelector('[data-booking-drawer]').open,url:document.querySelector('[data-booking-drawer]').dataset.bookingUrl,expected:document.querySelector('.story-actions [data-booking]').dataset.bookingUrl})`);assert.ok(row.open);assert.equal(new URL(row.url).hostname,new URL(row.expected).hostname.replace(/^n/,'b'));await close();assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);return row;
 });
}finally{await writeFile(`tmp/planning/${process.env.QA_REPORT_PREFIX||'iteration39'}-journeys.json`,JSON.stringify(report,null,2));await b.close();}
assert.deepEqual(report.failures,[]);console.log(`${report.cases.length} route/contrast/interaction cases passed`);
