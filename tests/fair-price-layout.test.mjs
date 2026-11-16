import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sharp from 'sharp';
import slogans from '../content/honest-price-slogans.json' with {type:'json'};
import artwork from '../content/fair-price-artwork.json' with {type:'json'};

test('ten original slogan proposals keep one explicit selected two-line heading',()=>{
 assert.equal(slogans.items.length,10);assert.equal(new Set(slogans.items.map(s=>s.lines.join(' '))).size,10);
 const selected=slogans.items.find(s=>s.id===slogans.selected);assert.equal(selected.lines.length,2);
 const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8').replaceAll('\u00a0',' ');
 for(const line of selected.lines)assert.ok(html.includes(line));
});
test('selected Soviet-clothing duo has traceable portraits and alpha without meadow layers',async()=>{
 const digest=p=>createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex');
 assert.equal(artwork.id,'poster-duo-soviet-v3');assert.deepEqual(artwork.references,['public/media/team/souz-sonya-kid.webp','public/media/team/souz-svetlana.webp']);
 for(const item of [artwork]){
  assert.equal(digest(item.source),item.sourceSha256);assert.equal(digest('public'+item.url),item.sha256);
  const stats=await sharp(readFileSync(new URL('../public'+item.url,import.meta.url))).stats();assert.equal(stats.channels.at(-1).min,0);assert.equal(stats.channels.at(-1).max,255);
 }
 assert.ok(artwork.variants.some(v=>v.id==='previous-poster'));
 const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');assert.doesNotMatch(html,/visit-field|fair-price-meadow-/);
});
test('separate figures preserve the original and retain traceable transparent sources',async()=>{
 assert.equal(artwork.separateFigures.editTarget,artwork.source);
 assert.deepEqual(artwork.separateFigures.items.map(x=>x.id),['svetlana','sonya']);
 for(const figure of artwork.separateFigures.items){
  const hash=path=>createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex');
  assert.equal(hash(figure.source),figure.sourceSha256);assert.equal(hash('public'+figure.url),figure.sha256);
  const stats=await sharp(readFileSync(new URL('../public'+figure.url,import.meta.url))).stats();
  assert.equal(stats.channels.at(-1).min,0);assert.equal(stats.channels.at(-1).max,255);
 }
});
