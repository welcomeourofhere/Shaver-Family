import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sharp from 'sharp';
import article from '../content/master-articles/sofya-shalaginova.json' with {type:'json'};
import media from '../content/master-articles/sofya-shalaginova.media.json' with {type:'json'};
import sources from '../artifacts/master-articles/sofya-shalaginova/media-sources.json' with {type:'json'};
import team from '../content/team.json' with {type:'json'};

const file=path=>readFileSync(new URL('../'+path,import.meta.url));
const digest=path=>createHash('sha256').update(file(path)).digest('hex');
const questions=article.sections.flatMap(section=>section.blocks.filter(block=>block.kind==='qa'));

test('all 36 interview answers and the closing preserve the supplied text',()=>{
  assert.equal(digest(article.source.file),article.source.sha256);
  const lines=file(article.source.file).toString('utf8').split(/\r?\n/).map(line=>line.trim());
  assert.equal(questions.length,36);
  const copy=[article.title,...article.sections.flatMap(section=>[
    ...(section.intro??[]),...section.blocks.filter(block=>block.kind==='qa').flatMap(block=>[block.question,...block.paragraphs]),
  ]),article.closing.title,...article.closing.paragraphs];
  const captions=new Set(['ДО/ПОСЛЕ',...article.sections.flatMap(section=>section.blocks.filter(block=>block.kind==='photos').map(block=>block.caption))]);
  for(const line of lines.filter(line=>line&&!line.includes('изображение №')&&!captions.has(line)))
    assert.ok(copy.includes(line),'Missing source paragraph: '+line);
  for(const paragraph of copy) assert.ok(lines.includes(paragraph),'Changed paragraph: '+paragraph);
  for(const question of questions) assert.equal(lines[question.sourceLine-1],question.question);
  assert.equal(new Set(questions.map(question=>question.id)).size,36);
});

test('all 24 originals remain intact and the 22 displayed photographs keep their proportions',async()=>{
  assert.equal(sources.images.length,24);
  const used=new Set([article.cover,...article.sections.flatMap(section=>section.blocks.flatMap(block=>block.kind==='photos'?block.images:[]))]);
  assert.deepEqual(new Set(Object.keys(media)),used);
  assert.equal(used.size,22);
  for(const original of sources.images) assert.equal(digest(original.source),original.sha256,original.id);
  for(const photo of Object.values(media)) {
    assert.equal(digest(photo.source),photo.sourceSha256);
    assert.ok(photo.alt.trim());
    const original=await sharp(file(photo.source)).metadata();
    for(const variant of photo.variants) {
      assert.equal(digest('public'+variant.url),variant.sha256);
      const image=await sharp(file('public'+variant.url)).metadata();
      assert.equal(image.width,variant.width);assert.equal(image.height,variant.height);
      assert.ok(image.width<=original.width);
      assert.ok(Math.abs(image.width/image.height-original.width/original.height)<.002);
    }
  }
});

test('the same full interview renders in the master dialog and its own route with the right booking destination',()=>{
  const home=file('dist/index.html').toString('utf8').replaceAll('\u00a0',' ');
  const page=file(`dist/masters/${article.slug}/index.html`).toString('utf8').replaceAll('\u00a0',' ');
  const master=team.masters.find(master=>master.id===article.masterId);
  assert.ok(master);
  for(const html of [home,page]) {
    for(const question of questions) assert.ok(html.includes(question.question),question.id);
    for(const photo of Object.values(media)) assert.ok(html.includes(photo.variants[0].url));
    assert.ok(html.includes(`data-booking-url="${master.bookingUrl}"`));
  }
  assert.equal((page.match(/<h1\b/g)??[]).length,1);
  assert.ok(page.includes('href="/#masters"'));
  assert.ok(page.includes('href="/#services"'));
  const structured=[...page.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/g)].map(match=>JSON.parse(match[1]));
  assert.equal(structured.find(item=>item['@type']==='Article').headline,article.title);
});
