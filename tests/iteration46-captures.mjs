import {mkdirSync,writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
mkdirSync('docs/previews',{recursive:true});
async function capture(name){const shot=await b.send('Page.captureScreenshot',{format:'png'});writeFileSync(`docs/previews/round46-${name}.png`,Buffer.from(shot.data,'base64'));}
try{
 for(const width of [390,1440]){
  await b.viewport(width,900,true);await b.open(base);
  if(width===390)await capture('initial-dock-390');
  await b.evaluate(`document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();
  await capture(`article-opening-${width}`);
  await b.evaluate(`document.querySelector('dialog[open] .story-answer').scrollIntoView({block:'start'})`);await b.settle();
  await capture(`article-dialogue-${width}`);
 }
 console.log('Captured initial dock and editorial layout.');
}finally{await b.close()}
