// scripts/vk_fetch.mjs
// Node 20+ (GitHub Actions). Env: VK_TOKEN

import fs from "node:fs/promises";
import {prepareFeed} from './news_images.mjs';
import {collectPosts,enrichPosts} from './news_posts.mjs';
import {retainFeedVersions} from './news_retention.mjs';

const VK_API_VERSION = "5.131";
const GROUP_SCREEN_NAME = "shaver_family";

// СКОЛЬКО ПОКАЗЫВАЕМ
const OUT_LIMIT = 35;

// СКОЛЬКО БЕРЁМ СТЕНОЙ ЗА РАЗ (макс для wall.get = 100)
const PAGE_SIZE = 100;

// СКОЛЬКО СТРАНИЦ СТЕНЫ МАКСИМУМ ПРОСМАТРИВАЕМ, ЕСЛИ МАЛО МЕДИА
const MAX_PAGES = 6;

// ТВОЙ BLACKLIST (в одном месте — здесь)
const BLACKLIST_INPUT = [
  "https://vk.com/wall-115375700_7141",
  "https://vk.com/wall-221312879_10970",
  "https://vk.com/wall-115375700_7100",
  "https://vk.com/wall-115375700_7054",
  "https://vk.com/wall-115375700_7005",
  "https://vk.com/wall-221312879_9942",
  "https://vk.com/wall-115375700_6989",
  "https://vk.com/wall-115375700_7046",
  "https://vk.com/wall-115375700_7026",
  "https://vk.com/wall-115375700_6979",
  "https://vk.com/wall-24447840_22984",
  "https://vk.com/wall-212196960_162",
  "https://vk.com/wall-221312879_8954",
  "https://vk.com/wall-115375700_6934",
  "https://vk.com/wall-115375700_7061",
  "https://vk.com/wall-115375700_6873",
  "https://vk.com/wall-115375700_6875",
  "https://vk.com/wall-115375700_7781",
  "https://vk.com/wall-115375700_7284",
  "https://vk.com/wall-115375700_7795",
  "https://vk.com/wall-115375700_7271",
  "https://vk.com/wall-115375700_7282",  
  "https://vk.com/wall-115375700_6990",
];

function getWallIdFromUrl(u) {
  const m = String(u || "").match(/wall-?\d+_\d+/i);
  return m ? m[0].toLowerCase() : "";
}
const BLACKLIST = new Set(BLACKLIST_INPUT.map(getWallIdFromUrl).filter(Boolean));

async function vkCall(method, params) {
  const publicEmbed=method === 'video.getOembed';
  const token = process.env.VK_TOKEN;
  if (!token && !publicEmbed) throw new Error("VK_TOKEN is not set");

  const url = new URL(`https://api.vk.com/method/${method}`);
  if (!publicEmbed) url.searchParams.set("access_token", token);
  url.searchParams.set("v", VK_API_VERSION);

  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null) continue;
    url.searchParams.set(k, String(v));
  }

  const ctrl = new AbortController();
  const tid = setTimeout(() => {
    try { ctrl.abort(); } catch (e) {}
  }, 15000);

  let r;
  try {r = await fetch(url.toString(), { method: "GET", signal: ctrl.signal });}
  finally {clearTimeout(tid);}
  if (!r.ok) throw new Error("VK API request failed");

  const data = await r.json().catch(() => null);
  if (!data) throw new Error("VK API bad JSON");
  if (data.error) throw new Error(data.error.error_msg || "VK API error");
  return data.response;
}

async function getGroupId() {
  const resp = await vkCall("groups.getById", { group_id: GROUP_SCREEN_NAME });
  const id = resp && resp[0] && typeof resp[0].id === "number" ? resp[0].id : null;
  if (!id) throw new Error("Cannot resolve group id");
  return id;
}

async function main() {
  const generatedAt = new Date().toISOString();

  try {
    let previous=null;
    try {previous=JSON.parse(await fs.readFile('data/feed.json','utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
    const groupId = await getGroupId();
    const posts = await collectPosts(vkCall,{ownerId:-groupId,limit:OUT_LIMIT,pageSize:PAGE_SIZE,maxPages:MAX_PAGES,blacklist:BLACKLIST});
    const r = await enrichPosts(posts,vkCall,generatedAt);

    const payload = await prepareFeed({
      ok: true,
      group: GROUP_SCREEN_NAME,
      generated_at: generatedAt,
      count: r.items.length,
      statistics: {updated_at:generatedAt,likes_source:"wall.likes.count",views_source:"wall.views.count",reach_source:"stats.getPostReach",reach_status:r.reachStatus},
      items: r.items,
    });

    await fs.mkdir("data", { recursive: true });
    await fs.writeFile("data/feed.json.tmp", JSON.stringify(payload, null, 2), "utf8");
    await fs.rename("data/feed.json.tmp", "data/feed.json");
    await retainFeedVersions(payload,{previous});
    console.log(`OK: wrote data/feed.json (${payload.count} items)`);
  } catch (e) {
    // An API/image failure must never replace working news with an empty feed.
    const diagnostic=String(e?.message||'unknown error').replaceAll(process.env.VK_TOKEN||'__absent_token__','[redacted]').replace(/access_token=[^&\s]+/gi,'access_token=[redacted]').slice(0,300);
    console.error('Feed update failed; the previous feed was retained. Reason: '+diagnostic);
    process.exitCode = 1;
  }
}

main();
