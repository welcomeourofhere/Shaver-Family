import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try{
 for(const width of [320,390,768,1024,1440]) for(const theme of ['light','dark']){
  await b.viewport(width,900,true);await b.open(base);
  await b.evaluate(`document.documentElement.dataset.theme='${theme}';document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();
  const state=await b.evaluate(`(()=>{const story=document.querySelector('dialog[open] .master-story'),qa=story.querySelector('.story-answer'),question=qa.querySelector('h4'),answer=qa.querySelector('blockquote'),rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top,width:r.width}};return{question:rect(question),answer:rect(answer),background:getComputedStyle(answer).backgroundColor,line:getComputedStyle(answer).borderLeftWidth,cover:rect(story.querySelector('.story-cover')),body:rect(story.querySelector('.story-body')),overflow:document.documentElement.scrollWidth-innerWidth,quotes:story.querySelectorAll('blockquote').length}})()`);
  assert.equal(state.background,'rgba(0, 0, 0, 0)');assert.equal(state.line,'3px');assert.ok(state.quotes>20&&state.overflow<=1);
  assert.ok(Math.abs(state.cover.width-state.body.width)<1);
  assert.ok(Math.abs(state.question.left-state.answer.left)<1&&state.answer.top>state.question.top,JSON.stringify({width,theme,state}));
  const photo=await b.evaluate(`(async()=>{const img=document.querySelector('dialog[open] .story-photos:not(.story-photos-grid) .story-portrait img');await img.decode();const r=img.getBoundingClientRect(),close=document.querySelector('dialog[open] .story-dialog-head button').getBoundingClientRect(),text=document.querySelector('dialog[open] .story-answer p').getBoundingClientRect();return{ratio:r.width/r.height,natural:img.naturalWidth/img.naturalHeight,height:r.height,close:{left:close.left,right:close.right,top:close.top},textRight:text.right}})()`);
  assert.ok(Math.abs(photo.ratio-photo.natural)<.01&&photo.height<=900*.65+1,JSON.stringify(photo));
  assert.ok(photo.close.right<=width&&photo.close.top>=0,JSON.stringify({width,photo}));
  const visual=await b.evaluate(`(()=>{const d=document.querySelector('dialog[open]'),viewport=d.querySelector('.surface-content'),r=d.getBoundingClientRect(),s=viewport.getBoundingClientRect();return{right:r.right-s.right,tones:new Set([...d.querySelectorAll('.story-answer blockquote')].map(e=>getComputedStyle(e).borderLeftColor)).size,headings:new Set([...d.querySelectorAll('.story-chapter>h3')].map(e=>getComputedStyle(e).color)).size,underlines:[...d.querySelectorAll('.story-chapter>h3')].some(e=>parseFloat(getComputedStyle(e).borderBottomWidth)>0),radii:[...d.querySelectorAll('.story-portrait img')].map(e=>parseFloat(getComputedStyle(e).borderRadius))}})()`);
  assert.ok(visual.right<1&&visual.tones===3&&visual.headings===1&&!visual.underlines&&visual.radii.every(radius=>radius>=12),JSON.stringify(visual));
  console.log(`PASS editorial single column ${width} ${theme}`);
 }
 await b.viewport(1440,900,true);await b.send('Page.navigate',{url:new URL('masters/sofya-shalaginova/',base).href});await b.until(`document.readyState==='complete'&&!!document.querySelector('.story-answer')`);await b.settle();
 assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('.story-answer')).display`),'block');
 assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);console.log('PASS standalone article uses the same layout');
}finally{await b.close()}
