import {test} from 'node:test';
import assert from 'node:assert/strict';
import {swipeDirection,nearestRailStop} from '../src/scripts/gesture-math.ts';

test('intentional travel and same-direction velocity select a single neighboring card',()=>{
 assert.equal(swipeDirection(-100,0,390),1);assert.equal(swipeDirection(100,0,390),-1);
 assert.equal(swipeDirection(-25,-.6,300),1);assert.equal(swipeDirection(25,.6,300),-1);
 assert.equal(swipeDirection(-4,-3,300),0);assert.equal(swipeDirection(-20,2,300),0);
 assert.equal(swipeDirection(-100,-2,300,true),0);
});
test('rail magnet chooses a real stop, bounds velocity and has an empty fallback',()=>{
 assert.equal(nearestRailStop([0,320,640],290),320);
 assert.equal(nearestRailStop([0,320,640],170,-1),0);
 assert.equal(nearestRailStop([0,320,640],170,1),320);
 assert.equal(nearestRailStop([0,320,640],0,-100),0);
 assert.equal(nearestRailStop([],200),0);
});
