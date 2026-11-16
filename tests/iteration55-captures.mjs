import{mkdirSync,writeFileSync}from'node:fs';import{touchBrowser}from'./touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',out='artifacts/iteration55';mkdirSync(out,{recursive:true});
async function shot(name,selector,width,height,theme='light',prepare){
 await b.viewport(width,height,true);await b.open(base);await b.send('Page.bringToFront');await b.evaluate(`document.querySelector('[data-theme-select]').value='${theme}';document.querySelector('[data-theme-select]').dispatchEvent(new Event('change',{bubbles:true}))`);
 const cleanup=prepare?await prepare():undefined;if(selector==='.hero-scene')await b.evaluate(`scrollTo({top:0,behavior:'instant'})`);else if(!cleanup)await b.center(selector);await b.pause(cleanup?30:500);
 const heldIndex=name==='live-indicator-mouse'?await b.evaluate(`document.querySelector('#masters-rail').dataset.railIndex`):null;
 if(heldIndex!==null&&heldIndex!=='1')throw Error('The held indicator must still show the second card before capture');
 const{data}=await b.send('Page.captureScreenshot',{format:'jpeg',quality:90,captureBeyondViewport:false});writeFileSync(out+'/'+name+'.jpg',Buffer.from(data,'base64'));if(cleanup)await cleanup();console.log('CAPTURE '+name);
}
try{
 await shot('hero-phone','.hero-scene',390,844);
 await shot('hero-tablet','.hero-scene',768,1024);
 await shot('promotions-phone','.hero-asides',390,1100);
 await shot('promotions-tablet','.hero-asides',768,1100);
 await shot('services-phone','#services',390,1050);
 await shot('services-narrow','#services',320,1100);
 await shot('fair-price-phone','#first-visit',390,1000);
 await shot('fair-price-tablet','#first-visit',768,1000);
 await shot('offers-pc-drag','.of-slider',1440,1000,'light',async()=>{await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});await b.center('.of-rail');const p=await b.point('.of-rail',.5,.35);await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1});for(const dx of[15,100])await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-dx,y:p.y,button:'left',buttons:1});if(!await b.evaluate(`document.querySelector('.of-rail').classList.contains('is-dragging')`))throw Error('Offer capture requires a held drag');return()=>b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x-100,y:p.y,button:'left',buttons:0});});
 await shot('menu-phone','.mobile-nav',390,844,'light',async()=>{await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle()});
 await shot('menu-dark','.mobile-nav',390,844,'dark',async()=>{await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle()});
 await shot('reviews-desktop','#reviews',1440,1500);
 await shot('reviews-phone','#review-03',390,900);
 await shot('about-phone','.about-layer:first-child',390,1000);
 await shot('live-indicator-mouse','#masters',390,1000,'light',async()=>{await b.send('Emulation.setTouchEmulationEnabled',{enabled:false});await b.center('#masters-rail');const p=await b.point('#masters-rail',.88,.3),end={x:p.x-190,y:p.y};await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1});for(const dx of[12,190])await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-dx,y:p.y,button:'left',buttons:1});if(await b.evaluate(`document.querySelector('#masters-rail').dataset.railIndex`)!=='1')throw Error('Live indicator capture requires selection during the held drag');return()=>b.send('Input.dispatchMouseEvent',{type:'mouseReleased',...end,button:'left',buttons:0});});
 await shot('contacts-desktop','#contacts .contact-layout',1440,1100);
 await shot('faq-desktop','#faq',1440,1100);
 await shot('faq-dark','#faq',768,1000,'dark',async()=>{await b.evaluate(`document.querySelector('.faq-item').open=true`)});
 await shot('interview-phone','.team-story-dialog',390,844,'light',async()=>{await b.evaluate(`const id=document.querySelector('.team-story-dialog').id.replace('team-dialog-','');document.querySelector('[data-team-open="'+id+'"]').click()`)});
 await b.viewport(256,256,true);await b.send('Page.navigate',{url:new URL('/brand/favicon-red.svg',base).href});await b.until(`document.readyState==='complete'&&document.documentElement.nodeName==='svg'`);const icon=await b.send('Page.captureScreenshot',{format:'png'});writeFileSync(out+'/favicon-red.png',Buffer.from(icon.data,'base64'));console.log('CAPTURE favicon-red');
}finally{await b.close()}
