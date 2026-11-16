import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b=await touchBrowser(),report=[],base=process.env.QA_URL||'http://127.0.0.1:4321/';
mkdirSync('tmp/planning/iteration55',{recursive:true});
const check=async(name,run)=>{try{const evidence=await run();report.push({name,pass:true,evidence});console.log('PASS '+name)}catch(error){report.push({name,pass:false,error:String(error)});console.log('FAIL '+name+': '+error.message)}};
async function press(selector){const p=await b.point(selector);await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',buttons:1,clickCount:1,...p});await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',buttons:0,clickCount:1,...p});await b.pause(230);await b.settle();}
const reset=async()=>{await b.pause(190);await b.evaluate('window.__audio=[];window.__haptics=[]')};
const audio=()=>b.evaluate('__audio.map(item=>new URL(item.src).pathname)');
async function expectTone(tone){const calls=await audio();assert.deepEqual(calls,tone?[`/audio/${tone}.wav`]:[]);return calls;}
async function key(key){const codes={Enter:13,Escape:27,ArrowDown:40,ArrowUp:38,Tab:9};await b.send('Input.dispatchKeyEvent',{type:'keyDown',key,code:key,text:key==='Enter'?'\r':undefined,windowsVirtualKeyCode:codes[key]||0});await b.send('Input.dispatchKeyEvent',{type:'keyUp',key,code:key,windowsVirtualKeyCode:codes[key]||0});await b.pause(230);await b.settle();}
try{
 await b.send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__audio=[];window.__haptics=[];HTMLMediaElement.prototype.play=function(){if(this.src.includes('/audio/'))__audio.push({src:this.src,volume:this.volume});return Promise.resolve()};Object.defineProperty(navigator,'vibrate',{configurable:true,value:pattern=>{__haptics.push(pattern);return true}});`});
 await b.viewport(390,844,false);await b.open(base);
 await check('cancelled trusted click is silent after all DOM listeners',async()=>{
  await b.evaluate(`(()=>{const e=document.createElement('button');e.id='cancel-audit';e.textContent='Проверка';e.style='position:fixed;left:80px;top:100px;z-index:9999;width:160px;height:48px';e.addEventListener('click',event=>event.preventDefault());document.body.append(e)})()`);
  await reset();await press('#cancel-audit');await expectTone(null);await b.evaluate(`document.querySelector('#cancel-audit').remove()`);
 });
 await check('mobile menu opening and closing use their respective single cues',async()=>{
  await reset();await press('[data-open-menu]');await expectTone('open');assert.ok(await b.evaluate(`document.querySelector('#mobile-menu').open`));
  await reset();await press('[data-open-menu]');return expectTone('close');
 });
 await check('theme trigger closes on repeated press and does not play opening again',async()=>{
  await press('[data-open-menu]');await reset();await press('#mobile-menu .choice-trigger');await expectTone('open');
  assert.ok(await b.evaluate(`!!document.querySelector('#mobile-menu .choice-list:popover-open')`));
  await reset();await press('#mobile-menu .choice-trigger');await expectTone('close');
  assert.equal(await b.evaluate(`!!document.querySelector('#mobile-menu .choice-list:popover-open')`),false);
 });
 await check('theme option changes theme and uses selection cue once',async()=>{
  await press('#mobile-menu .choice-trigger');await reset();await press('#mobile-menu .choice-option[data-value="dark"]');await expectTone('select');
  assert.equal(await b.evaluate('document.documentElement.dataset.theme'),'dark');
 });
 await check('keyboard combobox uses opening, selection and closing cues',async()=>{
  await b.evaluate(`document.querySelector('#mobile-menu .choice-trigger').focus()`);await reset();await key('ArrowDown');await expectTone('open');
  await reset();await key('Enter');await expectTone('select');
  await reset();await key('ArrowDown');await expectTone('open');await reset();await key('Escape');return expectTone('close');
 });
 await check('mute synchronizes settings, remains silent and survives reload',async()=>{
  await reset();await press('#mobile-menu [data-feedback-toggle]');await expectTone(null);
  assert.equal(await b.evaluate(`document.querySelector('[data-feedback-toggle]').getAttribute('aria-pressed')`),'false');
  await b.open(base);await press('[data-open-menu]');await expectTone(null);assert.equal(await b.evaluate(`document.querySelector('[data-feedback-toggle]').getAttribute('aria-pressed')`),'false');
  await press('#mobile-menu [data-feedback-toggle]');return expectTone('tap');
 });
 await press('[data-open-menu]');
 await check('touch has one haptic request while mouse is silent and volume stays shared',async()=>{
  await reset();await b.tap(await b.point('[data-open-menu]'));await b.pause(70);await expectTone('open');
  const evidence=await b.evaluate('({audio:__audio,haptics:__haptics})');assert.equal(evidence.audio[0].volume,.18);assert.deepEqual(evidence.haptics,[[8,24,14]]);
  await reset();await press('[data-open-menu]');await expectTone('close');assert.deepEqual(await b.evaluate('__haptics'),[]);return evidence;
 });
 await check('reduced motion suppresses haptics without disabling the requested sound',async()=>{
  await b.viewport(390,844,true);await reset();await b.tap(await b.point('[data-open-menu]'));await b.pause(60);await expectTone('open');assert.deepEqual(await b.evaluate('__haptics'),[]);await press('[data-open-menu]');
 });
 await check('programmatic clicks and hover never play audio',async()=>{
  await reset();await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.pause(150);await expectTone(null);await b.evaluate(`document.querySelector('[data-open-menu]').click()`);await b.settle();await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...await b.point('[data-open-menu]')});await b.pause(220);await expectTone(null);
 });
 await check('FAQ opens and closes with disclosure cues, keyboard included',async()=>{
  const selector='.faq-item:first-child>summary';await b.center(selector);await reset();await press(selector);await expectTone('open');
  await b.evaluate(`document.querySelector('${selector}').focus()`);await reset();await key('Enter');await expectTone('close');
 });
 await check('mouse drag from a booking control cancels click, audio and booking',async()=>{
  await b.viewport(390,844,false);await b.center('#masters-rail');const p=await b.point('.team-card:first-child .team-book');await reset();
  await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',...p});await b.send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
  for(let i=1;i<=8;i++){await b.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x-35*i/8,y:p.y,button:'left',buttons:1});await b.pause(20)}
  await b.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x-35,y:p.y,button:'left',buttons:0,clickCount:1});await b.pause(400);await expectTone(null);
  assert.equal(await b.evaluate(`!!document.querySelector('[data-booking-drawer][open]')`),false);
 });
 await check('local navigation commits one tap and a native rail control one selection',async()=>{
  await press('[data-open-menu]');await reset();await press('#mobile-menu a[href="#offers"]');await expectTone('tap');await b.pause(280);
  await b.center('#offers');await reset();await press('#offers [data-rail-step="1"]');return expectTone('select');
 });
 await check('review media indicator commits one selection and automatic media stays quiet',async()=>{
  await b.viewport(1440,1000,true);await b.open(base);await b.evaluate(`document.querySelector('[data-theme-select]').value='light';document.querySelector('[data-theme-select]').dispatchEvent(new Event('change',{bubbles:true}))`);
  const selector='.review-gallery:has(.slide-indicator) .slide-dot[data-slide-index="1"]';await b.center(selector);await reset();await press(selector);await expectTone('select');await reset();await b.pause(450);return expectTone(null);
 });
 await check('accepted booking clicks have one opening cue, including an already open drawer',async()=>{
  await b.send('Fetch.enable',{patterns:[{urlPattern:'*yclients.ru*'}]});b.on('Fetch.requestPaused',request=>{void b.send('Fetch.fulfillRequest',{requestId:request.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'text/html'}],body:Buffer.from('<!doctype html><title>Локальная проверка записи</title>').toString('base64')})});
  await b.center('.header-book');await reset();await press('.header-book');await expectTone('open');assert.ok(await b.evaluate(`document.querySelector('[data-booking-drawer]').open`));
  await reset();await press('.header-book');await expectTone('open');await reset();await key('Escape');await expectTone('close');await b.send('Fetch.disable');
 });
 await check('desktop header consumes native disclosure without losing its closing cue',async()=>{
  await b.evaluate(`scrollTo({top:0,behavior:'instant'})`);await b.settle();await key('Tab');await b.evaluate(`document.querySelector('.more-menu>summary').focus()`);await b.settle();assert.equal(await b.evaluate(`document.querySelector('.more-menu').open`),true);
  await reset();await key('Enter');return expectTone('close');
 });
 await check('contextual contact action opens the shared dialog and clears old context',async()=>{
  await b.viewport(390,844,true);await b.open(base);await b.center('#faq');await b.until(`document.querySelector('[data-mobile-nav]').dataset.section==='faq'`);
  await b.evaluate(`const context=document.querySelector('[data-contact-context]');context.textContent='Старый контекст';context.hidden=false`);await reset();await press('[data-action="contact"]');await expectTone('open');
  const state=await b.evaluate(`({open:document.querySelector('.contact-dialog').open,context:document.querySelector('[data-contact-context]').textContent,hidden:document.querySelector('[data-contact-context]').hidden})`);assert.deepEqual(state,{open:true,context:'',hidden:true});return state;
 });
 await check('no runtime errors across feedback and preference scenarios',async()=>{const errors=await b.evaluate('__touchErrors');assert.deepEqual(errors,[]);return errors});
}finally{writeFileSync('tmp/planning/iteration55/feedback.json',JSON.stringify({report,evidence:'Trusted Chromium input; playback and vibration API requests instrumented, no claim about physical hardware.',published:false},null,2));await b.close()}
assert.ok(report.every(r=>r.pass),'Feedback scenarios failed');
