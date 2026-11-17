import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';

const config=JSON.parse(readFileSync(new URL('../src/config/feedback.json',import.meta.url),'utf8'));
const original=readFileSync(new URL('../src/scripts/feedback.ts',import.meta.url),'utf8');
const source=stripTypeScriptTypes(original.replace(/^import config .*$/m,'const config='+JSON.stringify(config)+';')).replace(/\bexport\s+/g,'')+'\nglobalThis.api={beginSlideFeedback,requestFeedback};';
function fixture({reduced=false,enabled=true}={}){
 let now=0,nextFrame=1,preference=String(enabled);const frames=new Map(),plays=[],haptics=[],documentEvents=new Map(),windowEvents=new Map();
 const on=map=>(name,listener)=>{const listeners=map.get(name)||[];listeners.push(listener);map.set(name,listeners);};
 const media={matches:reduced,addEventListener(){}};
 const document={hidden:false,querySelectorAll:()=>[],addEventListener:on(documentEvents)};
 class Element{}
 class Audio{constructor(src){this.src=src;this.currentTime=0;}load(){}pause(){}play(){plays.push({at:now,url:this.src});return Promise.resolve();}}
 const window={localStorage:{getItem:()=>preference,setItem:(_,value)=>preference=value},matchMedia:()=>media,addEventListener:on(windowEvents)};
 const sandbox={document,window,Element,Audio,location:{origin:'https://soyuz.hair'},navigator:{vibrate:pattern=>haptics.push({at:now,pattern})},performance:{now:()=>now},
  requestAnimationFrame:callback=>{const id=nextFrame++;frames.set(id,callback);return id;},cancelAnimationFrame:id=>frames.delete(id)};
 runInNewContext(source,sandbox);
 const event=(extra={})=>{const event={isTrusted:true,type:'pointermove',pointerType:'touch',target:null,...extra};if(event.pointerType===undefined)delete event.pointerType;return event;};
 return {...sandbox.api,plays,haptics,media,event,
  frame(at){now=at;const callbacks=[...frames.values()];frames.clear();callbacks.forEach(callback=>callback(at));},
  dispatch(type,event={}){for(const listener of documentEvents.get(type)||[])listener(event);},
  hide(){document.hidden=true;for(const listener of documentEvents.get('visibilitychange')||[])listener({});},
  mute(){preference='false';for(const listener of windowEvents.get('storage')||[])listener({key:'soyuz_feedback_enabled'});},
  pending:()=>frames.size,positive:()=>haptics.filter(item=>Array.isArray(item.pattern)&&item.pattern.some(value=>value>0)),
 };
}

test('each rendered slide vibrates during motion while audio alone keeps its 48ms gate',()=>{
 const f=fixture(),gesture=f.beginSlideFeedback(0,f.event());
 gesture.cross(1);f.frame(16);gesture.cross(2);f.frame(32);gesture.cross(3);f.frame(64);
 assert.deepEqual(f.positive().map(item=>item.at),[16,32,64]);
 assert.deepEqual(f.plays.map(item=>item.at),[16,64]);
 gesture.finish();f.frame(1000);assert.equal(f.positive().length,3);assert.equal(f.pending(),0);
});

test('unpainted jumps and reversals coalesce to the actual final selected index with no backlog',()=>{
 const f=fixture(),gesture=f.beginSlideFeedback(0,f.event());
 gesture.cross(1);gesture.cross(20);f.frame(16);assert.equal(f.positive().length,1);
 gesture.cross(21);gesture.cross(20);f.frame(32);assert.equal(f.positive().length,1);
 gesture.cross(19);gesture.finish();f.frame(48);assert.equal(f.positive().length,2);
 f.frame(10000);assert.equal(f.positive().length,2);assert.equal(f.pending(),0);
});

test('same index, untrusted sources, cancellation and a newer gesture never replay stale pulses',()=>{
 const f=fixture();let gesture=f.beginSlideFeedback(0,f.event({isTrusted:false}));gesture.cross(1);f.frame(16);assert.equal(f.positive().length,0);
 gesture=f.beginSlideFeedback(0,f.event());gesture.cross(0);f.frame(32);assert.equal(f.positive().length,0);
 gesture.cross(1);gesture.cancel();f.frame(48);assert.equal(f.positive().length,0);
 gesture=f.beginSlideFeedback(0,f.event());gesture.cross(1);const latest=f.beginSlideFeedback(7,f.event());latest.cross(8);f.frame(64);assert.equal(f.positive().length,1);
 assert.equal(gesture.cross(2),0);latest.finish();assert.equal(latest.cross(9),0);
});

test('pointercancel used for native touch handoff survives, while new input, focus, mute and hidden state cancel',()=>{
 const f=fixture();let gesture=f.beginSlideFeedback(0,f.event({type:'touchmove',pointerType:undefined}));
 f.dispatch('pointercancel',{});gesture.cross(1);f.frame(16);assert.equal(f.positive().length,1);
 for(const type of['pointerdown','keydown','focusin','wheel']){
  gesture=f.beginSlideFeedback(1,f.event());gesture.cross(2);f.dispatch(type,f.event());f.frame(80);assert.equal(f.positive().length,1,type);
 }
 gesture=f.beginSlideFeedback(1,f.event());gesture.cross(2);f.hide();f.frame(96);assert.equal(f.positive().length,1);
 const muted=fixture();gesture=muted.beginSlideFeedback(0,muted.event());gesture.cross(1);muted.mute();muted.frame(16);assert.equal(muted.positive().length,0);
});

test('mute and reduced motion suppress haptics; mouse crosses may sound but never vibrate',()=>{
 for(const options of[{enabled:false},{reduced:true}]){const f=fixture(options),gesture=f.beginSlideFeedback(0,f.event());gesture.cross(1);f.frame(16);assert.equal(f.positive().length,0);}
 const f=fixture(),gesture=f.beginSlideFeedback(0,f.event({pointerType:'mouse'}));gesture.cross(1);f.frame(16);assert.equal(f.positive().length,0);assert.equal(f.plays.length,1);
});

test('ordinary actions retain one-event deduplication and cancel pending slide feedback',()=>{
 const f=fixture(),gesture=f.beginSlideFeedback(0,f.event()),event=f.event({type:'click'});gesture.cross(1);
 f.requestFeedback('tap',event);f.requestFeedback('tap',event);f.frame(16);
 assert.equal(f.plays.length,1);assert.equal(f.positive().length,1);assert.equal(f.plays[0].url,config.tones.tap.url);
});
