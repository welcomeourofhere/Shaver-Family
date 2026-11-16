import {mkdirSync,writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
import assert from 'node:assert/strict';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
mkdirSync('artifacts/iteration52',{recursive:true});
async function capture(name,selector,width,height){
 await b.viewport(width,height,true);await b.open(base);await b.send('Page.bringToFront');await b.center(selector);
 await b.until(`[...document.querySelectorAll(${JSON.stringify(selector+' img')})].every(i=>i.complete&&i.naturalWidth>0)`);
 await b.pause(selector.includes('contact')?2500:350);
 await shot(name,selector);
}
async function shot(name,selector){
 const clip=await b.evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height,scale:1}})()`);
 const {data}=await b.send('Page.captureScreenshot',{format:'jpeg',quality:90,captureBeyondViewport:true,clip});
 writeFileSync('artifacts/iteration52/'+name+'.jpg',Buffer.from(data,'base64'));console.log('CAPTURE '+name);
}
try{
 await capture('contacts-desktop','#contacts .contact-layout',1440,1500);
 await capture('contacts-phone','#contacts .contact-layout',390,1600);
 await capture('contacts-narrow','#contacts .contact-layout',320,1600);
 await capture('personal-contacts','#contacts .contact-stack',1440,1500);
 await capture('reviews-desktop','#reviews-rail',1440,1500);
 await capture('about-phone','[data-about-card]',390,1100);
 await b.evaluate(`document.querySelector('[data-about-more]').click()`);await b.settle();await shot('about-phone-reading','[data-about-card]');
 await capture('review-phone','#review-03',390,1000);
 await b.evaluate(`document.querySelector('#review-03 [data-review-read]').click()`);await b.settle();await shot('review-phone-reading','#review-03');
 await b.viewport(1440,1200,true);await b.open(base);await b.until(`document.querySelector('#reviews-rail').dataset.bentoReady==='true'`);
 await b.until(`!!document.querySelector('[data-review-composition="side"]')`);
 const selector=await b.evaluate(`'#'+document.querySelector('[data-review-composition="side"]').id`);
 await b.center(selector);await shot('review-horizontal',selector);
 await b.viewport(1440,1000,false);await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.open(base);
 assert.ok(await b.evaluate(`matchMedia('(hover:hover) and (pointer:fine)').matches`));
 const contrast=[];
 for(const selector of ['#contacts .contact-address','#contacts .contact-person-links a']){
  await b.center(selector);await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...await b.point(selector)});await b.pause(220);
  const row=await b.evaluate(`(()=>{const e=document.querySelector('${selector}'),s=getComputedStyle(e),bg=getComputedStyle(e.closest('article')).backgroundColor,ctx=document.createElement('canvas').getContext('2d');function rgb(c){ctx.fillStyle=c;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3)}function l(c){return rgb(c).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0)}const a=l(s.color),b=l(bg);return{color:s.color,background:bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}})()`);
  assert.ok(row.ratio>=4.5,JSON.stringify(row));contrast.push({selector,...row});
 }
 writeFileSync('tmp/planning/iteration52/contact-contrast.json',JSON.stringify(contrast,null,2));console.log('PASS yellow link contrast >=4.5 on red and blue');
}finally{await b.close()}
