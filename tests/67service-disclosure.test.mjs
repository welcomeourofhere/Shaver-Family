import{test}from'node:test';import assert from'node:assert/strict';
import{animateServiceDisclosure}from'../src/scripts/service-disclosure.ts';
globalThis.getComputedStyle=e=>({height:e.layoutHeight+'px'});
function fixture(scale=1){const effects=[],dataset={};let resolve;
 const element=height=>({layoutHeight:height,getBoundingClientRect:()=>({height:height*scale}),animate(frames,options){const effect={frames,options,cancelled:false,cancel(){this.cancelled=true;},finished:new Promise(done=>{resolve=done;})};effects.push(effect);return effect;}});
 const body=element(80),summary=element(44),row={...element(124),open:true,dataset,querySelector:s=>s==='summary'?summary:body};
 return{row,effects,finish:()=>resolve()};}
test('service disclosure reveals its natural height on one bounded shared timeline',()=>{const f=fixture();const stop=animateServiceDisclosure(f.row,false,220);assert.equal(f.effects.length,2);assert.equal(f.effects[0].frames[0].height,'44px');assert.equal(f.effects[0].frames.at(-1).height,'124px');assert.ok(f.effects[0].frames.some(x=>parseFloat(x.height)>44&&parseFloat(x.height)<124));assert.ok(f.effects.every(x=>x.options.duration===220));assert.equal(f.row.open,true);stop();assert.ok(f.effects.every(x=>x.cancelled));assert.equal(f.row.dataset.serviceOpening,undefined);});
test('reduced motion and native closed details need no temporary animated state',()=>{const f=fixture();assert.equal(animateServiceDisclosure(f.row,true,220),undefined);f.row.open=false;assert.equal(animateServiceDisclosure(f.row,false,220),undefined);assert.equal(f.effects.length,0);});
test('parent card perspective cannot feed its visible scale back into disclosure layout',()=>{const f=fixture(.75);f.row.layoutHeight=124.375;f.row.querySelector('summary').layoutHeight=44.125;const stop=animateServiceDisclosure(f.row,false,220);assert.equal(f.effects[0].frames[0].height,'44.125px');assert.equal(f.effects[0].frames.at(-1).height,'124.375px');stop();});
