import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

export function retainedKeys(feed) {
  const keys=new Set();
  for(const item of feed?.items || []) for(const media of Array.isArray(item.media)?item.media:[item.media]) {
    for(const variant of media?.variants || []) {
      const url=new URL(variant.url);
      if(url.origin==='https://welcomeourofhere.github.io'&&url.pathname.startsWith('/Shaver-Family/data/media/'))keys.add(path.posix.basename(url.pathname));
    }
    const source=media?.original_full_url;
    if(source)keys.add(createHash('sha256').update(source).digest('hex')+'.json');
  }
  return [...keys].sort();
}

export async function retainFeedVersions(feed,{root='.',previous=null,keep=6}={}) {
  if(!feed.ok||!feed.items?.length)throw new Error('Cannot retain an incomplete feed');
  const folder=path.resolve(root,'data/media'),ledger=path.join(folder,'feed-versions.json');
  await fs.mkdir(folder,{recursive:true});
  let versions=[];
  try {versions=JSON.parse(await fs.readFile(ledger,'utf8')).versions;}catch(e){if(e.code!=='ENOENT')throw e;}
  const add=value=>{
    if(!value?.items?.length)return;
    const id=createHash('sha256').update(JSON.stringify(value)).digest('hex').slice(0,20);
    if(!versions.some(v=>v.id===id))versions.push({id,generated_at:value.generated_at,keys:retainedKeys(value)});
  };
  add(previous);add(feed);
  versions=versions.slice(-keep);
  const protectedKeys=new Set(versions.flatMap(v=>v.keys));
  // Only files created by this image pipeline are managed. The previous five
  // complete snapshots keep their media available to already open clients.
  const removed=[];
  for(const name of await fs.readdir(folder)) {
    if(!/^(?:news-[a-f0-9]{20}\.webp|[a-f0-9]{64}\.json)$/.test(name)||protectedKeys.has(name))continue;
    const target=path.resolve(folder,name);
    if(path.dirname(target)!==folder)throw new Error('Invalid media path');
    await fs.unlink(target);removed.push(name);
  }
  await fs.writeFile(ledger+'.tmp',JSON.stringify({schemaVersion:1,keep,versions},null,2)+'\n');
  await fs.rename(ledger+'.tmp',ledger);
  return {keptVersions:versions.length,removed:removed.length};
}
