import{mkdirSync,writeFileSync}from'node:fs';import{touchBrowser}from'./touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/',out='artifacts/iteration53';mkdirSync(out,{recursive:true});
async function shot(name,selector,width,height,theme='light',prepare){
 await b.viewport(width,height,true);await b.open(base);await b.send('Page.bringToFront');await b.evaluate(`document.querySelector('[data-theme-select]').value='${theme}';document.querySelector('[data-theme-select]').dispatchEvent(new Event('change',{bubbles:true}))`);
 if(prepare)await prepare();await b.center(selector);await b.pause(500);
 const clip=await b.evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height,scale:1}})()`);const{data}=await b.send('Page.captureScreenshot',{format:'jpeg',quality:90,captureBeyondViewport:true,clip});writeFileSync(out+'/'+name+'.jpg',Buffer.from(data,'base64'));console.log('CAPTURE '+name);
}
try{
 await shot('hero-phone','.hero-scene',390,844);
 await shot('promotions-phone','.hero-asides',390,1100);
 await shot('promotions-tablet','.hero-asides',768,1100);
 await shot('services-phone','#services',390,1050);
 await shot('menu-phone','.mobile-nav',390,844,'light',async()=>{await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle()});
 await shot('menu-dark','.mobile-nav',390,844,'dark',async()=>{await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle()});
 await shot('reviews-desktop','#reviews',1440,1500);
 await shot('reviews-phone','#review-03',390,900);
 await shot('about-phone','.about-layer:first-child',390,1000);
 await shot('contacts-desktop','#contacts .contact-layout',1440,1100);
 await shot('faq-desktop','#faq',1440,1100);
 await shot('faq-dark','#faq',768,1000,'dark',async()=>{await b.evaluate(`document.querySelector('.faq-item').open=true`)});
 await shot('interview-phone','.team-story-dialog',390,844,'light',async()=>{await b.evaluate(`const id=document.querySelector('.team-story-dialog').id.replace('team-dialog-','');document.querySelector('[data-team-open="'+id+'"]').click()`)});
}finally{await b.close()}
