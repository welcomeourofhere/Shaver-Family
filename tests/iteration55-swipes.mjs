import assert from 'node:assert/strict';
import {writeFile,mkdir} from 'node:fs/promises';
import {touchBrowser} from './touch-browser.mjs';

const browser=await touchBrowser(),report={cases:[],failures:[],input:'CDP Input.dispatchTouchEvent',published:false,filter:process.env.SWIPE_TEST_ONLY||null};
const url=process.env.SWIPE_TEST_URL||'http://127.0.0.1:4321/';
const custom=[
  {name:'hero',rail:'.hero-rail',state:`[...document.querySelectorAll('.hero-slide')].findIndex(e=>e.dataset.heroActive==='true')`,count:'.hero-slide'},
  {name:'services',rail:'.sd-stack',state:`[...document.querySelectorAll('[data-sd-tab]')].findIndex(e=>e.getAttribute('aria-selected')==='true')`,count:'[data-sd-tab]'},
  {name:'certificates',rail:'[data-certificate-scene]',state:`Math.max(0,[...document.querySelectorAll('[data-certificate]')].findIndex(e=>e.getAttribute('aria-pressed')==='true'))`,count:'[data-certificate]'},
];
const native=[
  {name:'offers',rail:'.of-rail',card:'.of-card',selection:'.of-card[data-offer-active=true]',controls:'offers-rail'},
  {name:'masters',rail:'.team-grid',card:'.team-card',selection:'.team-card[data-mobile-current=true]',controls:'masters-rail'},
  {name:'about',rail:'.about-stack',card:'.about-layer',selection:'.about-layer',controls:'about-rail'},
  {name:'gifts',rail:'.gifts-grid',card:'.gift',controls:'gifts-rail'},
  {name:'service-tabs',rail:'.sd-tabs'},
];
async function check(name,run) {
  if(report.filter&&!name.includes(report.filter))return;
  try {const evidence=await run();report.cases.push({name,...evidence});console.log('PASS '+name);}
  catch(error){report.failures.push({name,error:error.message});console.log('FAIL '+name+': '+error.message);}
}
const state=scene=>browser.evaluate(scene.state);
const noDialog=async()=>assert.equal(await browser.evaluate(`!!document.querySelector('dialog:modal')`),false,'swipe opened an action');
async function tap(selector,reveal=true) {
  if(reveal)await browser.center(selector);
  const p=await browser.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect();for(let y=Math.max(10,r.top+5);y<Math.min(innerHeight-120,r.bottom-5);y+=5)for(let x=Math.max(10,r.left+5);x<Math.min(innerWidth-10,r.right-5);x+=5)if(document.elementFromPoint(x,y)?.closest(${JSON.stringify(selector)})===e)return{x,y};return null})()`);
  assert.ok(p,'no exposed touch target: '+selector);await browser.tap(p);
}
async function gesture(selector,direction,dy=0,cancel=false,distance=190) {
  await browser.center(selector);
  const p=await browser.point(selector,direction<0?.82:.18,.4);
  assert.ok(await browser.evaluate(`!!document.elementFromPoint(${p.x},${p.y})?.closest(${JSON.stringify(selector)})`),'gesture start is covered: '+selector+' '+JSON.stringify({p,hit:await browser.evaluate(`document.elementFromPoint(${p.x},${p.y})?.outerHTML.slice(0,180)`)}));
  await browser.swipe(p,direction*distance,dy,cancel);await browser.until(`![...document.querySelectorAll('.compact-rail')].some(e=>e.dataset.railSettling==='true')`);
}
try {
  for(const [width,height,reduced] of [[320,740,true],[390,844,true],[768,600,true],[960,540,true],[390,844,false]]) {
    const prefix=`${width}x${height} ${reduced?'reduced':'motion'}`;
    await browser.viewport(width,height,reduced);await browser.open(url);
    const device=await browser.evaluate(`({coarse:matchMedia('(pointer:coarse)').matches,touch:navigator.maxTouchPoints,width:innerWidth})`);
    assert.equal(device.coarse,true);assert.ok(device.touch>0);assert.equal(device.width,width);
    for(const scene of custom.filter(scene=>scene.name!=='hero')) {
      await check(`${prefix} ${scene.name} forward/back/wrap`,async()=>{
        await browser.center(scene.rail);const first=await state(scene),count=await browser.evaluate(`document.querySelectorAll(${JSON.stringify(scene.count)}).length`);
        if(scene.name==='services'&&width<=600){
          const seen=new Set([first]);
          for(let i=0;i<count;i++){
            const under=await browser.evaluate(`[...document.querySelectorAll('[data-sd-panel]')].findIndex(e=>e.style.getPropertyValue('--card-level')==='1')`);
            await gesture(scene.rail,i%2?1:-1);assert.equal(await state(scene),under,'reveal the card underneath');seen.add(await state(scene));await noDialog();
          }
          assert.equal(seen.size,count,'repeated throws must visit every category');assert.equal(await state(scene),first,'full stack cycle');return{device,count,physicalStack:true};
        }
        await gesture(scene.rail,-1);assert.equal(await state(scene),(first+1)%count,'forward');await noDialog();
        await gesture(scene.rail,1);assert.equal(await state(scene),first,'back');
        await gesture(scene.rail,1);assert.equal(await state(scene),(first+count-1)%count,'reverse boundary');
        await gesture(scene.rail,-1);assert.equal(await state(scene),first,'forward boundary');
        return {device,count,trace:await browser.evaluate('window.__touchTrace.slice(-8)')};
      });
      await check(`${prefix} ${scene.name} vertical/cancel/short`,async()=>{
        await browser.center(scene.rail);const before=await state(scene);
        await gesture(scene.rail,-1,0,true);assert.equal(await state(scene),before,'cancel');
        await gesture(scene.rail,-1,0,false,20);assert.equal(await state(scene),before,'short drag');
        await browser.center(scene.rail);const y=await browser.evaluate('scrollY');
        await gesture(scene.rail,-1,-145,false,12);assert.equal(await state(scene),before,'vertical gesture switched a card');
        const scroll=await browser.evaluate('scrollY');assert.ok(scroll>y+20,'vertical page scrolling was blocked');await noDialog();
        assert.equal(await browser.evaluate(`document.querySelectorAll('.is-dragging').length`),0);
        return {verticalDistance:scroll-y};
      });
    }
    for(const scene of native) {
      await check(`${prefix} ${scene.name} native touch`,async()=>{
        await browser.center(scene.rail);
        const geometry=await browser.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(scene.rail)});e.scrollTo({left:0,behavior:'instant'});return{width:e.clientWidth,total:e.scrollWidth}})()`);await browser.settle();
        if(geometry.total<=geometry.width+1)return {fits:true,geometry};
        const before=await browser.evaluate(`document.querySelector(${JSON.stringify(scene.rail)}).scrollLeft`);
        await gesture(scene.rail,-1,0,false,Math.min(260,width*.6));
        const forward=await browser.evaluate(`document.querySelector(${JSON.stringify(scene.rail)}).scrollLeft`);
        assert.ok(forward>before+10,'native forward');await noDialog();
        const selection=scene.selection?await browser.evaluate(`document.querySelector(${JSON.stringify(scene.selection)})?.outerHTML.slice(0,280)`):undefined;
        const controls=scene.controls?await browser.evaluate(`document.querySelector('[data-rail-controls="${scene.controls}"]')?.innerText`):undefined;
        if(scene.card) {
          const owner=await browser.evaluate(`(()=>{const rail=document.querySelector(${JSON.stringify(scene.rail)}),r=rail.getBoundingClientRect(),cards=[...rail.querySelectorAll(${JSON.stringify(scene.card)})],overlap=cards.map(c=>{const b=c.getBoundingClientRect();return Math.max(0,Math.min(b.right,r.right)-Math.max(b.left,r.left))}),count=document.querySelector('[data-rail-controls="${scene.controls}"] output'),index=${scene.name==='masters'?"cards.findIndex(c=>c.dataset.mobileCurrent==='true')":scene.name==='about'?"Number(rail.dataset.railIndex)":"Number(count.textContent.trim().split('/')[0])-1"};return{index,overlap,count:count?.textContent,dock:document.querySelector('[data-mobile-nav]').dataset.section,primary:document.querySelector('[data-dock-primary]').getAttribute('aria-label'),name:cards[index]?.dataset.bookingName}})()`);
          assert.ok(owner.index>=0);assert.ok(owner.overlap[owner.index]>=Math.max(...owner.overlap)-1,'selection did not follow visible card');
          if(scene.controls)assert.equal(Number(owner.count.trim().split('/')[0]),owner.index+1,'counter');
          if(scene.name==='masters'&&owner.dock==='masters')assert.ok(owner.primary.includes(owner.name),'dock booking owner');
        }
        await gesture(scene.rail,1,0,false,Math.min(260,width*.6));
        const back=await browser.evaluate(`document.querySelector(${JSON.stringify(scene.rail)}).scrollLeft`);assert.ok(back<forward-10,'native back');await noDialog();
        if(scene.selection)assert.ok(selection,'selected item is absent');
        await browser.center(scene.rail);const start=await browser.point(scene.rail,.5,.4),verticalStart=await browser.evaluate('scrollY');
        await browser.swipe(start,10,start.y<160?130:-130);
        assert.ok(Math.abs(await browser.evaluate('scrollY')-verticalStart)>20,'vertical page scroll from native rail');
        return {geometry,before,forward,back,selection,controls};
      });
    }
    for(const [name,selector] of [
      ['offer-button','.of-card[data-offer-active=true] .of-action'],
      ['service-summary','.sd-card[aria-hidden=false] .sd-summary'],
      ['master-booking','.team-card[data-mobile-current=true] .team-book'],
      ['about-disclosure','.about-layer:first-child [data-about-more]'],
      ['gift-button','.gifts-grid .gift-visual[data-has-photo=true]'],
    ])await check(`${prefix} ${name} touch start`,async()=>{
      await gesture(selector,-1,0,false,Math.min(130,width*.35));await noDialog();
      if(name==='about-disclosure')assert.equal(await browser.evaluate(`document.querySelector(${JSON.stringify(selector)}).getAttribute('aria-expanded')`),'false');
      if(name==='gift-button')assert.equal(await browser.evaluate(`document.querySelector(${JSON.stringify(selector)}).getAttribute('aria-pressed')`),'false');
      return {trace:await browser.evaluate('window.__touchTrace.slice(-5)')};
    });
    await check(`${prefix} taps still work`,async()=>{
      await tap('[data-sd-tab="0"]');assert.equal(await state(custom[1]),0);
      await tap('[data-sd-tab="1"]');assert.equal(await state(custom[1]),1);
      await tap('[data-certificate-value="3000"]');assert.equal(await state(custom.find(scene=>scene.name==='certificates')),3);
      await tap('.gifts-grid .gift-visual[data-has-photo=true]');
      // A neighbour is selected on the first tap and its own action runs on the next tap.
      if(await browser.evaluate(`document.querySelector('.gifts-grid .gift-visual[data-has-photo=true]').getAttribute('aria-pressed')`)!=='true')await tap('.gifts-grid .gift-visual[data-has-photo=true]',false);
      assert.equal(await browser.evaluate(`document.querySelector('.gifts-grid .gift-visual[data-has-photo=true]').getAttribute('aria-pressed')`),'true');
      await tap('.gifts-grid .gift-visual[data-has-photo=true]',false);
      return {};
    });
    await check(`${prefix} second finger cancels custom swipe`,async()=>{
      const scene=custom[1];await browser.center(scene.rail);const before=await state(scene),p=await browser.point(scene.rail,.7,.4);
      const a={...p,id:1},c={x:p.x-80,y:p.y,id:2};
      await browser.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[a]});
      await browser.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...a,x:a.x-15}]});
      await browser.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...a,x:a.x-15},c]});
      await browser.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...a,x:a.x-65},{...c,x:c.x-50}]});
      await browser.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await browser.settle();
      assert.equal(await state(scene),before);assert.equal(await browser.evaluate(`document.querySelectorAll('.is-dragging').length`),0);
      await browser.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});return {};
    });
    await check(`${prefix} no overflow/errors`,async()=>{
      assert.deepEqual(await browser.evaluate('window.__touchErrors'),[]);
      assert.equal(await browser.evaluate('document.documentElement.scrollWidth>innerWidth+1'),false);
      return {};
    });
  }
} finally {
  await mkdir('tmp/planning',{recursive:true});await writeFile(process.env.SWIPE_TEST_REPORT||'tmp/planning/iteration37-swipes.json',JSON.stringify(report,null,2));await browser.close();
}
assert.equal(report.failures.length,0,JSON.stringify(report.failures,null,2));
console.log(`${report.cases.length} touch cases passed`);
