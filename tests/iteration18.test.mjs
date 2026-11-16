import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolveTheme} from '../src/scripts/theme.ts';
import {certificateWaveLevels} from '../src/scripts/certificate-order.ts';
import {newsActionTone} from '../src/scripts/news-tone.ts';
import {springProgress,spring} from '../src/config/spring.ts';
import catalog from '../content/service-catalog.json' with {type:'json'};
import photos from '../content/service-photos.json' with {type:'json'};
import font from '../content/display-font.json' with {type:'json'};
const read=p=>readFileSync(new URL('../'+p,import.meta.url));
const sha=p=>createHash('sha256').update(read(p)).digest('hex');
test('theme respects explicit choice and otherwise follows the system',()=>{
  assert.equal(resolveTheme('dark',false),'dark');assert.equal(resolveTheme('light',true),'light');
  assert.equal(resolveTheme('auto',true),'dark');assert.equal(resolveTheme(null,false),'light');assert.equal(resolveTheme('invalid',true),'dark');
});
test('certificate wave ranks selected card, neighbours and distant cards independently',()=>{
  assert.deepEqual(certificateWaveLevels(4,null),[0,1,2,3]);
  assert.deepEqual(certificateWaveLevels(4,2),[2,1,0,1]);
  assert.deepEqual(certificateWaveLevels(4,0),[0,1,2,3]);
  assert.deepEqual(certificateWaveLevels(4,3),[3,2,1,0]);
});
test('service posters cover active positions and original photography is retained',()=>{
  const ids=[...catalog.categories.flatMap(c=>c.services.map(s=>s.id)),...catalog.archivedServices.map(s=>s.id)];assert.deepEqual(Object.keys(photos.images).sort(),ids.sort());
  const original=JSON.parse(readFileSync(new URL('../content/service-photos-photography.json',import.meta.url)));assert.equal(new Set(Object.values(original.images).map(p=>p.sourceSha256)).size,29);for(const p of Object.values(original.images))for(const v of p.variants)assert.equal(sha('public'+v.url),v.sha256);
  for(const p of Object.values(photos.images)){
    assert.deepEqual(p.variants.map(v=>v.width),p.artwork?[600,1200]:[480,960]);
    for(const v of p.variants)assert.equal(sha('public'+v.url),v.sha256);
  }
});
function tables(data){const map={};for(let i=0;i<data.readUInt16BE(4);i++){const pos=12+i*16,offset=data.readUInt32BE(pos+8),length=data.readUInt32BE(pos+12);map[data.toString('ascii',pos,pos+4)]=data.subarray(offset,offset+length);}return map;}
test('web Molot removes old grid programs while preserving source, widths and character map',()=>{
  assert.equal(sha(font.source),font.sourceSha256);assert.equal(sha(font.output),font.sha256);
  const source=tables(read(font.source)),web=tables(read(font.output));
  for(const tag of ['fpgm','prep','cvt ']){assert.ok(source[tag]);assert.equal(web[tag],undefined);}
  assert.deepEqual(web.hmtx,source.hmtx);assert.deepEqual(web.cmap,source.cmap);
  assert.equal(web.head.readUInt16BE(16)&24,0);assert.equal(font.outlinesAndAdvancesUnchanged,true);
});
test('drawer spring remains monotonic while surface spring visibly settles',()=>{
  const drawer=Array.from({length:501},(_,i)=>springProgress(i/500,spring.drawerDamping));
  assert.ok(drawer.every((v,i)=>v>=0&&v<=1&&(!i||v>=drawer[i-1])));
  assert.ok(Math.max(...Array.from({length:501},(_,i)=>springProgress(i/500)))>1.06);
});

test('news actions use only brand colours with no adjacent repetition including loop seam',()=>{
  for(let count=2;count<=20;count++){
    const tones=Array.from({length:count},(_,i)=>newsActionTone(i,count));
    assert.ok(tones.every(t=>['red','blue','yellow'].includes(t)));
    assert.ok(tones.every((t,i)=>t!==tones[(i+1)%count]));
  }
});
test('springs become progressively calmer from cards to windows, menus and drawers',()=>{
  const peak=(d)=>Math.max(...Array.from({length:501},(_,i)=>springProgress(i/500,d)));
  const peaks=[spring.damping,spring.windowDamping,spring.popoverDamping,spring.drawerDamping].map(peak);
  assert.ok(peaks.every((v,i)=>!i||v<=peaks[i-1]));assert.ok(peaks[2]<1.02);
});
