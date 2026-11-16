import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sharp from 'sharp';
import {springProgress, springCSS, stepSpring} from '../src/config/spring.ts';
import offers from '../content/offers.json' with {type:'json'};
import team from '../content/team.json' with {type:'json'};
import artwork from '../content/fair-price-artwork.json' with {type:'json'};
import feedback from '../src/config/feedback.json' with {type:'json'};

test('one gentle oscillator drives CSS and scripted springs, settles and survives interruption',()=>{
  const curve=Array.from({length:1001},(_,i)=>springProgress(i/1000));
  assert.equal(curve[0],0);assert.equal(curve.at(-1),1);
  assert.ok(Math.max(...curve)>1.06&&Math.max(...curve)<1.12);
  assert.ok(curve.every(Number.isFinite));assert.match(springCSS,/^linear\(/);
  let s={value:0,velocity:0};
  for(let i=0;i<30;i++)s=stepSpring(s.value,s.velocity,1,1/60);
  assert.ok(Math.abs(s.value-1)<.005);
  const velocity=s.velocity;s=stepSpring(s.value,velocity,0,1/60);
  for(let i=0;i<120;i++)s=stepSpring(s.value,s.velocity,0,1/60);
  assert.ok(Math.abs(s.value)<.00001&&Math.abs(s.velocity)<.00001);
});
test('honest price keeps owner minimum and first-visit-to-master eligibility with real destinations',()=>{
  const o=offers.offers.find(o=>o.id==='honest-price');
  assert.equal(o.minimumPrice,500);assert.equal(o.firstVisitToMasterOnly,true);
  assert.deepEqual(o.eligibleMasterIds,['souz-sonya-kid','souz-svetlana']);
  assert.deepEqual(o.eligibleMasterIds.map(id=>team.masters.find(m=>m.id===id).bookingUrl),['https://n2266404.yclients.ru/','https://n2440449.yclients.ru/']);
  assert.match(o.summary,/500 ₽/);assert.match(o.description,/первый визит именно/);
});
test('masters artwork has genuine transparency and recorded local source/delivery hashes',async()=>{
  const digest=p=>createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex');
  assert.equal(digest(artwork.source),artwork.sourceSha256);
  assert.equal(digest('public'+artwork.url),artwork.sha256);
  const image=sharp(readFileSync(new URL('../public'+artwork.url,import.meta.url)));
  const meta=await image.metadata();assert.ok(meta.hasAlpha);
  const stats=await image.stats();assert.equal(stats.channels.at(-1).min,0);assert.equal(stats.channels.at(-1).max,255);
});
test('retro audio stays quiet at source and at the shared player',()=>{
  const manifest=JSON.parse(readFileSync(new URL('../content/feedback-sources.json',import.meta.url)));
  assert.ok(feedback.volume<=.18);
  for(const clip of manifest.clips)assert.ok(clip.peak<=.25&&clip.rms<.15);
});
