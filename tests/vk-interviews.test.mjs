import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {parse} from 'parse5';
import sharp from 'sharp';

const file=path=>readFileSync(new URL('../'+path,import.meta.url));
const json=path=>JSON.parse(file(path).toString('utf8').replace(/^\uFEFF/,''));
const hash=path=>createHash('sha256').update(file(path)).digest('hex');
const normal=text=>text.replaceAll('\u00a0',' ').replace(/\s+/g,' ').trim();
const nodes=node=>[node,...(node.childNodes??[]).flatMap(nodes)];
const attr=(node,name)=>node.attrs?.find(a=>a.name===name)?.value;
const text=node=>(node.childNodes??[]).map(c=>c.value??text(c)).join(' ');
const expected=[['milena-malyshevskaya','souz-milena',17,10],['sonya-kid','souz-sonya-kid',16,18],['svetlana-demina','souz-svetlana',9,6],['lyubov-shklyaeva','souz-lyubov',29,29]];

for(const [slug,masterId,questions,photos]of expected){
 const article=json(`content/master-articles/${slug}.json`),media=json(`content/master-articles/${slug}.media.json`),source=json(`artifacts/master-articles/${slug}/source-dom.json`),manifest=json(`artifacts/master-articles/${slug}/media-sources.json`);
 test(`${slug}: every source paragraph, continuation, caption and blitz answer stays in order`,()=>{
  assert.equal(article.masterId,masterId);assert.equal(hash(article.source.file),article.source.sha256);assert.equal(hash(`artifacts/master-articles/${slug}/source-dom.json`),manifest.domSha256);
  const blocks=article.sections.flatMap(s=>s.blocks),copy=[article.title,...(article.lead??[]),article.coverCaption??'',...blocks.flatMap(b=>b.kind==='qa'?[b.question,...b.paragraphs]:b.kind==='photos'?[b.caption]:b.paragraphs),article.closing.title,...article.closing.paragraphs].filter(Boolean).map(normal);
  const original=source.blocks.map(b=>b.tag==='FIGURE'?b.text.replace(/^\d+\s+из\s+\d+\s*/,''):b.text).filter(t=>t.trim()).map(normal);
  assert.deepEqual(copy,original);assert.equal(blocks.filter(b=>b.kind==='qa').length,questions);
  const lines=file(article.source.file).toString('utf8').split(/\r?\n/);
  for(const block of blocks.filter(b=>b.kind==='qa'))assert.equal(normal(lines[block.sourceLine-1]),normal(block.question));
  if(slug==='sonya-kid'){assert.equal(article.lead.length,2);assert.equal(article.coverCaption,'Ну что, поехали!');}
  if(slug==='svetlana-demina')assert.equal(blocks.filter(b=>b.kind==='text'&&b.quoted).length,1);
 });
 test(`${slug}: every carousel frame has an intact original and local variants without upscaling`,async()=>{
  assert.equal(manifest.images.length,photos);assert.equal(Object.keys(media).length,photos);
  const blocks=article.sections.flatMap(s=>s.blocks),used=[article.cover,...blocks.flatMap(b=>b.kind==='photos'?b.images:[])];assert.equal(used.length,photos);assert.equal(new Set(used).size,photos);
  for(const figure of source.blocks.filter(b=>b.tag==='FIGURE')){
   const count=figure.photoSources.reduce((n,s)=>n+s.sizes.length,0),entries=manifest.images.filter(p=>p.sourceBlock===figure.index);
   assert.equal(entries.length,count);const declared=/^\d+\s+из\s+(\d+)/.exec(figure.text);if(declared)assert.equal(count,Number(declared[1]));
  }
  for(const original of manifest.images){
   assert.equal(hash(original.source),original.sha256);const photo=media[original.id];assert.equal(photo.sourceSha256,original.sha256);assert.equal(photo.alt,json(`artifacts/master-articles/${slug}/alt-texts.json`)[original.id]);
   const meta=await sharp(file(photo.source)).metadata(),rotated=meta.orientation>=5&&meta.orientation<=8,w=rotated?meta.height:meta.width,h=rotated?meta.width:meta.height;
   assert.ok(photo.alt.length>15);assert.equal(original.width,meta.width);assert.equal(original.height,meta.height);assert.equal(meta.width,original.declaredWidth);assert.equal(meta.height,original.declaredHeight);
   for(const variant of photo.variants){assert.equal(hash('public'+variant.url),variant.sha256);const m=await sharp(file('public'+variant.url)).metadata();assert.equal(m.width,variant.width);assert.equal(m.height,variant.height);assert.ok(m.width<=w);assert.ok(Math.abs(m.width/m.height-w/h)<.003);}
  }
 });
 test(`${slug}: complete interview is present in the common dialog and its own page`,()=>{
  for(const path of ['dist/index.html',`dist/masters/${slug}/index.html`]){
   const all=nodes(parse(file(path).toString('utf8'))),story=all.find(n=>n.tagName==='article'&&attr(n,'data-article-slug')===slug);assert.ok(story,path);
   const content=normal(text(story));
   for(const block of source.blocks.filter(b=>b.tag!=='FIGURE'&&b.text.trim()))assert.ok(content.includes(normal(article.sections.flatMap(s=>s.blocks).find(b=>b.question===block.text)?.displayQuestion??block.text)),`${slug}: missing source block ${block.index}`);
   assert.equal(nodes(story).filter(n=>n.tagName==='img').length,photos);
   const actual=nodes(story).filter(n=>n.tagName==='img').map(n=>attr(n,'src').split('?')[0]);for(const photo of Object.values(media))assert.ok(actual.some(src=>photo.variants.some(v=>v.url===src)));
  }
 });
}
test('all six masters have exactly one complete interview catalogue entry',()=>{
 const articles=readdirSync(new URL('../content/master-articles/',import.meta.url)).filter(n=>n.endsWith('.json')&&!n.endsWith('.media.json')).map(n=>json('content/master-articles/'+n));
 assert.equal(articles.length,6);assert.deepEqual(new Set(articles.map(a=>a.masterId)),new Set(json('content/team.json').masters.map(m=>m.id)));
});
