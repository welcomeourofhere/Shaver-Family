import assert from 'node:assert/strict';
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),url=process.env.QA_URL||'http://127.0.0.1:4321/previews/contacts/',folder='public/previews/contact-concepts',sources=['src/content/contact-map.ts','src/components/contact-concepts/ContactConcept.astro','src/components/contact-concepts/ConceptMap.astro','src/components/contact-concepts/ConceptPerson.astro','src/styles/contact-concepts.css','src/scripts/contact-concepts.ts'],manifest={url,sources:Object.fromEntries(sources.map(file=>[file,createHash('sha256').update(readFileSync(file)).digest('hex')])),items:[]};mkdirSync(folder,{recursive:true});
try{
 await b.send('Page.bringToFront');await b.viewport(1280,1900,true);await b.send('Page.navigate',{url});await b.until(`document.readyState==='complete'&&!!document.querySelector('[data-concept-stage] iframe')`);await b.settle();
 await b.evaluate(`document.documentElement.dataset.theme='light';addEventListener('load',e=>{if(e.target instanceof HTMLIFrameElement)e.target.dataset.qaLoaded='true'},true)`);
 for(const [label,width,viewport,height] of [['desktop',1160,1280,1900],['phone',390,430,2300]]){
  await b.viewport(viewport,height,true);await b.evaluate(`(()=>{const r=document.querySelector('[data-concept-range]');r.value='${width}';r.dispatchEvent(new Event('input',{bubbles:true}))})()`);await b.settle();
  for(let n=1;n<=10;n++){
   const id=String(n).padStart(2,'0');
   // Visit a different panel first so even the initial iframe has an observed load.
   if(n===1)await b.evaluate(`document.querySelector('[data-contact-choice="10"]').click()`);
   await b.evaluate(`(()=>{document.querySelector('[data-contact-choice="${id}"]').click();const f=document.querySelector('#contact-${id} iframe');f.addEventListener('load',()=>f.dataset.qaLoaded='true',{once:true})})()`);await b.settle();await b.center('#contact-'+id);
   try{await b.until(`document.querySelector('#contact-${id} iframe').dataset.qaLoaded==='true'`)}catch(error){const shot=await b.send('Page.captureScreenshot',{format:'jpeg',quality:85});writeFileSync('tmp/planning/iteration51/capture-failure.jpg',Buffer.from(shot.data,'base64'));throw error}await b.pause(1000);
   assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);
   const r=await b.evaluate(`(()=>{const r=document.querySelector('#contact-${id}').getBoundingClientRect();return{x:r.x,y:r.y+scrollY,width:r.width,height:r.height,top:r.top,bottom:r.bottom,viewport:innerHeight}})()`);
   assert.ok(Math.abs(r.width-width)<1);assert.ok(r.top>170&&r.bottom<r.viewport,JSON.stringify(r));
   const {data}=await b.send('Page.captureScreenshot',{format:'jpeg',quality:88,clip:{x:r.x,y:r.y,width:r.width,height:r.height,scale:1},captureBeyondViewport:false}),buffer=Buffer.from(data,'base64'),file=`${id}-${label}.jpg`;
   writeFileSync(`${folder}/${file}`,buffer);manifest.items.push({id,label,file,width:Math.round(r.width),height:Math.round(r.height),sha256:createHash('sha256').update(buffer).digest('hex')});console.log(`CAPTURE ${file} ${Math.round(r.width)} × ${Math.round(r.height)}`);
  }
 }
 writeFileSync(`${folder}/manifest.json`,JSON.stringify(manifest,null,2));
}finally{await b.close()}
