import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),base=process.env.QA_URL||'http://127.0.0.1:4321/';
async function click(selector){const p=await b.point(selector);await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',buttons:0,clickCount:1});}
try{
 await b.viewport(390,844,false);await b.open(base);
 await click('[data-open-menu]');
 const opening=await b.evaluate(`document.querySelector('.dock-shell').getAnimations().map(a=>a.effect.getTiming().duration)`);
 assert.ok(opening.includes(280),JSON.stringify(opening));await b.settle();
 await click('[data-open-menu]');
 const closing=await b.evaluate(`document.querySelector('.dock-shell').getAnimations().map(a=>a.effect.getTiming().duration)`);
 assert.ok(closing.includes(220),JSON.stringify(closing));await b.settle();
 await b.evaluate(`document.querySelector('[data-open-menu]').focus()`);
 await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',windowsVirtualKeyCode:13});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
 assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),true,JSON.stringify(await b.evaluate(`({focus:document.activeElement?.outerHTML,events:window.__touchTrace.slice(-6),expanded:document.querySelector('[data-mobile-nav]').dataset.expanded})`)));
 assert.equal(await b.evaluate(`document.querySelector('.dock-shell').getAnimations().length`),0);
 assert.equal(await b.evaluate(`getComputedStyle(document.querySelector('.dock-close-icon')).transitionDuration`),'0s');
 await b.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
 assert.equal(await b.evaluate(`document.querySelector('#mobile-menu').open`),false);
 assert.deepEqual(await b.evaluate('window.__touchErrors'),[]);console.log('PASS pointer timings and immediate keyboard menu');
}finally{await b.close()}
