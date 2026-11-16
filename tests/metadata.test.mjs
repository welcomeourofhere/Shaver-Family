import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from 'parse5';
const root=new URL('../dist/',import.meta.url);
const productionPages=JSON.parse(readFileSync(new URL('../deploy/production.json',import.meta.url),'utf8')).pages;
function files(path){return readdirSync(path,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(join(path,e.name)):e.name.endsWith('.html')?[join(path,e.name)]:[])}
function nodes(node){return [node,...(node.childNodes??[]).flatMap(nodes)]}
const attr=(node,name)=>node.attrs?.find(a=>a.name===name)?.value;
const text=node=>(node.childNodes??[]).map(c=>c.value??text(c)).join('');
test('all built routes have unique metadata, one H1, local image descriptions and truthful schema',()=>{
 const titles=new Set(),descriptions=new Set();
 const production=readFileSync(new URL('robots.txt',root),'utf8').includes('Allow: /');
 for(const file of files(fileURLToPath(root))){
  const all=nodes(parse(readFileSync(file,'utf8'))),title=text(all.find(n=>n.tagName==='title'));
  assert.ok(title.length>10);assert.ok(!titles.has(title),file);titles.add(title);
  const desc=attr(all.find(n=>n.tagName==='meta'&&attr(n,'name')==='description'),'content');
  assert.ok(desc?.length>40);assert.ok(!descriptions.has(desc),file);descriptions.add(desc);
  assert.equal(all.filter(n=>n.tagName==='h1').length,1,file);
  for(const key of ['og:title','og:description','og:image','og:image:alt'])assert.ok(all.some(n=>n.tagName==='meta'&&attr(n,'property')===key&&attr(n,'content')),`${file}: ${key}`);
  assert.ok(all.some(n=>n.tagName==='meta'&&attr(n,'name')==='twitter:card'));
  const privateRoute=/[\\/]previews[\\/]|[\\/]404\.html$/.test(file);
  const robots=attr(all.find(n=>n.tagName==='meta'&&attr(n,'name')==='robots'),'content');
  assert.equal(robots,production&&!privateRoute?'index, follow, max-image-preview:large':'noindex, nofollow');
  for(const img of all.filter(n=>n.tagName==='img')){
   assert.notEqual(attr(img,'alt'),undefined,file);
   assert.ok(Number(attr(img,'width'))>0&&Number(attr(img,'height'))>0,`${file}: image geometry`);
  }
  const schema=all.filter(n=>n.tagName==='script'&&attr(n,'type')==='application/ld+json').map(n=>JSON.parse(text(n)));
  assert.equal(schema[0]['@type'],'HairSalon');assert.equal(schema[0].address.streetAddress,'ул. Владимирская, 132');
  assert.equal(schema[0].aggregateRating,undefined);
  const canonical=all.find(n=>n.tagName==='link'&&attr(n,'rel')==='canonical');
  if(production){
   const path=file.slice(fileURLToPath(root).length).replaceAll('\\','/').replace(/(?:^|\/)index\.html$/,'').replace(/\.html$/,'');
   assert.equal(attr(canonical,'href'),'https://soyuz.hair/'+path);
   assert.equal(schema[0].url,'https://soyuz.hair/');
  }else assert.equal(canonical,undefined,'local previews retain noindex and omit production canonicals');
  const image=all.find(n=>n.tagName==='meta'&&attr(n,'property')==='og:image');
  assert.ok(existsSync(new URL('.'+new URL(attr(image,'content')).pathname,root)));
 }
 const expected=[...productionPages];
 if(existsSync(new URL('../src/pages/previews/',import.meta.url)))expected.push('/previews/contacts','/previews/contacts/overview','/previews/review-extras');
 const routes=files(fileURLToPath(root)).map(file=>'/'+file.slice(fileURLToPath(root).length).replaceAll('\\','/').replace(/(?:^|\/)index\.html$/,'').replace(/\.html$/,''));
 assert.deepEqual(routes.sort(),expected.sort(),'Production routes are exact; local workshop routes exist only with their preview sources');
 assert.equal(titles.size,expected.length);
});
