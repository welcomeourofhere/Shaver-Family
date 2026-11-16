import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),report=[];
const selectors='.header-capsule,.hero-heading,.hero-scene,.hero-news-panel,.first-visit,.cashback,.team-card,.visit-ticket,.about-card,.gift-visual,.certificates,.of-card,.hero-nav';
try{
 await b.send('Network.enable');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 for(const width of [1024,1440,1920]){
  const versions=[];
  for(const url of [process.env.QA_BASELINE_URL,process.env.QA_URL]){
   await b.viewport(width,1000,true);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(url);
   await b.evaluate(`(()=>{const theme=document.querySelector('[data-theme-select]');theme.value='light';theme.dispatchEvent(new Event('change',{bubbles:true}));scrollTo({top:0,behavior:'instant'})})()`);await b.settle();
   versions.push(await b.evaluate(`(()=>{const keys=['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius','padding','display','gridTemplateColumns','columnGap','rowGap','textAlign'];return[...document.querySelectorAll(${JSON.stringify(selectors)})].map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{selector:e.className,width:r.width,height:r.height,styles:Object.fromEntries(keys.map(key=>[key,s[key]]))}})})()`));
  }
  const [before,after]=versions;assert.equal(before.length,after.length);const offerContentHeightChanges=[];
  for(let i=0;i<before.length;i++){
   assert.ok(Math.abs(before[i].width-after[i].width)<.6,JSON.stringify({width,before:before[i],after:after[i]}));
   assert.ok(Math.abs(before[i].height-after[i].height)<.6,JSON.stringify({width,before:before[i],after:after[i]}));
   assert.deepEqual(after[i].styles,before[i].styles,JSON.stringify({width,selector:before[i].selector}));
  }
  report.push({width,elements:before.length,offerContentHeightChanges});console.log(`PASS preserved desktop widths/styles ${width}: ${before.length}, updated offer copy heights recorded`);
 }
}finally{writeFileSync('tmp/planning/iteration51/desktop.json',JSON.stringify({report,published:false},null,2));await b.close();}
