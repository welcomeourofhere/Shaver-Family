import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {heroVideoPlayback} from '../src/scripts/hero-video-playback.ts';
const flush=async()=>{for(let step=0;step<5;step++)await Promise.resolve();};
function fixture(){
 const attempts=[];let pauses=0;
 const video={paused:true,src:'',dataset:{videoSrc:'/approved-video.mp4'},getAttribute:name=>name==='src'?video.src:null,
  pause(){video.paused=true;pauses++;},play(){return new Promise((resolve,reject)=>attempts.push({resolve:()=>{video.paused=false;resolve();},reject}));}};
 return {video,attempts,owner:heroVideoPlayback(video),pauses:()=>pauses};
}

test('repeated visibility scheduling shares one pending play and keeps source lazy',async()=>{
 const f=fixture();f.owner.sync(false);assert.equal(f.video.src,'');assert.equal(f.pauses(),0);
 f.owner.sync(true);f.owner.sync(true);f.owner.sync(true);assert.equal(f.attempts.length,1);assert.equal(f.video.src,'/approved-video.mp4');
 f.attempts[0].resolve();await flush();assert.equal(f.video.dataset.heroVideoPlayback,'playing');f.owner.sync(true);assert.equal(f.attempts.length,1);
});

test('late completion after pause cannot restart video or overwrite its latest state',async()=>{
 const f=fixture();f.owner.sync(true);f.owner.sync(false);assert.equal(f.video.dataset.heroVideoPlayback,'paused');
 f.attempts[0].resolve();await flush();assert.equal(f.video.paused,true);assert.equal(f.video.dataset.heroVideoPlayback,'paused');
});

test('rapid play-pause-play ignores the old AbortError and keeps the newest successful attempt',async()=>{
 const f=fixture();f.owner.sync(true);f.owner.sync(false);f.owner.sync(true);assert.equal(f.attempts.length,2);
 f.attempts[0].reject(new Error('AbortError'));await flush();assert.equal(f.video.dataset.heroVideoPlayback,'pending');
 f.attempts[1].resolve();await flush();assert.equal(f.video.paused,false);assert.equal(f.video.dataset.heroVideoPlayback,'playing');
});

test('blocked autoplay leaves a retryable poster state rather than a stuck pending attempt',async()=>{
 const f=fixture();f.owner.sync(true);f.attempts[0].reject(new Error('NotAllowedError'));await flush();assert.equal(f.video.dataset.heroVideoPlayback,'blocked');
 f.owner.sync(true);assert.equal(f.attempts.length,2);f.attempts[1].resolve();await flush();assert.equal(f.video.dataset.heroVideoPlayback,'playing');
});

test('compact tap is independent of desktop focus pause and manual play can override reduced autoplay',()=>{
 const source=readFileSync(new URL('../src/scripts/hero-news.ts',import.meta.url),'utf8');
 assert.match(source,/focusin", \(\)=>\{if\(!compact\.matches\)pause\(\)\}/);
 assert.match(source,/visible&&!videoPaused&&!document\.hidden&&\(!reducedMotion\.matches\|\|videoExplicit\)/);
 assert.match(source,/if\(!event\.defaultPrevented&&compact\.matches/);
 assert.doesNotMatch(source,/void video\.play\(\)/);
});
