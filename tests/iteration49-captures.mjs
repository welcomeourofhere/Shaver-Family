import {mkdirSync,writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
process.env.QA_BROWSER_SESSION='soyuz49-touch';process.env.QA_BROWSER_SOCKET_DIR='.local/browser-qa49';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
mkdirSync('artifacts/iteration49',{recursive:true});
const shot=async name=>{const r=await b.send('Page.captureScreenshot',{format:'png'});writeFileSync(`artifacts/iteration49/${name}.png`,Buffer.from(r.data,'base64'));};
try{
 await b.send('Network.enable');await b.send('Network.clearBrowserCache');await b.send('Network.setCacheDisabled',{cacheDisabled:true});
 for(const width of [390,1440]){
  await b.viewport(width,1000,true);await b.open(base);await b.evaluate(`(()=>{const s=document.querySelector('[data-theme-select]');s.value='light';s.dispatchEvent(new Event('change',{bubbles:true}))})()`);await b.settle();
  await b.evaluate(`document.querySelector('#reviews').scrollIntoView({block:'start',behavior:'instant'})`);await b.pause(500);await shot(`reviews-${width}`);
  if(width===390){
   await b.evaluate(`document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();await shot('interview-mobile');
   await b.evaluate(`document.querySelector('dialog[open] [data-dismiss]').click()`);await b.settle();
   await b.center('.sd-tabs');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='services'`);await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle();await shot('menu-mobile');await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle();
   await b.evaluate(`location.hash='#offer-first-visit'`);await b.until(`document.querySelector('#offer-first-visit').dataset.offerActive==='true'`);await b.center('#offer-first-visit .info-trigger');await b.tap(await b.point('#offer-first-visit .info-trigger'));await b.until(`document.querySelector('#offer-first-visit .info-panel').matches(':popover-open')`);await shot('offer-note-mobile');
   const tip=await b.evaluate(`(()=>{const c=document.querySelector('#offer-first-visit'),a=getComputedStyle(c.querySelector('.of-action')),b=getComputedStyle(c.querySelector('.info-trigger')),p=getComputedStyle(c.querySelector('.info-panel')),i=getComputedStyle(c.querySelector('.info-trigger>span'));return{action:a.backgroundColor,trigger:b.backgroundColor,popup:p.backgroundColor,ring:i.borderWidth}})()`);console.log('tip',JSON.stringify(tip));
   await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
   await b.center('#review-07 [data-review-video-play]');await b.tap(await b.point('#review-07 [data-review-video-play]'));await b.until(`document.querySelector('#review-07 video')?.readyState>=2`);await b.evaluate(`document.querySelector('#review-07 video').pause();document.querySelector('#review-07 video').currentTime=3`);await b.pause(200);await b.center('.review-video-frame');await shot('review-video-mobile');
  }
  await b.evaluate(`document.querySelector('#contacts').scrollIntoView({block:'start',behavior:'instant'})`);await b.pause(15000);await shot(`contacts-${width}`);
  console.log('captured',width);
 }
}finally{await b.close()}
