import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import sharp from 'sharp';
import {prepareMedia,prepareFeed} from './news_images.mjs';

const source={type:'photo',full_url:'https://sun9-1.userapi.com/test.jpg',thumb_url:'https://sun9-1.userapi.com/thumb.jpg'};
test('responsive widths, aspect ratio, bounded pixels and cache recovery',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-variants-'));
 try {
  const raw=await sharp({create:{width:900,height:1200,channels:3,background:'#e61010'}}).jpeg().toBuffer();let calls=0;
  const download=async()=>{calls++;return raw;};
  const result=await prepareMedia(source,{root,download});
  assert.deepEqual(result.variants.map(v=>v.width),[160,320,640,900]);
  assert.ok(result.variants.every(v=>Math.abs(v.height-v.width*4/3)<=.5&&v.bytes>0&&v.url.endsWith('.webp')));
  for(const v of result.variants){const file=path.join(root,new URL(v.url).pathname.replace('/Shaver-Family/',''));const meta=await sharp(await fs.readFile(file)).metadata();assert.equal(meta.width,v.width);assert.equal(meta.format,'webp');}
  assert.equal(result.original_full_url,source.full_url);
  const video=await prepareMedia({...source,type:'video',player_url:'https://vk.com/video_ext.php?oid=-42&id=3'},{root,download});
  assert.equal(video.type,'video');assert.equal(video.player_url,'https://vk.com/video_ext.php?oid=-42&id=3');assert.deepEqual(video.variants,result.variants);
  assert.deepEqual(await prepareMedia(source,{root,download}),result);assert.equal(calls,2);
  await fs.unlink(path.join(root,new URL(result.variants[0].url).pathname.replace('/Shaver-Family/','')));
  assert.deepEqual(await prepareMedia(source,{root,download}),result);assert.equal(calls,3);
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('a failed video cover keeps the actual post, poster URL and player instead of failing the whole feed',async()=>{
 const item={id:5,owner_id:-42,media:{...source,type:'video',player_url:'https://vk.com/video_ext.php?oid=-42&id=3'}};
 const result=await prepareFeed({ok:true,items:[item]},{download:async()=>{throw new Error('CDN unavailable');}});
 assert.equal(result.items[0].media.player_url,item.media.player_url);assert.equal(result.items[0].media.thumb_url,source.thumb_url);assert.equal(result.items[0].media.optimization_status,'original-source');
});

test('VK clip posters on the exact OK CDN host are optimised without enlargement',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-clip-'));
 try {
  const raw=await sharp({create:{width:130,height:96,channels:3,background:'#777777'}}).jpeg().toBuffer();
  const item={...source,type:'video',full_url:'https://iv.okcdn.ru/clip.jpg'};
  const r=await prepareMedia(item,{root,download:async()=>raw});
  assert.deepEqual(r.variants.map(v=>v.width),[130]);assert.equal(r.variants[0].height,96);
  await assert.rejects(prepareMedia({...item,full_url:'https://evil.iv.okcdn.ru/clip.jpg'},{root,download:async()=>raw}));
  await assert.rejects(prepareMedia({...item,full_url:'https://iv.okcdn.ru.evil.example/clip.jpg'},{root,download:async()=>raw}));
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('feed keeps text, counts and URLs; reruns use original images; failures propagate',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-feed-'));
 try {
  const raw=await sharp({create:{width:320,height:240,channels:3,background:'#777777'}}).jpeg().toBuffer();let calls=0;
  const download=async()=>{calls++;return raw;};const item={id:1,text:'Первая строка\n\nВторая строка',likes:17,views:90,link:'https://vk.com/wall-1_1',media:source};
  const result=await prepareFeed({ok:true,items:[item]},{root,download});
  assert.equal(result.items[0].text,item.text);assert.equal(result.items[0].likes,17);assert.equal(result.items[0].link,item.link);
  assert.deepEqual(await prepareFeed(result,{root,download}),result);assert.equal(calls,1);
  await assert.rejects(prepareFeed({ok:false,items:[]}));
  await assert.rejects(prepareMedia({...source,full_url:'http://sun9-1.userapi.com/test.jpg'},{root,download}));
  await assert.rejects(prepareMedia({...source,full_url:'https://sun9-1.userapi.com/other.jpg'},{root,download:async()=>{throw new Error('offline');}}));
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('video selection compares decoded pixels, removes certified black bars and reuses its cache',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-real-cover-'));
 try {
  const portrait=await sharp({create:{width:450,height:800,channels:3,background:'#aa5544'}}).png().toBuffer();
  const letterboxed=await sharp({create:{width:1280,height:800,channels:3,background:'#000000'}})
    .composite([{input:portrait,left:415,top:0}]).png().toBuffer();
  const tiny=await sharp({create:{width:86,height:152,channels:3,background:'#337788'}}).png().toBuffer();
  const alternate='https://iv.okcdn.ru/frame.jpg';let downloads=0;
  const item={...source,type:'video',video_width:1080,video_height:1920,_poster_candidates:[{url:alternate,width:320,height:180}]};
  const download=async url=>{downloads++;return url===alternate?letterboxed:tiny;};
  const r=await prepareMedia(item,{root,download});
  assert.equal(r.width,450);assert.equal(r.height,800);assert.equal(r.poster_black_bars_removed,true);
  assert.equal(r.original_full_url,alternate);assert.ok(!('_poster_candidates' in r));
  const image=await sharp(await fs.readFile(path.join(root,new URL(r.full_url).pathname.replace('/Shaver-Family/','')))).raw().toBuffer({resolveWithObject:true});
  assert.ok(image.data[0]>100 && image.data[image.data.length-3]>100,'Neither outer edge is a black bar');
  assert.deepEqual(await prepareMedia(item,{root,download}),r);assert.equal(downloads,2);
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('photographic dark-coloured edges and photo posts are not automatically cropped',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-no-crop-'));
 try{
  const raw=await sharp({create:{width:800,height:450,channels:3,background:'#152c37'}}).png().toBuffer();
  const video=await prepareMedia({...source,type:'video',video_width:1080,video_height:1920},{root,download:async()=>raw});
  assert.equal(video.width,800);assert.equal(video.height,450);assert.equal(video.poster_black_bars_removed,false);
  const black=await sharp({create:{width:800,height:450,channels:3,background:'#000000'}}).png().toBuffer();
  const photo=await prepareMedia({...source,video_width:1080,video_height:1920},{root,download:async()=>black});
  assert.equal(photo.width,800);assert.equal(photo.height,450);
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
test('poster candidate failures do not discard a working alternate or allow an unrelated host',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-cover-fallback-'));
 try{
  const alternate='https://iv.okcdn.ru/frame.jpg',visited=[];
  const raw=await sharp({create:{width:360,height:640,channels:3,background:'#aa5544'}}).png().toBuffer();
  const r=await prepareMedia({...source,type:'video',video_width:1080,video_height:1920,
    _poster_candidates:[{url:'https://evil.example/image.jpg',width:2000,height:2000},{url:alternate,width:360,height:640}]},
    {root,download:async url=>{visited.push(url);if(url!==alternate)throw new Error('unavailable');return raw;}});
  assert.equal(r.width,360);assert.deepEqual(visited,[source.full_url,alternate]);
 } finally {await fs.rm(root,{recursive:true,force:true});}
});
