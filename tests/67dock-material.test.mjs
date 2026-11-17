import { test } from 'node:test';
import assert from 'node:assert/strict';
import { boundedSpringProgress, boundedMaterialShape, springProgress, spring } from '../src/config/spring.ts';
import {floatingTones,floatingActionTone} from '../src/scripts/floating-tone.ts';
import design from '../src/config/design.json' with {type:'json'};
import designTokens from '../src/config/design.ts';

test('bounded dock material keeps shape and alpha moving until the shared endpoint', () => {
  // The previous underdamped response crossed 1 before half the context duration.
  // Clamping it made height/colour/fades finish while the animation was still running.
  assert.ok(springProgress(.5, spring.windowDamping) > 1);
  const values=Array.from({length:241},(_,i)=>boundedSpringProgress(i/240));
  assert.equal(values[0],0);
  assert.equal(values.at(-1),1);
  for(let i=1;i<values.length;i++) {
    assert.ok(values[i]>=values[i-1] && values[i]<=1,'No reverse motion or overshoot at a material boundary');
    if(i<values.length-1)assert.ok(values[i]<1,'The endpoint must not be clipped early');
  }
  assert.ok(boundedSpringProgress(.45)<.95,'A late first RAF still sees an intermediate material pose');
  assert.ok(boundedSpringProgress(.8)>.98 && boundedSpringProgress(.8)<1,'The final part settles without an idle plateau');
  assert.equal(boundedSpringProgress(-.1),0);
  assert.equal(boundedSpringProgress(1.1),1);
});

test('painted material has visible elastic tension, while both endpoints release exactly',()=>{
  assert.deepEqual(boundedMaterialShape(0,.12),{x:1,y:1});
  assert.deepEqual(boundedMaterialShape(1,.12),{x:1,y:1});
  const frames=Array.from({length:61},(_,i)=>boundedMaterialShape(i/60,.12));
  assert.ok(frames.some(frame=>frame.x<.97&&frame.y>1.04),'The actual painted object visibly compresses and stretches');
  assert.ok(frames.every(frame=>frame.x>.9&&frame.x<=1&&frame.y>=1&&frame.y<1.15),'Strain stays finite and restrained');
  for(let i=0;i<=60;i++)assert.deepEqual(boundedMaterialShape(i/60,0),{x:1,y:1});
});

test('dock action partners vary through the existing surface registry with readable contrast',()=>{
  const luminance=hex=>hex.slice(1).match(/../g).map(value=>parseInt(value,16)/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
  const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
  const pairs=new Set();
  for(const tone of floatingTones){
    const roles=design.actionBySurface[tone],primary=roles.primary,secondary=roles.blue;
    assert.notEqual(primary,secondary);assert.notEqual(primary,tone);assert.notEqual(secondary,tone);
    pairs.add(`${primary}/${secondary}`);
    for(const partner of[primary,secondary]){
      const foreground=['yellow','paper'].includes(partner)?'ink':'paper';
      assert.ok(contrast(design.base[`--${partner}`],design.base[`--${foreground}`])>=4.5,`${tone}/${partner} text contrast`);
    }
    const menuRoles=design.actionBySurface[floatingActionTone(tone,true)];
    assert.notEqual(menuRoles.primary,'paper');assert.notEqual(menuRoles.blue,'paper');
    for(const mode of['panel','menu']){
      const actionTone=floatingActionTone(tone,mode==='menu'),backing=mode==='menu'?'paper':tone;
      const roleColors=['primary','secondary','primary-active','secondary-active'].map(role=>{
        const prefix=`--dock-${actionTone}-${mode}-${role}`;
        const color=designTokens.base[`${prefix}-bg`].match(/^var\(--(.+)\)$/)[1];
        const foreground=designTokens.base[`${prefix}-fg`].match(/^var\(--(.+)\)$/)[1];
        assert.notEqual(color,backing,`${tone}/${mode}/${role} must remain visible against its backing`);
        assert.ok(contrast(design.base[`--${color}`],design.base[`--${foreground}`])>=4.5,`${tone}/${mode}/${role} contrast`);
        return color;
      });
      assert.equal(new Set(roleColors).size,4,'Primary and secondary normal/active partners remain distinct');
    }
  }
  assert.equal(pairs.size,4,'Changing the plate also changes the primary/secondary partner combination');
  assert.equal(designTokens.base['--action-primary-bg'],design.base['--action-primary-bg'],'Other page actions keep their existing roles');
});

test('bounded material interpolates both geometry directions while button targets stay at least 44px',()=>{
  for(const [before,after,buttonBefore,buttonAfter]of[[56,72,44,56],[72,56,56,44]]) {
    const heights=[],targets=[];
    for(let i=0;i<=60;i++) {
      const p=boundedSpringProgress(i/60);
      heights.push(before+(after-before)*p);
      targets.push(buttonBefore+(buttonAfter-buttonBefore)*p);
    }
    assert.equal(heights[0],before);
    assert.equal(heights.at(-1),after);
    assert.ok(Math.abs(heights[1]-before)<1,'The first sample retains the released geometry instead of jumping to the final floor');
    assert.ok(heights.slice(1,-1).every(h=>h>Math.min(before,after)&&h<Math.max(before,after)));
    assert.ok(targets.every(h=>h>=44),'Geometry interpolation never scales a control below the actual target floor');
  }
});
