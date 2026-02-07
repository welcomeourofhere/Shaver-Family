// scripts/vk_fetch.mjs
// Node 20+ (GitHub Actions). Env: VK_TOKEN

import fs from "node:fs/promises";

const VK_API_VERSION = "5.131";
const GROUP_SCREEN_NAME = "shaver_family";

// СКОЛЬКО ПОКАЗЫВАЕМ
const OUT_LIMIT = 12;

// СКОЛЬКО БЕРЁМ СТЕНОЙ ЗА РАЗ (макс для wall.get = 100)
const PAGE_SIZE = 100;

// СКОЛЬКО СТРАНИЦ СТЕНЫ МАКСИМУМ ПРОСМАТРИВАЕМ, ЕСЛИ МАЛО ФОТО
const MAX_PAGES = 6;

// ОБРЕЗКА ТЕКСТА ДЛЯ ОВЕРЛЕЯ
const TEXT_LEN = 5000;

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
  "https://vk.com/wall-115375700_6990",
];

function getWallIdFromUrl(u) {
  const m = String(u || "").match(/wall-?\d+_\d+/i);
  return m ? m[0].toLowerCase() : "";
}
const BLACKLIST = new Set(BLACKLIST_INPUT.map(getWallIdFromUrl).filter(Boolean));

function normalizeNewlines(s) {
  return String(s || "").replace(/\r\n?/g, "\n");
}

/**
 * Важно: НЕ схлопываем пробелы и переносы строк.
 * Оставляем пустые строки.
 */
function cutTextKeepLines(s, maxLen) {
  s = normalizeNewlines(s);
  maxLen = Math.max(0, Math.floor(Number(maxLen || 0)));
  if (!maxLen) return s;
  if (s.length <= maxLen) return s;
  return s.slice(0, Math.max(0, maxLen - 1)).trimEnd() + "…";
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

/**
 * Важно:
 * - ссылку делаем на САМ пост в группе (raw.owner_id/raw.id)
 * - медиа берём из copy_history[0], если это репост, чтобы было фото
 * - дату берём raw.date (это дата поста в группе)
 * - текст берём так, чтобы сохранить переносы/пустые строки
 */
function normalizeWallItem(raw) {
  const rawOwner = Number(raw?.owner_id || 0);
  const rawId = Number(raw?.id || 0);
  const link = rawOwner && rawId ? `https://vk.com/wall${rawOwner}_${rawId}` : "";

  const src = (raw && Array.isArray(raw.copy_history) && raw.copy_history[0]) ? raw.copy_history[0] : raw;

  // Текст: если в посте группы пусто, берём из src, но переносы сохраняем
  const textRaw = (raw?.text && String(raw.text).length) ? String(raw.text) : String(src?.text || "");
  const text = normalizeNewlines(textRaw);

  const likes = raw?.likes && typeof raw.likes.count === "number" ? raw.likes.count : 0;
  const views = raw?.views && typeof raw.views.count === "number" ? raw.views.count : 0;
  const date = Number(raw?.date || 0);

  const attachments = Array.isArray(src?.attachments)
    ? src.attachments
    : (Array.isArray(raw?.attachments) ? raw.attachments : []);

  return {
    owner_id: rawOwner,
    id: rawId,
    link,
    text,
    likes,
    views,
    date,
    attachments,
    is_pinned: raw?.is_pinned ? 1 : 0
  };
}

function pickFirstPhotoMedia(attachments) {
  if (!Array.isArray(attachments)) return null;

  for (const att of attachments) {
    if (!att || !att.type) continue;
    if (att.type !== "photo") continue;

    const p = att.photo;
    if (!p || !Array.isArray(p.sizes)) continue;

    const thumb = pickImageByTargetWidth(p.sizes, 600);
    const full = pickImageByTargetWidth(p.sizes, 1280);
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

  return null;
}

async function vkCall(method, params) {
  const token = process.env.VK_TOKEN;
  if (!token) throw new Error("VK_TOKEN is not set");

  const url = new URL(`https://api.vk.com/method/${method}`);
  url.searchParams.set("access_token", token);
  url.searchParams.set("v", VK_API_VERSION);

  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null) continue;
    url.searchParams.set(k, String(v));
  }

  const ctrl = new AbortController();
  const tid = setTimeout(() => {
    try { ctrl.abort(); } catch (e) {}
  }, 15000);

  const r = await fetch(url.toString(), { method: "GET", signal: ctrl.signal });
  clearTimeout(tid);

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

async function fetchLatest12Photos() {
  const groupId = await getGroupId();
  const owner_id = -groupId;

  const out = [];
  const seen = new Set();

  let offset = 0;

  for (let page = 0; page < MAX_PAGES && out.length < OUT_LIMIT; page++) {
    const wall = await vkCall("wall.get", {
      owner_id,
      count: PAGE_SIZE,
      offset,
      filter: "owner",
    });

    const items = Array.isArray(wall?.items) ? wall.items : [];
    if (!items.length) break;

    for (const raw of items) {
      const it = normalizeWallItem(raw);

      // pinned пропускаем
      if (it.is_pinned) continue;

      const wallId = `wall${it.owner_id}_${it.id}`.toLowerCase();
      if (BLACKLIST.has(wallId)) continue;

      const k = `${it.owner_id}_${it.id}`;
      if (seen.has(k)) continue;
      seen.add(k);

      const media = pickFirstPhotoMedia(it.attachments);
      if (!media) continue;

      out.push({
        owner_id: it.owner_id,
        id: it.id,
        date: it.date,
        text: cutTextKeepLines(it.text, TEXT_LEN), // переносы/пустые строки сохраняем
        likes: it.likes,
        views: it.views,
        link: it.link,
        media,
      });

      if (out.length >= OUT_LIMIT) break;
    }

    offset += items.length;
  }

  return { owner_id: -groupId, items: out };
}

async function main() {
  const generatedAt = new Date().toISOString();

  try {
    const r = await fetchLatest12Photos();

    const payload = {
      ok: true,
      group: GROUP_SCREEN_NAME,
      generated_at: generatedAt,
      count: r.items.length,
      items: r.items,
    };

    await fs.mkdir("data", { recursive: true });
    await fs.writeFile("data/feed.json", JSON.stringify(payload, null, 2), "utf8");
    console.log(`OK: wrote data/feed.json (${payload.count} items)`);
  } catch (e) {
    const payload = {
      ok: false,
      group: GROUP_SCREEN_NAME,
      generated_at: generatedAt,
      count: 0,
      items: [],
      error: String(e && e.message ? e.message : e),
    };

    await fs.mkdir("data", { recursive: true });
    await fs.writeFile("data/feed.json", JSON.stringify(payload, null, 2), "utf8");
    console.log(`FAIL: wrote data/feed.json with error`);
    console.error(e);
    process.exitCode = 0;
  }
}

main();
