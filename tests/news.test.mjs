import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validNewsFeed, newsImageURL, newsTitle} from '../src/scripts/news.ts';
const source = new URL('../content/news.json', import.meta.url);
const feed = JSON.parse(readFileSync(source,'utf8'));
test('ten real SOYUZ posts are unique, latest first, escaped as text and independently usable offline',()=>{
  assert.ok(validNewsFeed(feed));
  const live=JSON.parse(readFileSync(new URL('../public/data/news.json',import.meta.url),'utf8'));
  assert.ok(validNewsFeed(live));assert.ok(Date.parse(live.generatedAt)>=Date.parse(feed.generatedAt),'runtime snapshot can advance without rebuilding SSR');
  for(const snapshot of[feed,live])for(let i=0;i<snapshot.items.length;i++){
    const p=snapshot.items[i];
    assert.ok(newsTitle(p));
    if(i)assert.ok(Date.parse(snapshot.items[i-1].publishedAt)>=Date.parse(p.publishedAt));
    for(const v of p.image?.variants||[]){
      const local=new URL(newsImageURL(v.url,'https://soyuz.local/data/news.json')).pathname;
      assert.ok(existsSync(new URL('../public'+local,import.meta.url)));
      assert.equal(createHash('sha256').update(readFileSync(new URL('../public'+local,import.meta.url))).digest('hex'),v.sha256);
      assert.equal(newsImageURL(v.url,'https://raw.githubusercontent.com/owner/repo/main/public/data/news.json'),'https://raw.githubusercontent.com/owner/repo/main/public'+local);
    }
  }
});
test('news trust boundary rejects foreign walls, duplicate IDs, executable or external images and malformed data',()=>{
  for(const edit of [d=>d.items.pop(),d=>d.groupId=-1,d=>d.items[0].url='javascript:alert(1)',d=>d.items[1].id=d.items[0].id,d=>d.items.find(p=>p.image).image.variants[0].url='https://evil.test/1.webp',d=>d.items.find(p=>p.image).image.variants[0].url='../media/news/../../secret',d=>d.items[0].publishedAt='invalid',d=>d.generatedAt={toString:'invalid'},d=>d.items[0].publishedAt=[]]){
    const d=structuredClone(feed);edit(d);assert.equal(validNewsFeed(d),false);
  }
});

test('responsive news delivery allows three bounded variants up to 1600px',()=>{
 const d=structuredClone(feed),image=d.items.find(p=>p.image).image;
 const source=image.variants[0];image.variants=[640,1280,1600].map(width=>({...source,width}));assert.ok(validNewsFeed(d));
 image.variants[2].width=1601;assert.equal(validNewsFeed(d),false);
 image.variants[2].width=1600;image.variants.push({...source});assert.equal(validNewsFeed(d),false);
});

test('owner-excluded posts cannot return through a later runtime refresh',()=>{
 for(const id of ['1950','1941','1937','1943','1927','1935','1945','1955','1960','1914','1919','1923','1909','1911','1925','1948']){
  const candidate=structuredClone(feed);candidate.items[0].id=id;candidate.items[0].url=`https://vk.ru/wall-210007626_${id}`;
  assert.equal(validNewsFeed(candidate),false);
 }
});

test('malformed image variants are rejected without throwing or creating an ambiguous srcset',()=>{
 for(const variants of [[null],[12],[{url:null,width:640,height:640}],[{url:{toString:()=> '../media/news/abc.webp'},width:640,height:640}]]){
  const d=structuredClone(feed);d.items.find(p=>p.image).image.variants=variants;
  assert.equal(validNewsFeed(d),false);
 }
 const d=structuredClone(feed),image=d.items.find(p=>p.image).image,variant=image.variants[0];
 image.variants=[{...variant,width:640},{...variant,width:640}];assert.equal(validNewsFeed(d),false);
 image.variants=[{...variant,width:1280},{...variant,width:640}];assert.equal(validNewsFeed(d),false);
});
