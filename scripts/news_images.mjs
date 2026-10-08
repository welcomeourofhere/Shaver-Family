import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import sharp from 'sharp';

const widths=[160,320,640,960,1280];
const base='https://welcomeourofhere.github.io/Shaver-Family/';
const digest=raw=>createHash('sha256').update(raw).digest('hex');
function approved(url) {
  const u=new URL(url);
  return u.protocol==='https:'&&!u.username&&!u.password&&
    (/(^|\.)(userapi\.com|vk\.com|vkuserphoto\.ru|vk-cdn\.net)$/.test(u.hostname)||u.hostname==='iv.okcdn.ru');
}

// Remove letterboxing only when the complete outer bands are near-black.
// Actual video dimensions define the content ratio; dark photographic edges
// with texture/colour are retained, as are photo posts.
async function stripBars(oriented,ratio) {
  const {width:w,height:h}=oriented.info;
  if(!Number.isFinite(ratio)||ratio<.1||ratio>10)return {...oriented,cropped:false};
  const wide=w/h>ratio*1.04,high=w/h<ratio/1.04;
  if(!wide&&!high)return {...oriented,cropped:false};
  const cw=wide?Math.min(w,Math.round(h*ratio)):w,ch=high?Math.min(h,Math.round(w/ratio)):h;
  const left=Math.floor((w-cw)/2),top=Math.floor((h-ch)/2);
  const bands=wide?[{left:0,top:0,width:left-2,height:h},{left:left+cw+2,top:0,width:w-left-cw-2,height:h}]:
    [{left:0,top:0,width:w,height:top-2},{left:0,top:top+ch+2,width:w,height:h-top-ch-2}];
  if(bands.some(b=>b.width<2||b.height<2))return {...oriented,cropped:false};
  for(const band of bands){
    const edge=await sharp(oriented.data).extract(band).removeAlpha().toBuffer();
    const stats=await sharp(edge).stats();
    if(stats.channels.some(c=>c.mean>8||c.stdev>6||c.max>32))return {...oriented,cropped:false};
  }
  const trimmed=await sharp(oriented.data).extract({left,top,width:cw,height:ch}).toBuffer({resolveWithObject:true});
  return {...trimmed,cropped:true};
}

export async function prepareMedia(media,{root='.',download=downloadImage}={}) {
  if(!['photo','video'].includes(media?.type))return media;
  if(!media.full_url&&!media.thumb_url)return media;
  const source=media.full_url||media.thumb_url;
  if(!approved(source))throw new Error('Unexpected photo origin');
  const video=media.type==='video',ratio=Number(media.video_width)/Number(media.video_height);
  const candidates=video?[...new Set([source,...(media._poster_candidates||[]).slice()
    .sort((a,b)=>Number(b.width)*Number(b.height)-Number(a.width)*Number(a.height))
    .map(v=>v.url).filter(Boolean)])].filter(url=>{try{return approved(url);}catch{return false;}}).slice(0,6):[source];
  const profile=video?'webp-video-v2':'webp-v1';
  const cacheKey=video?JSON.stringify([profile,candidates,Number.isFinite(ratio)?ratio:null]):source;
  const cacheFile=path.join(root,'data/media',digest(cacheKey)+'.json');
  try {
    const saved=JSON.parse(await fs.readFile(cacheFile,'utf8'));
    if(saved.profile===profile&&saved.source===source&&saved.variants.length&&
       (await Promise.all(saved.variants.map(v=>fs.access(path.join(root,v.path)).then(()=>true,()=>false)))).every(Boolean))
      return result(media,saved.variants,saved.selected_source,saved.cropped);
  } catch(error) {if(error.code!=='ENOENT'&&!(error instanceof SyntaxError))throw error;}
  let best=null;
  for(const url of candidates) {
    try {
      const raw=await download(url);
      const oriented=await sharp(raw,{limitInputPixels:50_000_000}).rotate().toBuffer({resolveWithObject:true});
      const actual=video?await stripBars(oriented,ratio):{...oriented,cropped:false};
      const score=actual.info.width*actual.info.height;
      if(!best||score>best.score)best={...actual,url,score};
    } catch(error) {if(!video)throw error;}
  }
  if(!best)throw new Error('No usable video poster');
  const targets=[...new Set(widths.map(w=>Math.min(w,best.info.width)))];
  const variants=[];await fs.mkdir(path.join(root,'data/media'),{recursive:true});
  for(const width of targets) {
    const {data,info}=await sharp(best.data).resize({width,withoutEnlargement:true}).webp({quality:82,effort:5}).toBuffer({resolveWithObject:true});
    const file='data/media/news-'+digest(data).slice(0,20)+'.webp';
    await fs.writeFile(path.join(root,file),data);
    variants.push({url:new URL(file,base).href,path:file,width:info.width,height:info.height,bytes:data.length});
  }
  await fs.writeFile(cacheFile,JSON.stringify({profile,source,selected_source:best.url,cropped:best.cropped,variants},null,2)+'\n');
  return result(media,variants,best.url,best.cropped);
}

function result(media,variants,selectedSource,cropped) {
  const small=variants.find(v=>v.width>=640)||variants.at(-1),large=variants.at(-1);
  const {_poster_candidates,...publicMedia}=media;
  return {...publicMedia,thumb_url:small.url,full_url:large.url,width:large.width,height:large.height,
    original_thumb_url:media.original_thumb_url||media.thumb_url,original_full_url:selectedSource||media.original_full_url||media.full_url,
    ...(media.type==='video'?{poster_black_bars_removed:!!cropped}:{}),
    variants:variants.map(({path,...v})=>v)};
}

async function downloadImage(url) {
  const response=await fetch(url,{signal:AbortSignal.timeout(20_000)});
  if(!response.ok)throw new Error('Photo request failed');
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
  for(const item of feed.items) {
    const many=Array.isArray(item.media),media=many?item.media:[item.media],prepared=[];
    for(const photo of media) {
      const original=photo?.original_full_url?{...photo,full_url:photo.original_full_url,thumb_url:photo.original_thumb_url||photo.thumb_url}:photo;
      try {prepared.push(await prepareMedia(original,options));}
      catch(error) {
        const origin=(()=>{try{return new URL(original?.full_url||original?.thumb_url).hostname;}catch{return 'no-image';}})();
        console.warn('Media optimisation unavailable: post '+item.owner_id+'_'+item.id+', '+original?.type+', origin '+origin+'. Original API image retained.');
        const {_poster_candidates,...publicMedia}=original||{};
        prepared.push(original?{...publicMedia,optimization_status:'original-source'}:original);
      }
    }
    items.push({...item,media:many?prepared:prepared[0]});
  }
  return {...feed,media_profile:'webp-v1',items};
}
