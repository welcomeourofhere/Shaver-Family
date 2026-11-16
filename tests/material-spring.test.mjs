import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spring, springShape} from '../src/config/spring.ts';

test('material deformation stretches and compresses with the shared spring and settles to an exact neutral shape',()=>{
  for(const damping of [spring.windowDamping,spring.popoverDamping]){
    const frames=Array.from({length:601},(_,i)=>springShape(i/600,.24,damping));
    assert.deepEqual(frames[0],{x:1,y:1});assert.deepEqual(frames.at(-1),{x:1,y:1});
    assert.ok(Math.max(...frames.map(f=>f.y))>1.08);
    assert.ok(Math.min(...frames.map(f=>f.y))<1);
    assert.ok(frames.every(f=>f.x>.9&&f.x<1.01&&f.y>.99&&f.y<1.13));
    frames.forEach((f,i)=>{const reverse=springShape(i/600,-.24,damping);assert.ok(Math.abs(f.y+reverse.y-2)<1e-12);});
  }
});
test('aspect weighting limits capsule edge travel while popover deformation remains legible',()=>{
  const ratio=64/1160/1.61803398875;
  for(let i=0;i<=600;i++){
    const header=springShape(i/600,.24,spring.windowDamping,ratio);
    assert.ok(Math.abs(header.x-1)*1160/2<3);
    const panel=springShape(i/600,.075,spring.popoverDamping);
    assert.ok(Math.abs(panel.y-1)<.04&&Math.abs(panel.x-1)<.025);
  }
});
