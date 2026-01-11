// scripts/vk_fetch.mjs
// Node 20+
// Генерирует /data/feed.json для GitHub Pages

const VK_API_VERSION = "5.131";
const GROUP_SCREEN_NAME = "shaver_family";

// Сколько фото хотим на клиенте
const MAX_POOL = 12;

// Сколько постов сканируем вглубь (чтобы отфильтровать видео/закреп/старье/blacklist)
const SCAN = 90;

// Сколько фото отдаём в feed.json (с запасом под рандом)
const LIMIT_OUT = 36;

// Возраст (дней). Старше — не берем
const MAX_AGE_DAYS = 365;

// Обрезка текста
const TEXTLEN = 220;

// Черный список хранится ТОЛЬКО здесь
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
  "https://vk.com/wall-115375700_6990"
];

function getWallIdFromUrl(u){
  const m = String(u || "").match(/wall-?\d+_\d+/i);
  return m ? m[0] : "";
}
const BLACKLIST = new Set(BLACKLIST_INPUT.map(getWallIdFromUrl).filter(Boolean));

function cleanText(s){
  return String(s || "").replace(/\s+/g, " ").trim();
}
function cutText(s, maxLen){
  s = cleanText(s);
  const n = Math.max(0, Math.floor(Number(maxLen || 0)));
  if (!n) return s;
  if (s.length <= n) return s;
  return s.slice(0, Math.max(0, n - 1)).trimEnd() + "…";
}

function pickImageByTargetWidth(sizes, targetW) {
  if (!Array.isArray(sizes) || sizes.length === 0) return null;

  let best = null;
  let bestDelta = Infinity;
  let fallbackLargest = null;
  let fallbackArea = -1;

  for (const s of sizes) {
    if (!s || !s.url) continue;
    const w = Number(s.width || 0);
    const h = Number(s.height || 0);
    const area = w * h;

    if (area > fallbackArea) {
      fallbackArea = area;
      fallbackLargest = { url: s.url, width: w, height: h };
    }

    if (w > 0) {
      const delta = Math.abs(w - targetW);
      if (delta < bestDelta) {
        bestDelta = delta;
        best = { url: s.url, width: w, height: h };
      }
    }
  }

  return best || fallbackLargest;
}

function normalizeItem(raw) {
  const src = (raw && Array.isArray(raw.copy_history) && raw.copy_history[0]) ? raw.copy_history[0] : raw;

  const owner_id = Number(src.owner_id || raw.owner_id || 0);
  const id = Number(src.id || raw.id || 0);
  const link = owner_id && id ? `https://vk.com/wall${owner_id}_${id}` : null;

  const likes = src.likes && typeof src.likes.count === "number" ? src.likes.count : 0;
  const views = src.views && typeof src.views.count === "number" ? src.views.count : 0;

  const attachments = Array.isArray(src.attachments) ? src.attachments : [];

  return {
    owner_id,
    id,
    date: Number(src.date || 0),
    text: String(src.text || ""),
    likes,
    views,
    link,
    attachments,
    is_pinned: raw && raw.is_pinned ? 1 : 0,
  };
}

function pickPrimaryMedia(item) {
  for (const att of item.attachments) {
    if (!att || !att.type) continue;

    if (att.type === "photo" && att.photo && Array.isArray(att.photo.sizes)) {
      const thumb = pickImageByTargetWidth(att.photo.sizes, 600);
      const full  = pickImageByTargetWidth(att.photo.sizes, 1280);
      if (!thumb) continue;

      const w = Number((full && full.width) ? full.width : thumb.width) || 0;
      const h = Number((full && full.height) ? full.height : thumb.height) || 0;

      return {
        type: "photo",
        thumb_url: thumb.url,
        full_url: (full && full.url) ? full.url : thumb.url,
        width: w,
        height: h,
      };
    }

    // видео не берем в ленту
    if (att.type === "video") return { type: "video" };
  }
  return null;
}

async function vkCall(method, params, token) {
  const url = new URL(`https://api.vk.com/method/${method}`);
  url.searchParams.set("access_token", token);
  url.searchParams.set("v", VK_API_VERSION);
  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null) continue;
    url.searchParams.set(k, String(v));
  }

  const r = await fetch(url.toString(), { method: "GET" });
  const data = await r.json();

  if (data && data.error) throw new Error(data.error.error_msg || "VK API error");
  return data.response;
}

async function main(){
  const token = process.env.VK_TOKEN || "";
  if (!token) throw new Error("VK_TOKEN env is missing");

  const group = await vkCall("groups.getById", { group_id: GROUP_SCREEN_NAME }, token);
  const gid = group && group[0] && typeof group[0].id === "number" ? group[0].id : null;
  if (!gid) throw new Error("Cannot resolve group id");
  const owner_id = -gid;

  const wall = await vkCall("wall.get", { owner_id, count: SCAN, offset: 0, filter: "owner" }, token);
  const items = Array.isArray(wall.items) ? wall.items : [];

  const nowSec = Math.floor(Date.now() / 1000);
  const minDate = nowSec - MAX_AGE_DAYS * 86400;

  const out = [];
  const seen = new Set();

  for (let i = 0; i < items.length; i++){
    const it = normalizeItem(items[i]);

    if (it.is_pinned) continue;
    if (it.date && it.date < minDate) continue;

    const media = pickPrimaryMedia(it);
    if (!media || media.type !== "photo") continue;

    const wallId = getWallIdFromUrl(it.link);
    if (wallId && BLACKLIST.has(wallId)) continue;

    const k = `${it.owner_id}_${it.id}`;
    if (seen.has(k)) continue;
    seen.add(k);

    out.push({
      owner_id: it.owner_id,
      id: it.id,
      date: it.date,
      text: cutText(it.text, TEXTLEN),
      likes: it.likes,
      views: it.views,
      link: it.link,
      media,
    });

    if (out.length >= LIMIT_OUT) break;
  }

  const payload = {
    ok: true,
    group: GROUP_SCREEN_NAME,
    generated_at: new Date().toISOString(),
    items: out,
    meta: {
      max_pool: MAX_POOL,
      scan: SCAN,
      limit_out: LIMIT_OUT,
      max_age_days: MAX_AGE_DAYS,
      textlen: TEXTLEN
    }
  };

  const fs = await import("node:fs/promises");
  await fs.mkdir("data", { recursive: true });
  await fs.writeFile("data/feed.json", JSON.stringify(payload), "utf8");

  console.log(`Saved ${out.length} items to data/feed.json`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
