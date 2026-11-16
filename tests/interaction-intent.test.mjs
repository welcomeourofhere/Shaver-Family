import test from 'node:test';
import assert from 'node:assert/strict';
import {isKeyboardActivation,isMousePointer} from '../src/scripts/interaction-intent.ts';
test('pointer release keeps its magnetic motion while keyboard activation is immediate',()=>{
 for(const type of ['pointerup','pointerdown','pointermove','pointercancel','mouseup','touchend'])assert.equal(isKeyboardActivation({type,detail:0}),false,type);
 for(const type of ['keydown','keyup','keypress'])assert.equal(isKeyboardActivation({type}),true,type);
 assert.equal(isKeyboardActivation({type:'click',detail:0}),true);
 assert.equal(isKeyboardActivation({type:'click',detail:1}),false);
 assert.equal(isKeyboardActivation(),false);
});
test('point-sized unidentified desktop input does not turn touch or pen into mouse drag',()=>{
 assert.equal(isMousePointer({pointerType:'mouse',width:1,height:1}),true);
 assert.equal(isMousePointer({pointerType:'',width:1,height:1}),true);
 for(const pointerType of ['touch','pen'])assert.equal(isMousePointer({pointerType,width:1,height:1}),false);
 assert.equal(isMousePointer({pointerType:'',width:12,height:12}),false);
});
