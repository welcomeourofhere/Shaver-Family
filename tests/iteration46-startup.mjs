import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try{
 for(const width of [320,390,768,960]){
  await b.viewport(width,844,true);
  await b.send('Emulation.setScriptExecutionDisabled',{value:true});
  await b.send('Page.navigate',{url:base});await b.until(`document.readyState==='complete'`);
  const state=await b.evaluate(`(()=>{const dock=document.querySelector('[data-mobile-nav]'),buttons=[...dock.querySelectorAll('.dock-toolbar>button:not([hidden])')],rects=buttons.map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return{top:r.top,height:r.height,width:r.width,left:r.left,background:s.backgroundColor,color:s.color}});return{rects,height:dock.getBoundingClientRect().height}})()`);
  assert.equal(state.rects.length,3);assert.ok(state.rects.every(r=>Math.abs(r.top-state.rects[0].top)<1),JSON.stringify({width,state}));
  assert.equal(state.rects[1].background,'rgb(246, 232, 211)');assert.equal(state.rects[1].color,'rgb(75, 75, 77)');
  assert.equal(state.rects[2].background,'rgb(255, 204, 41)');assert.ok(state.height<=84,JSON.stringify({width,state}));
  await b.send('Emulation.setScriptExecutionDisabled',{value:false});await b.open(base);
  assert.equal(await b.evaluate(`document.querySelector('[data-mobile-nav]').dataset.stacked`),'false');
  console.log(`PASS initial panel before and after JavaScript ${width}`);
 }
 await b.viewport(390,844,false);
 await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 await b.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:400000,uploadThroughput:400000});
 await b.send('Emulation.setCPUThrottlingRate',{rate:4});
 await b.send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__dockStartup=[];const started=performance.now();function sampleDock(){const dock=document.querySelector('[data-mobile-nav]'),toolbar=dock?.querySelector('.dock-toolbar');if(dock&&toolbar&&getComputedStyle(dock).position==='fixed'&&getComputedStyle(toolbar).display==='grid'){const buttons=[...toolbar.querySelectorAll('button:not([hidden])')];__dockStartup.push({height:dock.getBoundingClientRect().height,tops:buttons.map(b=>b.getBoundingClientRect().top),colors:buttons.slice(1).map(b=>getComputedStyle(b).backgroundColor)});}if(performance.now()-started<5000)requestAnimationFrame(sampleDock)}requestAnimationFrame(sampleDock);`});
 await b.open(new URL('?startup=throttled#reviews',base).href);await b.pause(350);
 const frames=await b.evaluate('window.__dockStartup');assert.ok(frames.length>5);
 assert.ok(frames.every(f=>f.height<=84&&f.tops.every(top=>Math.abs(top-f.tops[0])<2)&&f.colors.every(color=>color!=='rgb(240, 240, 240)')),JSON.stringify(frames));
 console.log(`PASS throttled startup and restored section, ${frames.length} rendered frames`);
}finally{await b.send('Emulation.setScriptExecutionDisabled',{value:false});await b.close()}
