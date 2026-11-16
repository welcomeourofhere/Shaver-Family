import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const design=JSON.parse(readFileSync(new URL('../src/config/design.json',import.meta.url)));
const palette=Object.fromEntries(['red','blue','yellow','ink','paper'].map(name=>[name,design.base[`--${name}`]]));
function luminance(hex){return hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0)}
function contrast(a,b){const values=[luminance(a),luminance(b)].sort((a,b)=>a-b);return(values[1]+.05)/(values[0]+.05)}
test('dark headings stay yellow while scrollbars retain the standard brand red',()=>{
 assert.equal(design.dark['--heading-color'],'var(--yellow)');
 assert.equal(design.base['--heading-color'],'var(--red)');
 assert.equal(design.base['--scrollbar-thumb'],'var(--red)');
 assert.equal(design.dark['--scrollbar-thumb'],'var(--red)');
 assert.equal(design.dark['--red'],undefined);
});
test('each coloured surface has complete action states that stay visible and readable',()=>{
 assert.deepEqual(Object.keys(design.actionBySurface).sort(),Object.keys(design.selectionBySurface).sort());
 for(const[surface,roles]of Object.entries(design.actionBySurface)){
  assert.deepEqual(Object.keys(roles).sort(),['primary','secondary','red','blue'].sort());
  for(const[role,tone]of Object.entries(roles)){
   assert.ok(palette[tone],`${surface}/${role}: unknown palette colour`);
   assert.notEqual(tone,surface,`${surface}/${role}: hover disappears into its surface`);
   const foreground=['paper','yellow'].includes(tone)?'ink':'paper';
   assert.ok(contrast(palette[tone],palette[foreground])>=4.5,`${surface}/${role}: text contrast`);
  }
  const foreground=surface==='yellow'?'ink':'paper';
  assert.ok(contrast(palette[surface],palette[foreground])>=3,`${surface}: focus ring contrast`);
 }
});
