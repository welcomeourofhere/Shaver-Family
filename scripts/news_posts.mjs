// Pure wall normalization: counters and links always belong to the group post,
// while repost attachments may belong to the original author.
export function count(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(typeof value === 'object' ? value.count : value);
  return Number.isSafeInteger(n) && n >= 0 ? n : null;
}

export function pickImage(sizes, target) {
  const usable = (Array.isArray(sizes) ? sizes : []).filter(s => s?.url && Number(s.width) > 0);
  const above = usable.filter(s => Number(s.width) >= target).sort((a,b) => a.width-b.width);
  return above[0] || usable.sort((a,b) => b.width-a.width)[0] || null;
}

export function playerUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && ['vk.com','vk.ru','vkvideo.ru'].includes(url.hostname) &&
      url.pathname === '/video_ext.php' && !url.username && !url.password ? url.href : '';
  } catch { return ''; }
}

export function normalizePost(raw) {
  const source = raw.copy_history?.[0] || raw;
  const attachments = raw.attachments?.length ? raw.attachments : source.attachments || [];
  return {
    owner_id: Number(raw.owner_id), id: Number(raw.id), date: Number(raw.date),
    text: String(raw.text || source.text || '').replace(/\r\n?/g,'\n'),
    likes: count(raw.likes), views: count(raw.views), is_pinned: raw.is_pinned ? 1 : 0,
    link: `https://vk.com/wall${Number(raw.owner_id)}_${Number(raw.id)}`, attachments
  };
}

export function pickMedia(attachments) {
  // Keep video posts in the same news cards, including posts with a cover photo.
  for (const att of attachments) {
    const video = att.type === 'video' && att.video;
    if (!video || video.can_view === 0 || !Number.isSafeInteger(video.owner_id) || !Number.isSafeInteger(video.id)) continue;
    const images = video.image || video.first_frame || [];
    const thumb = pickImage(images,640), full = pickImage(images,1280);
    return {
      type: 'video', owner_id: video.owner_id, id: video.id,
      video_url: `https://vk.com/video${video.owner_id}_${video.id}`,
      player_url: playerUrl(video.player), title: String(video.title || ''),
      duration: count(video.duration), thumb_url: thumb?.url || '', full_url: full?.url || thumb?.url || '',
      width: Number(full?.width || thumb?.width || 0), height: Number(full?.height || thumb?.height || 0),
      // Used only for the authenticated API call, removed before serialization.
      _access_key: video.access_key || ''
    };
  }
  for (const att of attachments) {
    if (att.type !== 'photo') continue;
    const thumb = pickImage(att.photo?.sizes,640), full = pickImage(att.photo?.sizes,1280);
    if (thumb) return {type:'photo',thumb_url:thumb.url,full_url:full?.url || thumb.url,
      width:Number(full?.width || thumb.width),height:Number(full?.height || thumb.height)};
  }
  return null;
}

export async function collectPosts(call,{ownerId,limit=12,pageSize=100,maxPages=6,blacklist=new Set()}={}) {
  const result = [], seen = new Set(); let offset = 0;
  for (let page=0;page<maxPages && result.length<limit;page++) {
    const wall = await call('wall.get',{owner_id:ownerId,count:pageSize,offset,filter:'owner'});
    const rawItems = Array.isArray(wall?.items) ? wall.items : [];
    if (!rawItems.length) break;
    for (const raw of rawItems) {
      const item = normalizePost(raw), key = `${item.owner_id}_${item.id}`;
      if (!item.owner_id || !item.id || seen.has(key) || blacklist.has(`wall${key}`)) continue;
      seen.add(key);
      const media = pickMedia(item.attachments);
      // A pinned text-only announcement is still a valid news item.
      if (!media && !item.is_pinned) continue;
      delete item.attachments;
      result.push({...item,text:item.text.length>5000?item.text.slice(0,4999).trimEnd()+'…':item.text,media});
      if (result.length>=limit) break;
    }
    offset += rawItems.length;
  }
  result.sort((a,b)=>b.is_pinned-a.is_pinned || b.date-a.date);
  return result;
}

export async function enrichPosts(items,call,updatedAt) {
  const out=items.map(item=>({...item,stats_updated_at:updatedAt,reach:null,
    media:item.media ? {...item.media} : null}));
  for (const item of out) {
    const media=item.media;
    if (media?.type !== 'video') continue;
    if (!media.player_url) {
      try {
        const response=await call('video.get',{videos:`${media.owner_id}_${media.id}${media._access_key?'_'+media._access_key:''}`});
        const video=response?.items?.[0];
        if (video && video.can_view !== 0) {
          media.player_url=playerUrl(video.player);
          const poster=pickImage(video.image || video.first_frame,1280);
          if (!media.full_url && poster) Object.assign(media,{thumb_url:poster.url,full_url:poster.url,width:Number(poster.width),height:Number(poster.height)});
        }
      } catch { /* The original public VK link remains usable if embedding is unavailable. */ }
    }
    delete media._access_key;
  }
  let reachStatus='unavailable';
  try {
    // Only the requested aggregate is exported; no demographic/conversion stats.
    const reach=await call('stats.getPostReach',{owner_id:out[0]?.owner_id,post_ids:out.map(x=>x.id).join(','),v:'5.199'});
    if (Array.isArray(reach)) for (const row of reach) {
      const item=out.find(x=>x.id===Number(row.post_id));
      if (item) item.reach=count(row.reach_total ?? row.reach_total_count);
    }
    if (out.some(x=>x.reach!==null)) reachStatus='available';
  } catch { /* Existing token permissions are preserved; missing reach is never zero. */ }
  return {items:out,reachStatus};
}
