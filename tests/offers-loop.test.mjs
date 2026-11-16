import assert from "node:assert/strict";
import test from "node:test";
import { wrapOfferPhase,offerDealFrame } from "../src/scripts/offer-loop.ts";

test("offer phase wraps in both directions, including long drags", () => {
  assert.equal(wrapOfferPhase(-1, 10), 9);
  assert.equal(wrapOfferPhase(10, 10), 0);
  assert.equal(wrapOfferPhase(-31.5, 10), 8.5);
  assert.equal(wrapOfferPhase(125.25, 10), 5.25);
});
test('held dragging follows the pointer linearly and reverses without temporal easing',()=>{
 const from={x:300,y:0,scale:1,opacity:1},to={x:0,y:40,scale:.9,opacity:0};
 for(const progress of [0,.1,.25,.5,.75,1,.75,.25,0]){
  const pose=offerDealFrame(from,to,progress,.1,true);
  assert.equal(pose.x,300*(1-progress));assert.equal(pose.y,40*progress);
  assert.equal(pose.opacity,1-progress);assert.equal(pose.scale,1+(.9-1)*progress);
 }
});

