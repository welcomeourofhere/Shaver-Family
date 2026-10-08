import test from 'node:test';import assert from 'node:assert/strict';
import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import {retainFeedVersions} from './news_retention.mjs';
test('current and five previous versions preserve shared files and remove only obsolete owned media',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'news-retention-')),folder=path.join(root,'data/media');await fs.mkdir(folder,{recursive:true});
 const name=n=>'news-'+n.toString(16).padStart(20,'0')+'.webp';
 try {
  await fs.writeFile(path.join(folder,'unrelated.jpg'),'preserve');
  for(let n=1;n<=7;n++){
   await fs.writeFile(path.join(folder,name(n)),'image');
   const feed={ok:true,generated_at:String(n),items:[{id:n,media:{variants:[{url:'https://welcomeourofhere.github.io/Shaver-Family/data/media/'+name(n)}]}}]};
   const result=await retainFeedVersions(feed,{root});assert.equal(result.keptVersions,Math.min(n,6));
  }
  await assert.rejects(fs.access(path.join(folder,name(1))));
  for(let n=2;n<=7;n++)await fs.access(path.join(folder,name(n)));
  await fs.access(path.join(folder,'unrelated.jpg'));
  await assert.rejects(retainFeedVersions({ok:false,items:[]},{root}));
 }finally {await fs.rm(root,{recursive:true,force:true});}
});
