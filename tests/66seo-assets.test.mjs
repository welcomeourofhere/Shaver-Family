import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sharp from 'sharp';
const root=new URL('../',import.meta.url);
const bytes=path=>readFileSync(new URL(path,root));
const json=path=>JSON.parse(bytes(path));
const sha=value=>createHash('sha256').update(value).digest('hex');

test('search copy names the actual business, services and current address without draft metadata',()=>{
 const seo=json('content/seo.json'),site=json('content/site.json');
 assert.ok(seo.title.includes('«'+site.brand+'»')&&seo.title.includes(site.city));
 assert.ok(seo.description.includes('стрижки')&&seo.description.includes('бороды')&&seo.description.includes('СПА'));
 assert.ok(seo.description.includes(site.address.replace('ул. ','')));
 assert.ok(!seo.description.includes(site.futureAddress));
 assert.ok(seo.description.length>=100&&seo.description.length<=180);
 assert.doesNotMatch(seo.description,/;|это не просто|это больше чем|это не только|лучший|гарантир/i);
 assert.equal(seo.status,'source-owned-release-metadata');
});

test('social and icon derivatives retain their inputs, pixel dimensions and immutable hashes',()=>{
 const source=json('content/seo-assets.json'),seo=json('content/seo.json');
 assert.equal(sha(bytes(source.generator)),source.generatorSha256);
 for(const input of source.sources)assert.equal(sha(bytes(input.path)),input.sha256,input.path);
 const design=json(source.designInputs.source);
 assert.deepEqual(source.designInputs,{source:'src/config/design.json',red:design.base['--red'],paper:design.base['--paper'],goldenRatio:design.scale.goldenRatio});
 assert.equal(sha(bytes('public/brand/favicon-red.svg')),'b73c1eee7a861e8b4c9944bee4f9b54bd8f7a5882f6601779ef3157c6c8af72c');
 assert.equal(seo.image,'/'+source.social.path.replace(/^public\//,''));
 assert.deepEqual([seo.imageWidth,seo.imageHeight,seo.imageType],[1200,630,'image/png']);
 for(const file of [source.social,...source.favicon.rasters]){
  const data=bytes(file.path);
  assert.equal(data.subarray(1,4).toString(),'PNG');
  assert.deepEqual([data.readUInt32BE(16),data.readUInt32BE(20)],[file.width,file.height]);
  assert.equal(data.length,file.bytes);assert.equal(sha(data),file.sha256);
 }
 assert.deepEqual(source.favicon.rasters.map(row=>row.width),[48,96,180]);
 assert.ok(source.social.bytes<400000,'The social image stays under 400 kB');
 const canvas=source.textGeometry.canvas,ratio=json('src/config/design.json').scale.goldenRatio;
 assert.equal(canvas.background,'rgb(196, 47, 42)');assert.equal(canvas.photoTop,0);
 assert.ok(Math.abs(canvas.columns[0]/canvas.columns[1]-ratio)<.001,'The composition uses the shared golden ratio');
});

test('favicon uses the ready-made circle with original letter fields, without requiring private originals in CI',async()=>{
 const favicon=json('content/seo-assets.json').favicon;
 assert.equal(favicon.source.sha256,'fc706affe04c6c2a9c5ce15604245b6a589e9981dfaac9c4a3d2ecebf5d9e05e');
 assert.deepEqual([favicon.source.width,favicon.source.height,favicon.source.bytes],[1000,1000,62240]);
 assert.deepEqual(favicon.sourceColors,{circle:'#c42f2a',wordmark:'#f6e8d3',signature:'#ffcc29'});
 const vector=bytes(favicon.svg.path),text=vector.toString();
 assert.equal(vector.length,favicon.svg.bytes);assert.equal(sha(vector),favicon.svg.sha256);
 assert.equal(favicon.svg.sourceSha256,'2072188966a68d37eb0caeb6fed3e32595853fce10aa3020616747e26710c2be');
 assert.doesNotMatch(text,/<(?:image|script|text|foreignObject)\b|@font-face|\bon\w+=/i);
 assert.match(text,/viewBox="0 0 1000 1000"/);assert.match(text,/#F6E8D3/);assert.match(text,/#FFCC29/);assert.match(text,/#C42F2A/);
 const {data,info}=await sharp(bytes('public/brand/favicon-96.png')).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let left=96,top=96,right=0,bottom=0;
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
  const i=(y*info.width+x)*4;
  if(data[i]>230&&data[i+1]>210&&data[i+2]>190&&data[i+3]>200){left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}
 }
 assert.ok(left>=12&&left<=16&&right>=80&&right<=84,'Keep original horizontal fields; do not enlarge toward the edges');
 assert.ok(top>=38&&top<=41&&bottom>=54&&bottom<=57,'Keep the standard circle wordmark position and height');
 let yellow=0;
 for(let i=0;i<data.length;i+=4)if(data[i]>230&&data[i+1]>170&&data[i+1]<225&&data[i+2]<100&&data[i+3]>200)yellow++;
 assert.ok(yellow>40,'Keep the original yellow BARBERSHOP signature');
});
