import {test} from 'node:test';
import assert from 'node:assert/strict';
import {syncBrowserTheme} from '../src/scripts/browser-theme.ts';

test('one resolved browser-theme metadata pair replaces media-qualified or native duplicates without styling the canvas',()=>{
 const originalDocument=globalThis.document,originalStyle=globalThis.getComputedStyle;
 const metas=[];
 const head={querySelectorAll(selector){return metas.filter(meta=>meta.name===selector.match(/name="([^"]+)"/)[1]);},append(meta){meta.parentNode=head;metas.push(meta);}};
 const createMeta=(name,content,media)=>({name,content,media,parentNode:null,removeAttribute(name){delete this[name];},remove(){metas.splice(metas.indexOf(this),1);this.parentNode=null;}});
 const root={dataset:{theme:'dark'},style:{}};
 try{
  globalThis.document={head,documentElement:root,createElement(){return createMeta('','','');}};
  globalThis.getComputedStyle=()=>({getPropertyValue:()=>' #18191a '});
  for(const [name,content,media]of [['theme-color','#ffffff','(prefers-color-scheme:light)'],['theme-color','#000000','(prefers-color-scheme:dark)'],['color-scheme','light dark',''],['color-scheme','light','']])head.append(createMeta(name,content,media));
  syncBrowserTheme();
  assert.deepEqual(metas.map(meta=>[meta.name,meta.content,meta.media]),[['theme-color','#18191a',undefined],['color-scheme','dark',undefined]]);
  assert.deepEqual(root.style,{},'root/body canvas ownership must remain CSS-owned');
  root.dataset.theme='light';globalThis.getComputedStyle=()=>({getPropertyValue:()=>'#fffcf7'});syncBrowserTheme();
  assert.deepEqual(metas.map(meta=>[meta.name,meta.content]),[['theme-color','#fffcf7'],['color-scheme','light']]);
  metas.splice(0);syncBrowserTheme();
  assert.deepEqual(metas.map(meta=>[meta.name,meta.content]),[['theme-color','#fffcf7'],['color-scheme','light']]);
 }finally{globalThis.document=originalDocument;globalThis.getComputedStyle=originalStyle;}
});
