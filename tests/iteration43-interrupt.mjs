import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
try {
 for(const width of [390,768]) for(const selector of ['.of-rail','.team-grid','.about-stack']) {
  await b.viewport(width,844,false);await b.open(base);await b.center(selector);
  const p=await b.point(selector,.8,.4),distance=Math.min(110,width*.25);
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});
  await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
  for(let i=1;i<=6;i++){await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-distance*i/6,y:p.y,button:'left',buttons:1});await b.pause(12)}
  await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x-distance,y:p.y,button:'left',buttons:0,clickCount:1});
  assert.equal(await b.evaluate(`document.querySelector('${selector}').dataset.railSettling`),'true');
  const before=await b.evaluate(`document.querySelector('${selector}').scrollLeft`);
  await b.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:p.x-distance,y:p.y,id:1}]});
  const held=await b.evaluate(`document.querySelector('${selector}').dataset.railSettling`);
  assert.equal(held,'false',`${selector} continued mouse animation under touch`);
  const after=await b.evaluate(`document.querySelector('${selector}').scrollLeft`);
  assert.ok(Math.abs(after-before)<50,`${selector} jumped when interrupted`);
  for(let i=1;i<=5;i++){await b.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:p.x-distance-i*12,y:p.y,id:1}]});await b.pause(16)}
  const moved=await b.evaluate(`document.querySelector('${selector}').scrollLeft`);
  assert.ok(moved>after+15,`${selector} did not follow the new touch`);
  await b.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await b.pause(500);
  assert.notEqual(await b.evaluate(`getComputedStyle(document.querySelector('${selector}')).scrollSnapType`),'none');
  assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);
  console.log(`PASS interrupt ${width} ${selector}`);
 }
} finally {await b.close()}
