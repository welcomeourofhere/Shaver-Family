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
  assert.deepEqual(await prepareMedia(source,{root,download}),result);assert.equal(calls,1);
  await fs.unlink(path.join(root,new URL(result.variants[0].url).pathname.replace('/Shaver-Family/','')));
  assert.deepEqual(await prepareMedia(source,{root,download}),result);assert.equal(calls,2);
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
