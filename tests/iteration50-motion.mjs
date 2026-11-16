import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try{
 for(const width of [320,390,768]) for(const section of ['top','offers']){
  await b.viewport(width,844,false);await b.open(base);await b.send('Page.bringToFront');
  if(section==='offers'){await b.center('.of-rail');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='offers'`);await b.settle();}
  for(const opening of [true,false]){
   const p=await b.point('[data-open-menu]');
   await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
   await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',buttons:0,clickCount:1});
   const frames=await b.evaluate(`(async()=>{const rows=[],end=performance.now()+550;do{const d=document.querySelector('[data-mobile-nav]'),r=d.querySelector('.dock-shell').getBoundingClientRect(),buttons=[...d.querySelectorAll('.dock-toolbar button:not([hidden])')].map(e=>{const x=e.getBoundingClientRect();return{top:x.top,bottom:x.bottom,left:x.left,right:x.right}});rows.push({top:r.top,bottom:r.bottom,left:r.left,right:r.right,buttons});await new Promise(requestAnimationFrame)}while(performance.now()<end);return rows})()`);
   assert.ok(frames.length>5,JSON.stringify({width,section,opening,frames:frames.length,visibility:await b.evaluate('document.visibilityState')}));
   const escaped=frames.find(f=>f.buttons.some(x=>x.left<f.left-3||x.right>f.right+3||x.top<f.top-3||x.bottom>f.bottom+3));
   assert.ok(!escaped,`toolbar escaped background ${width} ${section} ${opening?'opening':'closing'}: ${JSON.stringify(escaped)}`);
   assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),opening);
  }
  console.log(`PASS dock deformation ${width} ${section}`);
 }
}finally{await b.close()}
