import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';

test('eight owner reviews retain their full paragraphs and confirmed original photographs',()=>{
 const reviews=JSON.parse(readFileSync(new URL('../content/reviews.json',import.meta.url),'utf8'));
 const media=JSON.parse(readFileSync(new URL('../content/review-media.json',import.meta.url),'utf8'));
 assert.equal(reviews.length,8);assert.deepEqual(media.reviews.map(item=>item.photos.length),[2,1,2,2,2,1,1,1]);
 for(const item of reviews){
  assert.equal(item.source,item.id==='review-08'?'owner-provided 2026-11-15':'owner-provided 2026-11-09');assert.equal(item.author,undefined);assert.equal(item.rating,undefined);
  assert.ok(item.text.every(paragraph=>typeof paragraph==='string'&&paragraph.trim()));
  for(const photo of media.reviews.find(entry=>entry.id===item.id).photos){
   const original=readFileSync(photo.original?resolve(photo.original):resolve('archive/owner-media/2026-11-09/reviews',photo.source));
   assert.equal(createHash('sha256').update(original).digest('hex'),photo.sha256);
   for(const variant of photo.variants)assert.ok(variant.url.startsWith('/media/reviews/')&&existsSync(resolve('public',variant.url.slice(1))));
  }
 }
 assert.equal(reviews[2].text.length,7);assert.match(reviews[2].text.at(-1),/ветер в волосах/);
 assert.match(reviews[6].video,/video-210007626_456239202/);
 assert.equal(reviews[7].text.length,4);assert.equal(reviews[7].text[2],'Вообщем все рекоменду , приду еще и остальным советую!');
 const video=media.reviews[6].video;
 assert.equal(reviews[6].videoLocal,video.url);assert.equal(reviews[6].videoEmbed,undefined);
 assert.equal(createHash('sha256').update(readFileSync(resolve(video.original))).digest('hex'),video.originalSha256);
 const output=readFileSync(resolve('public',video.url.slice(1)));
 assert.equal(createHash('sha256').update(output).digest('hex'),video.sha256);
 assert.ok(output.subarray(0,64).includes(Buffer.from('ftyp')));
 assert.ok(output.indexOf(Buffer.from('moov'))<output.indexOf(Buffer.from('mdat')),'MP4 metadata precedes media for progressive playback');
 assert.equal(video.videoCodec,'h264');assert.equal(video.audioCodec,'aac');assert.ok(video.duration>8&&video.duration<9);
});
