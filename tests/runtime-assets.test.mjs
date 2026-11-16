import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sharp from 'sharp';
import {parse} from 'parse5';

const json=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const publicHashes=new Map(json('deploy/media-lock.json').files.map(item=>[item.sourcePath,item.sourceSha256]));
const bytes=url=>{assert.match(url,/^\/(?:media|reference|brand|fonts|audio|offer-icons)\//);assert.ok(!url.includes('..')&&!url.includes('\\'));return readFileSync(new URL('../public'+url,import.meta.url));};
const sha=body=>createHash('sha256').update(body).digest('hex');
async function variants(image){
 assert.ok(image.alt?.trim());assert.ok(image.variants.length>0);
 for(const item of image.variants){
  const body=bytes(item.url),meta=await sharp(body).metadata();
  assert.equal(sha(body),item.sha256??publicHashes.get(item.url.slice(1)),item.url);assert.equal(meta.width,item.width,item.url);assert.equal(meta.height,item.height,item.url);
  assert.ok(item.width>0&&item.height>0);
 }
}
const nodes=node=>[node,...(node.childNodes??[]).flatMap(nodes)],attr=(node,name)=>node.attrs?.find(a=>a.name===name)?.value;
const text=node=>node.value??(node.childNodes??[]).map(text).join(''),normal=value=>value.replace(/\s+/gu,' ').trim();

test('active services, offer posters, editorial images and every review use verified public derivatives',async()=>{
 const catalogue=json('content/service-catalog.json'),services=json('content/service-photos.json'),offers=json('content/offers.json'),posters=json('content/offer-poster-sources.json');
 for(const service of catalogue.categories.flatMap(c=>c.services))await variants(services.images[service.id]);
 assert.deepEqual(posters.images.map(p=>p.id),offers.offers.map(o=>o.id));
 for(const poster of posters.images)await variants({...poster,alt:poster.id});
 for(const image of json('content/editorial-images.json').images)await variants(image);
 const reviews=json('content/reviews.json'),media=json('content/review-media.json');
 assert.equal(reviews.length,8);assert.deepEqual(media.reviews.map(r=>r.id),reviews.map(r=>r.id));
 for(const review of media.reviews)for(const photo of review.photos)await variants({...photo,alt:photo.alt??review.id});
});

test('current separate fair-price figures retain genuine alpha without requiring original artwork',async()=>{
 const artwork=json('content/fair-price-artwork.json');
 assert.deepEqual(artwork.separateFigures.items.map(item=>item.id),['svetlana','sonya']);
 for(const figure of artwork.separateFigures.items){
  const body=bytes(figure.url),stats=await sharp(body).stats();
  assert.equal(sha(body),figure.sha256);assert.equal(stats.channels.at(-1).min,0);assert.equal(stats.channels.at(-1).max,255);
 }
});

test('all six full interviews and used carousel frames render from the public authored catalogue',async()=>{
 const team=json('content/team.json').masters,home=parse(readFileSync(new URL('../dist/index.html',import.meta.url),'utf8'));
 const articles=readdirSync(new URL('../content/master-articles/',import.meta.url)).filter(name=>name.endsWith('.json')&&!name.endsWith('.media.json')).map(name=>json('content/master-articles/'+name));
 assert.equal(articles.length,6);assert.deepEqual(new Set(articles.map(a=>a.masterId)),new Set(team.map(m=>m.id)));
 for(const article of articles){
  const media=json(`content/master-articles/${article.slug}.media.json`),blocks=article.sections.flatMap(s=>s.blocks),used=new Set([article.cover,...blocks.flatMap(b=>b.kind==='photos'?b.images:[])]);
  assert.deepEqual(new Set(Object.keys(media)),used);
  for(const id of used)await variants(media[id]);
  const page=parse(readFileSync(new URL(`../dist/masters/${article.slug}/index.html`,import.meta.url),'utf8'));
  const expected=[article.title,...(article.lead??[]),...article.sections.flatMap(s=>[...(s.intro??[]),...s.blocks.flatMap(b=>b.kind==='qa'?[b.question,...b.paragraphs]:b.kind==='text'?b.paragraphs:[])]),article.closing.title,...article.closing.paragraphs].map(normal).filter(Boolean);
  for(const document of [home,page]){
   const all=nodes(document),stories=all.filter(n=>n.tagName==='article'&&attr(n,'data-article-slug')===article.slug);assert.equal(stories.length,1,article.slug);
   const story=stories[0],copy=normal(text(story));for(const paragraph of expected)assert.ok(copy.includes(paragraph),article.slug+': '+paragraph);
   const images=nodes(story).filter(n=>n.tagName==='img');assert.equal(images.length,used.size);
   for(const id of used)assert.ok(images.some(image=>{const url=new URL(attr(image,'src'),'https://soyuz.local');return media[id].variants.some(v=>v.url===url.pathname&&url.searchParams.get('v')===v.sha256.slice(0,12));}),article.slug+': '+id);
   assert.ok(all.some(n=>attr(n,'data-booking-url')===team.find(m=>m.id===article.masterId).bookingUrl));
  }
 }
});

test('delivered hero and review videos keep their recorded bytes and faststart H264 structure',()=>{
 const hero=json('content/hero-media.json').playback,reviews=json('content/review-media.json').reviews;
 for(const video of [hero,...reviews.flatMap(r=>r.video?[r.video]:[])]){
  const body=bytes(video.url);assert.equal(sha(body),video.sha256);if(video.bytes)assert.equal(body.length,video.bytes);
  const atoms=[];for(let offset=0;offset<body.length;){const size=body.readUInt32BE(offset);assert.ok(size>=8&&offset+size<=body.length);atoms.push(body.toString('ascii',offset+4,offset+8));offset+=size;}
  assert.equal(atoms[0],'ftyp');assert.ok(atoms.indexOf('moov')>0&&atoms.indexOf('moov')<atoms.indexOf('mdat'));assert.ok(body.includes(Buffer.from('avc1')));
 }
});
