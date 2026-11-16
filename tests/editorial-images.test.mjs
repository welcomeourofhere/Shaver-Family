import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import images from '../content/editorial-images.json' with {type:'json'};
import site from '../content/site.json' with {type:'json'};

test('four owner originals keep their hashes and aspect ratios in responsive editorial slots',()=>{
 const digest=path=>createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex');
 assert.equal(images.images.length,4);assert.deepEqual(new Set(images.images.map(i=>i.slot)),new Set(['about:haircut','about:beard','about:team','about:place']));
 for(const image of images.images){
  assert.equal(digest(image.source),image.sourceSha256);assert.ok(image.alt.startsWith('Сотрудница СОЮЗа'));
  for(const variant of image.variants){assert.equal(digest('public'+variant.url),variant.sha256);assert.ok(variant.width<=image.sourceSize[0]);assert.ok(Math.abs(variant.width/variant.height-image.sourceSize[0]/image.sourceSize[1])<.001);}
 }
 const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
 const about=html.match(/<section\b[^>]*id="about"[^>]*>([\s\S]*?)<\/section>/)[0];
 for(const image of images.images){assert.ok(about.includes(image.variants[0].url),image.slot);assert.ok(!html.replace(about,'').includes(image.variants[0].url),'Owner photo used outside About');}
});
test('MAX uses the owner public profile in all four shared contact groups',()=>{
 assert.equal(site.maxUrl,'https://max.ru/u/f9LHodD0cOJ4rurD35gvwHJ5jR1Cy1N_MbuZCA8BlA3k2BfpFkVYZkD2FKo');
 const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
 const entries=[...html.matchAll(/<a[^>]*href="([^"]+)"[^>]*data-contact-channel="max"/g)];
 assert.equal(entries.length,4);assert.ok(entries.every(entry=>entry[1]===site.maxUrl));
});


