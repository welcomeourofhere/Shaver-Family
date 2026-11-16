import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',report=[];
mkdirSync('tmp/planning/iteration55',{recursive:true});
const geometry=`(()=>Object.fromEntries(['.hero-scene','.hero-lead','.hero-brand','.hero-heading','.hero-mobile-copy','.hero-asides','.first-visit','.cashback','.sd-stack','.team-grid','.visit-ticket','.about-stack','.about-media','.gifts-grid','.reviews-rail','#faq','#contacts'].map(s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return[s,{height:r.height,width:r.width,top:r.top+scrollY,left:r.left}]})))()`;
function same(before,after,width,noScript=false){for(const selector of Object.keys(before))for(const property of ['height','width','top','left']){if(noScript&&(selector==='#faq'&&property==='height'||selector==='#contacts'&&property==='top'))continue;assert.ok(Math.abs(before[selector][property]-after[selector][property])<1.1,JSON.stringify({width,selector,property,before:before[selector],after:after[selector]}));}}
async function check(name,fn){try{const evidence=await fn();report.push({name,pass:true,evidence});console.log('PASS '+name)}catch(error){report.push({name,pass:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}}
try{
 for(const [width,height,reduced] of [[320,844,true],[390,844,true],[600,900,true],[768,1000,true],[960,1000,true],[961,1000,true],[1024,1000,true],[1440,1000,true],[390,390,false],[1024,1000,false],[1440,1000,false]])await check(`one initial layout with and without JavaScript ${width}x${height} reduced=${reduced}`,async()=>{
  await b.viewport(width,height,reduced);await b.send('Emulation.setScriptExecutionDisabled',{value:true});await b.send('Page.navigate',{url:base});await b.until(`document.readyState==='complete'`);await b.evaluate('document.fonts.ready');const before=await b.evaluate(geometry);
  await b.send('Emulation.setScriptExecutionDisabled',{value:false});await b.open(base);await b.until(`document.querySelector('[data-review-bento]').dataset.bentoReady==='true'`);await b.pause(80);const after=await b.evaluate(geometry);same(before,after,width,true);
  const rail=await b.evaluate(`(()=>{const r=document.querySelector('[data-review-bento]');return{ready:r.dataset.bentoReady,busy:r.getAttribute('aria-busy'),loader:getComputedStyle(document.querySelector('.review-layout-loader')).display,errors:__touchErrors}})()`);assert.equal(rail.ready,'true');assert.equal(rail.busy,'false');assert.equal(rail.loader,'none');assert.deepEqual(rail.errors,[]);return{before,after,rail};
 });
 for(const width of [390,768,1024,1440])await check(`deferred scripts keep reserved geometry and expose only the finished review layout ${width}`,async()=>{
  await b.viewport(width,900,true);await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
  let released=false;const held=[];const off=b.on('Fetch.requestPaused',event=>{if(released)void b.send('Fetch.continueRequest',{requestId:event.requestId});else held.push(event.requestId)});
  await b.send('Fetch.enable',{patterns:[{urlPattern:'*.js*',resourceType:'Script',requestStage:'Request'}]});
  try{
   await b.send('Page.navigate',{url:base});await b.until(`!!document.querySelector('#contacts')&&getComputedStyle(document.querySelector('.sd-stack')).display==='grid'`);await b.evaluate('document.fonts.ready');await b.pause(100);
   const before=await b.evaluate(geometry),pending=await b.evaluate(`({card:getComputedStyle(document.querySelector('.review-card')).visibility,loader:getComputedStyle(document.querySelector('.review-layout-loader')).display})`);assert.ok(held.length>0);assert.equal(pending.card,'hidden');assert.equal(pending.loader,'grid');
   released=true;for(const requestId of held)await b.send('Fetch.continueRequest',{requestId});await b.until(`document.readyState==='complete'&&document.querySelector('[data-review-bento]').dataset.bentoReady==='true'`);await b.settle();const after=await b.evaluate(geometry);same(before,after,width);
   assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('.review-card')).visibility`),'visible');assert.deepEqual(await b.evaluate('__touchErrors'),[]);return{before,after,pending,held:held.length};
  }finally{released=true;off();await b.send('Fetch.disable');}
 });
 await check('red-circle icon is delivered on every page and preserves the original wordmark',async()=>{
  const evidence=[];for(const path of ['/','/masters/sofya-shalaginova/','/previews/contacts/','/previews/contacts/overview/','/previews/review-extras/']){
   await b.send('Page.navigate',{url:new URL(path,base).href});await b.until(`document.readyState==='complete'`);const icon=await b.evaluate(`(()=>{const link=document.querySelector('link[rel="icon"]');return{href:link.getAttribute('href'),type:link.type}})()`);assert.equal(icon.href,'/brand/favicon-red.svg');assert.equal(icon.type,'image/svg+xml');evidence.push({path,...icon});
  }
  const icon=await b.evaluate(`fetch('/brand/favicon-red.svg').then(r=>r.text()).then(t=>{const doc=new DOMParser().parseFromString(t,'image/svg+xml'),circle=doc.querySelector('circle');return{viewBox:doc.documentElement.getAttribute('viewBox'),fill:circle.getAttribute('fill'),radius:circle.getAttribute('r'),paths:doc.querySelectorAll('path').length}})`);assert.equal(icon.viewBox,'0 0 256 256');assert.equal(icon.fill,'#c42f2a');assert.equal(icon.radius,'128');assert.ok(icon.paths>0);return{pages:evidence,icon};
 });
 for(const [width,height]of[[320,844],[390,844],[768,1024],[960,600],[390,390]])await check(`compact video hero logo is centred, spaced and separate from the caption ${width}x${height}`,async()=>{
  await b.viewport(width,height,true);await b.open(base);
  for(const scale of [1,2]){
   if(scale===2)await b.evaluate(`for(const e of document.querySelectorAll('.hero-heading,.hero-mobile-copy'))e.style.fontSize=parseFloat(getComputedStyle(e).fontSize)*2+'px'`);
   await b.settle();const state=await b.evaluate(`(()=>{const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}},brand=document.querySelector('.hero-brand'),scene=document.querySelector('.hero-scene'),heading=document.querySelector('.hero-heading');return{brand:rect(brand),scene:rect(scene),heading:rect(heading),copy:rect(document.querySelector('.hero-mobile-copy')),display:getComputedStyle(brand).display,video:getComputedStyle(scene.querySelector('video')).display,logo:brand.querySelector('img').complete,legacy:scene.closest('.hero').style.getPropertyValue('--hero-min-height')}})()`);assert.equal(state.display,'block');assert.ok(state.logo);assert.ok(Math.abs(state.brand.x+state.brand.w/2-width/2)<.6);assert.ok(state.brand.y>=31.9);assert.ok(state.heading.y>=state.brand.bottom+31);assert.ok(state.copy.bottom<state.scene.bottom-60);assert.equal(state.video,'block');assert.equal(state.legacy,'');
  }
  return{width,height,scales:[1,2]};
 });
 await check('the caption reserves the actual dock when all interface text is enlarged to 200 percent',async()=>{
  await b.viewport(390,844,true);await b.open(base);await b.evaluate(`(()=>{const runs=[...document.querySelectorAll('body *')].filter(e=>!e.closest('svg,script,style')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const[e,size]of runs)e.style.fontSize=2*size+'px';})()`);await b.settle();await b.pause(150);
  const state=await b.evaluate(`(()=>{const scene=document.querySelector('.hero-scene').getBoundingClientRect(),copy=document.querySelector('.hero-mobile-copy').getBoundingClientRect(),dock=document.querySelector('.mobile-nav').getBoundingClientRect();return{height:scene.height,bottom:copy.bottom,dockHeight:dock.height,dockTop:dock.top}})()`);assert.ok(state.height-state.bottom>=state.dockHeight+20,JSON.stringify(state));return state;
 });
}finally{await b.send('Emulation.setScriptExecutionDisabled',{value:false});writeFileSync('tmp/planning/iteration55/startup.json',JSON.stringify({report,published:false},null,2));await b.close();}
assert.ok(report.every(row=>row.pass),'Initial-layout regressions failed');
