import {test} from 'node:test';
import assert from 'node:assert/strict';
import {modalDialogs} from '../src/scripts/modal-scroll-lock.ts';

test('unsupported modal selector never reaches the DOM parser or locks docked booking',()=>{
 const previous=globalThis.CSS,modal={getAttribute:()=>null,dataset:{}},docked={getAttribute:()=> 'false',dataset:{layout:'docked'}};
 try{
  for(const capability of [undefined,{supports:()=>false}]){
   globalThis.CSS=capability;
   const root={querySelectorAll(selector){assert.equal(selector,'dialog[open]');return[modal,docked]}};
   assert.deepEqual(modalDialogs(root),[modal]);
  }
  globalThis.CSS={supports:query=>{assert.equal(query,'selector(dialog:modal)');return true}};
  assert.deepEqual(modalDialogs({querySelectorAll(selector){assert.equal(selector,'dialog:modal');return[modal]}}),[modal]);
 }finally{if(previous===undefined)delete globalThis.CSS;else globalThis.CSS=previous;}
});
