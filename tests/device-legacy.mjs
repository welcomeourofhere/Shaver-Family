/** Actual older engines, isolated tool install; no application dependency or personal profile.
 * QA_LEGACY_PLAYWRIGHT points to Playwright 1.35.1 (WebKit 16.4 / Firefox 113).
 * node tests/device-legacy.mjs [--phase 57]
 */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile,readdir} from 'node:fs/promises';
import {resolve,relative,extname,sep} from 'node:path';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
const root=resolve('.'),phase=process.argv.includes('--phase')?Number(process.argv[process.argv.indexOf('--phase')+1]):57;
const folder=resolve(root,'dist'),out=resolve(root,`tmp/planning/iteration${phase}`),shots=resolve(root,`artifacts/iteration${phase}`);
const require=createRequire(import.meta.url),pw=require(process.env.QA_LEGACY_PLAYWRIGHT||resolve(tmpdir(),'soyuz-compat-browser-tools/node_modules/playwright'));
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.woff2':'font/woff2','.ttf':'font/ttf','.mp4':'video/mp4'};
async function digest(dir){
 const files=[];async function walk(path){for(const entry of await readdir(path,{withFileTypes:true})){const file=resolve(path,entry.name);if(entry.isDirectory())await walk(file);else if(entry.isFile())files.push(file)}}await walk(dir);
 // Same lowercase path-component ordering as the Python evidence runners, on every OS.
 files.sort((a,b)=>{const ap=relative(dir,a).split(sep).map(s=>s.toLowerCase()),bp=relative(dir,b).split(sep).map(s=>s.toLowerCase());for(let i=0;i<Math.min(ap.length,bp.length);i++)if(ap[i]!==bp[i])return ap[i]<bp[i]?-1:1;return ap.length-bp.length});
 const h=createHash('sha256');for(const file of files){h.update(relative(dir,file).split(sep).join('/'));h.update(createHash('sha256').update(await readFile(file)).digest())}return h.digest('hex');
}
const before=await digest(folder),results=[];await mkdir(out,{recursive:true});await mkdir(shots,{recursive:true});
const newsEndpoint=JSON.parse(await readFile(resolve(root,'content/site.json'),'utf8')).newsFeedUrl;
const server=createServer(async(req,res)=>{try{let file=resolve(folder,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));if(file!==folder&&!file.startsWith(folder+sep)){res.writeHead(403).end();return}if(!extname(file))file=resolve(file,'index.html');const body=await readFile(file);res.writeHead(200,{'Content-Type':mime[extname(file)]||'application/octet-stream'});res.end(body)}catch{res.writeHead(404).end()}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}/`;
const openState=el=>el.hasAttribute('data-popover-open');
async function settled(page){await page.evaluate(()=>document.fonts.ready);await page.waitForFunction(()=>document.querySelector('[data-review-bento]')?.dataset.bentoReady==='true',{},{timeout:10000});await page.waitForTimeout(100)}
async function check(name,fn){try{results.push({name,passed:true,evidence:await fn()});console.log('PASS '+name)}catch(error){results.push({name,passed:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}}
try{
 for(const engine of (process.argv.includes('--quick')?['webkit']:['webkit','firefox'])){
  const browser=await pw[engine].launch();
  try{
   for(const [width,height,dpr]of (process.argv.includes('--quick')?[[390,844,3]]:[[390,844,3],[768,1024,2],[1440,900,1]]))await check(`${engine} ${browser.version()} ${width}x${height} DPR${dpr}`,async()=>{
    const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:dpr,reducedMotion:'no-preference',...(engine==='webkit'?{isMobile:width<=960,hasTouch:width<=960}:{})});
    await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
    // Exercise clipboard denial as well; do not write to the user's clipboard.
    await context.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('QA permission denied'))},configurable:true}));
    const page=await context.newPage(),errors=[];let stage='startup';page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));
    try{
     await page.goto(base,{waitUntil:'domcontentloaded'});await settled(page);
     const features=await page.evaluate(()=>{const y=scrollY;scrollTo({left:1e6,top:y,behavior:'instant'});const horizontal=scrollX;scrollTo({left:0,top:y,behavior:'instant'});const c=document.createElement('canvas').getContext('2d');c.font='400 16px Manrope';return{popover:typeof HTMLElement.prototype.showPopover,linear:CSS.supports('animation-timing-function','linear(0,1)'),abortAny:typeof AbortSignal.any,ease:getComputedStyle(document.documentElement).getPropertyValue('--ease-spring').trim(),overflow:document.documentElement.scrollWidth-innerWidth,maxHorizontalScroll:horizontal,spaceWidth:c.measureText(' ').width,nbspWidth:c.measureText('\u00a0').width,dpr:devicePixelRatio}});
     assert.equal(features.popover,'undefined');assert.ok(features.overflow<=1&&features.maxHorizontalScroll<=1,JSON.stringify(features));assert.ok(Math.abs(features.spaceWidth-features.nbspWidth)<.02);assert.equal(features.dpr,dpr);if(!features.linear)assert.match(features.ease,/^cubic-bezier/);
     if(width<=960){stage='theme';
      await page.locator('[data-open-menu]').click();await page.waitForFunction(()=>document.querySelector('#mobile-menu').open);
      const trigger=page.locator('#mobile-menu .choice-trigger'),listId=await trigger.getAttribute('aria-controls'),list=page.locator('#'+listId);
      await trigger.click();await page.waitForFunction(id=>document.getElementById(id).hasAttribute('data-popover-open'),listId);
      const geometry=await list.evaluate(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,h:r.height,dialog:!!e.closest('dialog[open]')}});
      assert.ok(geometry.dialog&&geometry.x>=0&&geometry.right<=width+1&&geometry.bottom<=height+1&&geometry.h<220,JSON.stringify(geometry));
      if(width===390){await list.evaluate(e=>Promise.allSettled(e.getAnimations().filter(a=>Number.isFinite(a.effect?.getTiming().iterations)).map(a=>a.finished)));await page.screenshot({path:resolve(shots,`legacy-${engine}-${width}-menu.png`)})}
      await trigger.click();assert.equal(await list.evaluate(openState),false);
      await trigger.click();await page.keyboard.press('Escape');assert.equal(await list.evaluate(openState),false);assert.equal(await page.locator('#mobile-menu').evaluate(e=>e.open),true);
      await trigger.click();await list.locator('[data-value="dark"]').click();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
      await trigger.focus();await page.keyboard.press('ArrowDown');await page.keyboard.press('Home');await page.keyboard.press('Enter');assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
      await trigger.click();await page.locator('#menu-title').click();assert.equal(await list.evaluate(openState),false);
      await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.querySelector('#mobile-menu').open);
      stage='toast';await page.evaluate(()=>document.querySelector('#promo-dialog').showModal());
      await page.locator('#promo-dialog [data-copy-promo]').click();await page.waitForFunction(()=>document.querySelector('[data-toast]').classList.contains('is-visible'));
      assert.match(await page.locator('[data-toast-message]').textContent(),/Не\sудалось скопировать/);
      assert.equal(await page.locator('[data-toast]').evaluate(e=>!!e.closest('dialog[open]')),true);
      await page.waitForFunction(()=>!document.querySelector('[data-toast]').hasAttribute('data-popover-open'));
      await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.querySelector('#promo-dialog').open);
     }
     stage='tooltip';const tip=page.locator('.info-tip-compact[data-info-tip]').first(),button=tip.locator('button');
     await button.evaluate(e=>e.scrollIntoView({block:'center',inline:'center',behavior:'instant'}));await page.mouse.move(1,1);
     // Tooltip dismissal during a still-moving rail is intentional. Open it after native snap settles.
     await page.evaluate(()=>new Promise((resolve,reject)=>{const rail=document.getElementById('offers-rail');let previous=rail.scrollLeft,quiet=performance.now(),start=quiet;const scrolled=()=>quiet=performance.now();rail.addEventListener('scroll',scrolled,{passive:true});function tick(now){const left=rail.scrollLeft;if(Math.abs(left-previous)>.1||rail.dataset.railSettling==='true')quiet=now;previous=left;if(now-quiet>=200){rail.removeEventListener('scroll',scrolled);resolve()}else if(now-start>4000){rail.removeEventListener('scroll',scrolled);reject(Error('native rail did not settle'))}else requestAnimationFrame(tick)}requestAnimationFrame(tick)}));
     await button.evaluate(e=>{if(e.getAttribute('aria-expanded')!=='true')e.click()});
     const id=await button.getAttribute('aria-describedby'),panel=page.locator('#'+id);await page.waitForFunction(id=>document.getElementById(id).hasAttribute('data-popover-open'),id);
     const colors=await page.evaluate(id=>{const panel=document.getElementById(id),trigger=document.querySelector(`[aria-describedby="${id}"]`);return{panel:getComputedStyle(panel).backgroundColor,trigger:getComputedStyle(trigger).backgroundColor}},id);
     assert.equal(colors.panel,colors.trigger);await page.keyboard.press('Escape');assert.equal(await panel.evaluate(openState),false,'Escape closes the tooltip without focus reopening it');
     stage='services';for(const index of [1,2,3,4,0]){await page.locator(`[data-sd-tab="${index}"]`).click();await page.waitForFunction(()=>document.querySelector('[data-service-deck]').dataset.deckMoving==='false');assert.equal(await page.locator(`[data-sd-tab="${index}"]`).getAttribute('aria-selected'),'true')}
     await page.locator('.faq-item summary').first().click();assert.equal(await page.locator('.faq-item').first().evaluate(e=>e.open),true);
     stage='hours';const hours=page.locator('#contacts .business-hours button');
     await hours.scrollIntoViewIfNeeded();await hours.click();
     const hoursId=await hours.getAttribute('aria-describedby'),hoursPanel=page.locator('#'+hoursId);
     await page.waitForFunction(id=>document.getElementById(id).hasAttribute('data-popover-open'),hoursId);
     const hoursBounds=await hoursPanel.evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,visible:getComputedStyle(e).display!=='none'}});
     assert.ok(hoursBounds.visible&&hoursBounds.left>=0&&hoursBounds.right<=width+1&&hoursBounds.top>=0&&hoursBounds.bottom<=height+1,JSON.stringify(hoursBounds));
     assert.match(await hoursPanel.textContent(),/без\sобеда/);await page.keyboard.press('Escape');assert.equal(await hoursPanel.evaluate(openState),false);
     stage='rotation';if(width<=960){
      await page.setViewportSize({width:height,height:width});await page.waitForTimeout(120);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=1));
      await page.setViewportSize({width,height});
     }
     await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(200);await page.screenshot({path:resolve(shots,`legacy-${engine}-${width}.png`)});
     assert.deepEqual(errors,[]);return{features,errors};
    }catch(error){await page.screenshot({path:resolve(shots,`legacy-${engine}-${width}-failure.png`)});throw new Error(stage+': '+error.message+'; errors='+JSON.stringify(errors))}finally{await context.close()}
   });
   await check(`${engine} desktop news without AbortSignal.any/timeout`,async()=>{
    const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    let feed=JSON.parse(await readFile(resolve(root,'content/news.json'),'utf8')),requests=0,delayed=false;
    await context.route('**/*',async route=>{
     const url=route.request().url(),address=new URL(url);
     if(url===newsEndpoint||url.startsWith(base)&&address.pathname==='/data/news.json'){
      requests++;if(delayed){await new Promise(r=>setTimeout(r,150));return route.abort().catch(()=>{})}
      return route.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(feed)});
     }
     if(address.hostname==='raw.githubusercontent.com'&&address.pathname.includes('/media/news/')){
      const name=address.pathname.split('/').at(-1);assert.match(name,/^[\da-f-]+\.webp$/);
      return route.fulfill({status:200,contentType:'image/webp',body:await readFile(resolve(root,'public/media/news',name))});
     }
     return url.startsWith(base)?route.continue():route.abort();
    });
    try{
     feed={...feed,generatedAt:'2034-01-01T00:00:00+03:00'};await page.goto(base,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelector('.hero-scene').dataset.newsRevision==='2034-01-01T00:00:00+03:00');
     delayed=true;await page.evaluate(()=>{document.documentElement.style.setProperty('--hero-news-refresh-timeout','20');document.dispatchEvent(new Event('visibilitychange'))});await page.waitForTimeout(220);assert.equal(await page.locator('.hero-scene').getAttribute('data-news-revision'),'2034-01-01T00:00:00+03:00');
     delayed=false;feed={...feed,generatedAt:'2035-01-01T00:00:00+03:00'};await page.evaluate(()=>{document.documentElement.style.removeProperty('--hero-news-refresh-timeout');document.dispatchEvent(new Event('visibilitychange'))});await page.waitForFunction(()=>document.querySelector('.hero-scene').dataset.newsRevision==='2035-01-01T00:00:00+03:00');assert.ok(requests>=3);assert.deepEqual(errors,[]);return{requests,errors};
    }finally{await context.close()}
   });
  }finally{await browser.close()}
 }
}finally{
 server.closeAllConnections?.();await new Promise(r=>server.close(r));const after=await digest(folder);
 await writeFile(resolve(out,process.argv.includes('--quick')?'legacy-quick.json':'legacy.json'),JSON.stringify({cases:results,buildSha256:before,unchanged:before===after,externalRequestsBlocked:true,physicalDevices:false,published:false},null,2));assert.equal(before,after);
}
assert.equal(results.length,process.argv.includes('--quick')?2:8);assert.ok(results.every(row=>row.passed),'Legacy compatibility failed');
