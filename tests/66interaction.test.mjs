import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {floatingTone,floatingTones} from '../src/scripts/floating-tone.ts';

test('floating actions cycle through all brand tones and remain distinct from each sampled surface',()=>{
 for(const offset of [1,2]){
  assert.deepEqual(new Set([0,1,2,3].map(section=>floatingTone(section,offset))),new Set(floatingTones));
  for(let section=-4;section<12;section++)for(const surface of floatingTones)assert.notEqual(floatingTone(section,offset,surface),surface);
 }
});

test('beard artwork keeps separate sources and the owner-requested reflection',()=>{
 const photos=JSON.parse(readFileSync(new URL('../content/service-photos.json',import.meta.url)));
 assert.notEqual(photos.images['coloring-14360785'].sourceSha256,photos.images['coloring-11066470'].sourceSha256);
 assert.equal(photos.images['coloring-14360785'].mirror,true);
 assert.notEqual(photos.images['coloring-11066470'].mirror,true);
});

test('the edited question preserves the original interview and every answer',()=>{
 const article=JSON.parse(readFileSync(new URL('../content/master-articles/svetlana-demina.json',import.meta.url)));
 const question=article.sections.flatMap(section=>section.blocks).find(block=>block.id==='q05');
 assert.match(question.question,/не держала/);
 assert.match(question.displayQuestion,/Профессиональное/);
 assert.ok(question.paragraphs.length);
});
