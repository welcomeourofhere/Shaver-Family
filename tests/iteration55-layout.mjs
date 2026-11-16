import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),report={cases:[],failures:[],published:false};
const base=process.env.QA_URL||'http://127.0.0.1:4321/';
async function check(name,run){try{const data=await run();report.cases.push({name,...data});console.log('PASS '+name)}catch(error){report.failures.push({name,error:error.message});console.log('FAIL '+name+': '+error.message)}}
const audit=`(()=>{const bad=[],range=document.createRange();for(const e of document.querySelectorAll('button,.btn,.footer-groups a')){const r=e.getBoundingClientRect(),s=getComputedStyle(e);if(!r.width||!r.height||s.visibility==='hidden'||e.closest('[hidden],[inert],dialog:not([open])'))continue;if(r.height<43.9)bad.push('hit:'+e.className);if(e.matches('.hero-edge,.hero-dot,.icon-btn,.info-trigger,.certificate-object,.gift-visual,.dock-menu')||e.querySelector('img')||!e.textContent.trim())continue;if(e.scrollWidth>e.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push('label:'+e.className+':'+e.textContent.trim());const walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);while(walk.nextNode()){if(!walk.currentNode.textContent.trim()||!walk.currentNode.parentElement.getClientRects().length)continue;range.selectNodeContents(walk.currentNode);if(range.getClientRects().length>1)bad.push('wrap:'+walk.currentNode.textContent)}}const dock=document.querySelector('[data-mobile-nav]'),r=dock.getBoundingClientRect();return{bad,overflow:document.documentElement.scrollWidth>innerWidth+1,errors:window.__touchErrors,dock:{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom,count:Number(dock.dataset.actionCount),suppressed:dock.dataset.suppressed}}})()`;
async function inspect(){const row=await b.evaluate(audit);assert.deepEqual(row.bad,[]);assert.deepEqual(row.errors,[]);assert.equal(row.overflow,false);const shell=await b.evaluate(`(()=>{const r=document.querySelector('.visit-section').getBoundingClientRect(),s=getComputedStyle(document.documentElement),width=Math.min(parseFloat(s.getPropertyValue('--size-1160'))+parseFloat(s.getPropertyValue('--size-16')),innerWidth-parseFloat(s.getPropertyValue('--size-8')));return{x:r.x,w:r.width,expected:width,left:(innerWidth-width)/2}})()`);assert.ok(Math.abs(row.dock.x-shell.left)<.5&&Math.abs(row.dock.w-shell.expected)<.5&&row.dock.w>=shell.w,JSON.stringify({dock:row.dock,shell}));return row;}
async function click(selector){await b.evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);await b.settle();}
async function key(key,code=key){const windowsVirtualKeyCode={Escape:27,Enter:13,ArrowDown:40,ArrowUp:38,End:35,Home:36,Tab:9,' ':32}[key]||0;await b.send('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});await b.settle();}
try{
 for(const [width,height] of [[320,740],[360,800],[390,844],[540,960],[560,960],[600,960],[620,960],[650,960],[768,1000],[834,1000],[960,1000],[844,390]]){
  await b.viewport(width,height,true);await b.open(base);
  for(const theme of ['light','dark'])await check(`layout ${width}x${height} ${theme}`,async()=>{
   await b.evaluate(`(()=>{const e=document.querySelector('[data-theme-select]');e.value='${theme}';e.dispatchEvent(new Event('change',{bubbles:true}))})()`);await b.settle();
   const heads=await b.evaluate(`(()=>[...document.querySelectorAll('main .headline,.hero-heading')].map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{id:e.id,size:s.fontSize,weight:s.fontWeight,align:s.textAlign,width:e.clientWidth,scroll:e.scrollWidth,center:r.left+r.width/2,primary:e.matches('.section-title')}}))()`);
   assert.ok(heads.every(h=>h.size==='40px'&&h.weight==='400'&&h.align==='center'&&h.scroll<=h.width+1),JSON.stringify(heads));
   assert.ok(heads.filter(h=>h.primary).every(h=>Math.abs(h.center-width/2)<1),JSON.stringify(heads));
   const hero=await b.evaluate(`(()=>{const e=document.querySelector('.hero-brand');return{brand:getComputedStyle(e).display,title:document.querySelector('.hero-heading-mobile').textContent,address:!!document.querySelector('.hero-mobile-address')}})()`);
   assert.equal(hero.brand,'block');assert.equal(hero.title,'Барбершоп СОЮЗ');assert.equal(hero.address,false);
   const promo=await b.evaluate(`(()=>{const parent=document.querySelector('.hero-asides').getBoundingClientRect(),shell=document.querySelector('#first-visit').getBoundingClientRect(),cards=[...document.querySelector('.hero-asides').children].map(e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}});return{parent:{x:parent.x,w:parent.width},shell:{x:shell.x,w:shell.width},cards}})()`);
   assert.ok(Math.abs(promo.parent.w-promo.shell.w)<1&&Math.abs(promo.parent.x-promo.shell.x)<1);
   if(width>=620)assert.ok(Math.abs(promo.cards[0].h-promo.cards[1].h)<.2&&Math.abs(promo.cards[0].y-promo.cards[1].y)<.2,JSON.stringify(promo));
   await b.center('.visit-ticket');await b.evaluate('document.querySelector(".visit-art img").decode()');
   const ticket=await b.evaluate(`(()=>{const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}},t=document.querySelector('.visit-ticket'),c=t.querySelector('.visit-copy'),s=getComputedStyle(c);return{ticket:rect(t),section:rect(t.closest('section')),copy:rect(c),heading:rect(c.querySelector('h3')),paragraph:rect(c.querySelector('p')),actions:rect(c.querySelector('.visit-actions')),display:s.display,padding:parseFloat(s.paddingBottom),row:s.gridRowStart}})()`);
   assert.ok(Math.abs(ticket.ticket.w-ticket.section.w)<1);
   assert.ok(ticket.heading.bottom<ticket.paragraph.bottom&&ticket.paragraph.bottom<=ticket.actions.y+1);
   assert.ok(Math.abs(ticket.actions.bottom-(ticket.ticket.bottom-(ticket.display==='contents'?24:ticket.padding)))<1,JSON.stringify(ticket));
   if(ticket.display!=='contents')assert.ok(Math.abs(ticket.heading.y-(ticket.copy.y+parseFloat(await b.evaluate(`getComputedStyle(document.querySelector('.visit-copy')).paddingTop`))))<1);
   const row=await inspect();return{heads,hero,promo,ticket,...row};
  });
 }
 for(const width of [320,390,768,960])await check(`menu and settings ${width}`,async()=>{
  await b.viewport(width,844,true);await b.open(base);await click('[data-open-menu]');
  assert.equal(await b.evaluate(`document.querySelector('[data-mobile-nav]').parentElement===document.querySelector('#mobile-menu')`),true);
  let row=await inspect();assert.ok(row.dock.y>=8&&row.dock.bottom<=832.5);assert.equal(row.dock.count,1);
  const toolbar=await b.evaluate(`(()=>{const dock=document.querySelector('[data-mobile-nav]'),r=dock.getBoundingClientRect(),t=dock.querySelector('.dock-toolbar').getBoundingClientRect(),a=dock.querySelector('[data-dock-slot]:not([hidden])').getBoundingClientRect();return{display:getComputedStyle(dock).display,dockWidth:r.width,toolbarWidth:t.width,actionRight:a.right,dockRight:r.right}})()`);
  assert.equal(toolbar.display,'block');assert.ok(Math.abs(toolbar.toolbarWidth-(toolbar.dockWidth-16))<.5&&Math.abs(toolbar.actionRight-(toolbar.dockRight-8))<.5,JSON.stringify(toolbar));
  await click('#mobile-menu .choice-trigger');assert.equal(await b.evaluate(`document.querySelectorAll('[popover]:popover-open').length`),1);
  const popup=await b.evaluate(`(()=>{const r=document.querySelector('[popover]:popover-open').getBoundingClientRect();return{x:r.x,y:r.y,right:r.right,bottom:r.bottom}})()`);assert.ok(popup.x>=15.5&&popup.right<=width-15.5&&popup.y>=15.5&&popup.bottom<=828.5);
  await b.evaluate(`document.querySelector('#mobile-menu .choice-trigger').focus()`);await key('End');await key('Enter');
  assert.equal(await b.evaluate('document.documentElement.dataset.theme'),'dark');assert.equal(await b.evaluate(`[...document.querySelectorAll('[data-theme-select]')].every(e=>e.value==='dark')`),true);
  await click('#mobile-menu .choice-trigger');await key('Escape');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),true);
  await key('Escape');assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),false);
  assert.equal(await b.evaluate(`document.activeElement.matches('[data-open-menu]')`),true);
  await b.center('.of-rail');await b.pause(100);const offerDock=(await inspect()).dock;assert.equal(offerDock.count,3);assert.ok(offerDock.h<=80,'ordinary three-action toolbar should fit one compact row');
  await b.center('.about-stack');await b.pause(100);assert.equal((await inspect()).dock.count,1);
  await b.center('.team-grid');await b.pause(100);assert.equal((await inspect()).dock.count,2);
  return {popup,...row};
 });
 for(const width of [320,390,768])await check(`200 percent text ${width}`,async()=>{
  await b.viewport(width,844,true);await b.open(base);
  await b.evaluate(`(()=>{const runs=[...document.querySelectorAll('body *')].filter(e=>!e.closest('svg,script,style')&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const [e,size] of runs)e.style.fontSize=2*size+'px';const choice=document.querySelector('[data-theme-select]');choice.value='auto';choice.dispatchEvent(new Event('change',{bubbles:true}));})()`);await b.settle();
  for(const selector of ['#welcome-offer','.visit-ticket','.of-rail','.about-stack']){await b.center(selector);await inspect();}
  await click('[data-open-menu]');const row=await inspect();assert.ok(row.dock.y>=8&&row.dock.bottom<=832.5);
  await click('#mobile-menu .choice-trigger');await inspect();await key('Escape');await key('Escape');return row;
 });
}finally{await writeFile(`tmp/planning/${process.env.QA_REPORT_PREFIX||'iteration39'}-layout.json`,JSON.stringify(report,null,2));await b.close();}
assert.deepEqual(report.failures,[]);console.log(`${report.cases.length} layout/interaction cases passed`);
