import {test} from 'node:test';import assert from 'node:assert/strict';
import {offerSlot,offerDealFrame} from '../src/scripts/offer-loop.ts';
test('offer pile lays every upcoming card to the right, including loop seam',()=>{
 for(let selected=0;selected<11;selected++){
  const slots=Array.from({length:11},(_,i)=>offerSlot(i,selected,11,374,800));
  assert.equal(slots[selected].x,0);assert.ok(slots.every(s=>s.x>=0));
  assert.equal(slots[(selected+1)%11].x,374);assert.equal(slots.filter(s=>s.visible).length,3);
 }
});
test('pile visibility adapts without a left offscreen slot',()=>{
 const slots=Array.from({length:11},(_,i)=>offerSlot(i,10,11,300,280));
 assert.equal(slots.filter(s=>s.visible).length,1);assert.equal(slots[10].visible,true);assert.equal(slots[0].x,300);
});

test('elastic deal preserves stable travel while adding a bounded material spring',()=>{
 const a={x:374,y:0,scale:1,opacity:1},b={...a,x:0};
 const poses=Array.from({length:501},(_,i)=>offerDealFrame(a,b,i/500,.06));
 assert.deepEqual(poses[0],a);assert.deepEqual(poses.at(-1),b);
 assert.ok(poses.every((p,i)=>p.x>=0&&p.x<=374&&(!i||p.x<=poses[i-1].x)));
 assert.ok(Math.max(...poses.map(p=>p.scale))>1.01);assert.ok(Math.max(...poses.map(p=>p.scale))<1.025);
 const folded=poses.map((_,i)=>offerDealFrame({...a,x:0},{x:0,y:8,scale:.94,opacity:0},i/500,0));
 assert.ok(folded.every(p=>p.x===0&&p.opacity>=0&&p.opacity<=1&&p.scale>.92));
});
