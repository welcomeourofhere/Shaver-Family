import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {businessStatus} from '../src/scripts/business-clock.ts';
const read=path=>readFileSync(new URL('../'+path,import.meta.url));
test('business hours use Moscow clock, opening/closing boundaries and overnight countdown',()=>{
 for(const [time,state,text]of [['06:59','closed','1 мин'],['07:00','open','Открыто сейчас'],['17:00','closing','2 ч'],['18:59','closing','1 мин'],['19:00','closed','12 ч'],['23:00','closed','8 ч']]){
  const actual=businessStatus(new Date(`2026-11-14T${time}:00Z`),'10:00–22:00');assert.equal(actual.state,state);assert.ok(actual.text.includes(text));
 }
});
test('Darya interview preserves all supplied paragraphs and 24 original photos',()=>{
 const article=JSON.parse(read('content/master-articles/darya-merzlyakova.json')),media=JSON.parse(read('content/master-articles/darya-merzlyakova.media.json'));
 const source=read(article.source.file),lines=source.toString('utf8').split(/\r?\n/).filter(Boolean),questions=article.sections.flatMap(s=>s.blocks.filter(b=>b.kind==='qa'));
 assert.equal(article.masterId,'souz-darya');assert.equal(questions.length,34);assert.equal(Object.keys(media).length,24);
 assert.equal(createHash('sha256').update(source).digest('hex'),article.source.sha256);
 const copy=[article.title,...article.sections.flatMap(s=>[...(s.intro||[]),...s.blocks.flatMap(b=>b.kind==='qa'?[b.question,...b.paragraphs]:[])]),article.closing.title,...article.closing.paragraphs];
 for(const line of lines)if(!line.includes('изображение №')&&line!=='Даша и Соня все работы')assert.ok(copy.includes(line),line);
 for(const photo of Object.values(media)){assert.equal(createHash('sha256').update(read(photo.source)).digest('hex'),photo.sourceSha256);for(const v of photo.variants)assert.equal(createHash('sha256').update(read('public'+v.url)).digest('hex'),v.sha256);}
});
test('service copy has comparable complete lengths and identical descriptions for repeated services',()=>{
 const catalogue=JSON.parse(read('content/service-catalog.json')),names=new Map();
 for(const service of catalogue.categories.flatMap(c=>c.services)){
  assert.ok(service.description.length>=145&&service.description.length<=215,service.id);assert.ok(service.description.endsWith('.'));
  assert.ok(!/[:;—]|это не просто|это больше чем/iu.test(service.description));
  if(names.has(service.name))assert.equal(service.description,names.get(service.name));else names.set(service.name,service.description);
 }
});
