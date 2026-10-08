import test from 'node:test';
import assert from 'node:assert/strict';
import {collectPosts,enrichPosts,normalizePost,pickMedia,playerUrl} from './news_posts.mjs';
const image={url:'https://sun9-1.userapi.com/test.jpg',width:1280,height:720};
const photo={type:'photo',photo:{sizes:[image]}};
const video={type:'video',video:{owner_id:-42,id:3,title:'Видео',image:[image],duration:10,access_key:'private-test-key'}};
const post=(id,more={})=>({owner_id:-42,id,date:id,text:'Текст\n\nАбзац',likes:{count:1234},views:{count:9121},attachments:[photo],...more});

test('group post counters and URL stay separate from repost counters; absent data is unknown',()=>{
 const item=normalizePost(post(7,{text:'',views:undefined,copy_history:[post(2,{owner_id:-100,likes:{count:1},text:'Репост'})]}));
 assert.equal(item.likes,1234);assert.equal(item.views,null);assert.equal(item.text,'Репост');assert.equal(item.link,'https://vk.com/wall-42_7');
 assert.equal(normalizePost(post(8,{likes:{count:0}})).likes,0);
});
test('pinned text/video posts are first, deduplicated and respect the existing blacklist',async()=>{
 let requests=0;
 const list=[post(1,{is_pinned:1,attachments:[]}),post(12,{attachments:[photo,video]}),post(11),post(11),post(10)];
 const items=await collectPosts(async()=>{requests++;return {items:list};},{ownerId:-42,limit:3,blacklist:new Set(['wall-42_10'])});
 assert.equal(requests,1);assert.deepEqual(items.map(x=>x.id),[1,12,11]);assert.equal(items[0].media,null);assert.equal(items[1].media.type,'video');
});
test('video API enrichment removes access keys and treats unavailable reach as unknown',async()=>{
 const item={...normalizePost(post(12)),media:pickMedia([video])};delete item.attachments;
 const calls=[];
 const {items,reachStatus}=await enrichPosts([item],async(method,params)=>{
  calls.push(method);
  if(method==='video.get'){assert.equal(params.videos,'-42_3_private-test-key');return {items:[{player:'https://vk.com/video_ext.php?oid=-42&id=3&hash=public-embed',can_view:1}]};}
  throw new Error('no statistics permission');
 },'2026-10-08T00:00:00Z');
 assert.deepEqual(calls,['video.get','stats.getPostReach']);assert.equal(reachStatus,'unavailable');assert.equal(items[0].reach,null);
 assert.match(items[0].media.player_url,/video_ext.php/);assert.ok(!JSON.stringify(items).includes('private-test-key'));
 assert.equal(playerUrl('https://evil.example/video_ext.php'), '');assert.equal(playerUrl('javascript:alert(1)'), '');assert.equal(playerUrl('https://vk.com@evil.example/video_ext.php'), '');
});
test('reach exports only exact aggregate while preserving public views',async()=>{
 const input={...normalizePost(post(9)),media:pickMedia([photo])};delete input.attachments;
 const r=await enrichPosts([input],async()=>[{post_id:9,reach_total:4555,sex_age:[{private:'never export'}]}],'now');
 assert.equal(r.reachStatus,'available');assert.equal(r.items[0].reach,4555);assert.equal(r.items[0].views,9121);assert.ok(!JSON.stringify(r).includes('sex_age'));
 assert.equal(pickMedia([{...video,video:{...video.video,can_view:0}},photo]).type,'photo');
});
