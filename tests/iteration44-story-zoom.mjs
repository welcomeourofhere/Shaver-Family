import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try{
 for(const width of [320,390]){
  await b.viewport(width,844,true);await b.open(base);
  await b.evaluate(`(()=>{for(const e of document.querySelectorAll('body *')){if(e.closest('svg,script,style')||![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))continue;const size=parseFloat(getComputedStyle(e).fontSize);e.style.fontSize=2*size+'px';}})()`);
  await b.evaluate(`document.querySelector('[data-team-open="souz-sofya-shalaginova"]').click()`);await b.settle();
  const row=await b.evaluate(`(()=>{const d=document.querySelector('#team-dialog-souz-sofya-shalaginova'),content=d.querySelector('.surface-content'),e=d.querySelector('.team-dialog-actions button'),range=document.createRange();range.selectNodeContents(e);const r=e.getBoundingClientRect(),s=getComputedStyle(e),close=d.querySelector('[data-dismiss]').getBoundingClientRect();return{scroll:e.scrollWidth,client:e.clientWidth,lines:range.getClientRects().length,pad:parseFloat(s.paddingLeft),height:r.height,overflow:content.scrollWidth>content.clientWidth+1||document.documentElement.scrollWidth>innerWidth+1||close.right>innerWidth||close.left<0};})()`);
  assert.ok(row.scroll<=row.client+1&&row.lines===1&&row.pad>=12&&row.height>=44&&!row.overflow,JSON.stringify({width,...row}));
  console.log(`PASS article button 200% ${width}`);
 }
}finally{await b.close()}
