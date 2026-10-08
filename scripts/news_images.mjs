import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import sharp from 'sharp';

const widths=[160,320,640,960,1280];
const base='https://welcomeourofhere.github.io/Shaver-Family/';
const digest=raw=>createHash('sha256').update(raw).digest('hex');

export async function prepareMedia(media,{root='.',download=downloadImage}={}) {
  if(!['photo','video'].includes(media?.type))return media;
  if(!media.full_url&&!media.thumb_url)return media;
  const source=media.full_url||media.thumb_url;
  const sourceUrl=new URL(source);
  if(sourceUrl.protocol!=='https:'||!/(^|\.)(userapi\.com|vk\.com|vkuserphoto\.ru|vk-cdn\.net)$/.test(sourceUrl.hostname))throw new Error('Unexpected photo origin');
  // A source URL can contain an expiring signature. Its hash is only a cache
  // lookup; derivative filenames are bound to the actual encoded image bytes.
  const cacheFile=path.join(root,'data/media',digest(source)+'.json');
  try {
    const saved=JSON.parse(await fs.readFile(cacheFile,'utf8'));
    if(saved.profile==='webp-v1'&&saved.source===source&&saved.variants.length&&
       (await Promise.all(saved.variants.map(v=>fs.access(path.join(root,v.path)).then(()=>true,()=>false)))).every(Boolean))
      return result(media,saved.variants);
  } catch(error) {if(error.code!=='ENOENT'&&!(error instanceof SyntaxError))throw error;}
  const raw=await download(source);
  const image=sharp(raw,{limitInputPixels:50_000_000}).rotate();
  const oriented=await image.toBuffer({resolveWithObject:true});
  const actualWidth=oriented.info.width;
  const targets=[...new Set(widths.map(w=>Math.min(w,actualWidth)))];
  const variants=[];await fs.mkdir(path.join(root,'data/media'),{recursive:true});
  for(const width of targets) {
    const {data,info}=await sharp(oriented.data).resize({width,withoutEnlargement:true}).webp({quality:82,effort:5}).toBuffer({resolveWithObject:true});
    const file='data/media/news-'+digest(data).slice(0,20)+'.webp';
    await fs.writeFile(path.join(root,file),data);
    variants.push({url:new URL(file,base).href,path:file,width:info.width,height:info.height,bytes:data.length});
  }
  await fs.writeFile(cacheFile,JSON.stringify({profile:'webp-v1',source,variants},null,2)+'\n');
  return result(media,variants);
}

function result(media,variants) {
  const small=variants.find(v=>v.width>=640)||variants.at(-1),large=variants.at(-1);
  return {...media,thumb_url:small.url,full_url:large.url,width:large.width,height:large.height,
    original_thumb_url:media.original_thumb_url||media.thumb_url,original_full_url:media.original_full_url||media.full_url,
    variants:variants.map(({path,...v})=>v)};
}

async function downloadImage(url) {
  const response=await fetch(url,{signal:AbortSignal.timeout(20_000)});
  if(!response.ok)throw new Error(`Photo request failed (${response.status})`);
  if(!response.headers.get('content-type')?.startsWith('image/'))throw new Error('Photo response is not an image');
  const reader=response.body.getReader();const parts=[];let size=0;
  try {
    for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>20_000_000)throw new Error('Photo exceeds 20MB');parts.push(value);}
  } finally {await reader.cancel();}
  return Buffer.concat(parts);
}

export async function prepareFeed(feed,options={}) {
  if(!feed.ok||!Array.isArray(feed.items)||!feed.items.length)throw new Error('Feed has no usable news');
  const items=[];
  // Bounded serial downloads avoid hitting VK rate limits in the daily job.
  for(const item of feed.items) {
    const many=Array.isArray(item.media),media=many?item.media:[item.media];
    const prepared=[];
    for(const photo of media) {
      const original=photo?.original_full_url?{...photo,full_url:photo.original_full_url,thumb_url:photo.original_thumb_url||photo.thumb_url}:photo;
      try {prepared.push(await prepareMedia(original,options));}
      catch(error) {
        // A new video cover/CDN outage must not remove an otherwise valid post
        // or erase the whole working feed. Preserve its actual API image.
        const origin=(()=>{try{return new URL(original?.full_url||original?.thumb_url).hostname;}catch{return 'no-image';}})();
        console.warn(`Media optimisation unavailable: post ${item.owner_id}_${item.id}, ${original?.type}, origin ${origin}. Original API image retained.`);
        prepared.push({...original,optimization_status:'original-source'});
      }
    }
    items.push({...item,media:many?prepared:prepared[0]});
  }
  return {...feed,media_profile:'webp-v1',items};
}
