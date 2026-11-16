import policy from '../../content/news-policy.json' with { type: 'json' };

export interface NewsItem {
  id: string;
  publishedAt: string;
  text: string;
  url: string;
  image: { variants: { url: string; width: number; height: number }[] } | null;
}
export interface NewsFeed { version: number; groupId: number; generatedAt: string; items: NewsItem[] }

export function validNewsFeed(value: unknown): value is NewsFeed {
  if (!value || typeof value !== "object") return false;
  const feed = value as NewsFeed;
  if (feed.version !== 1 || feed.groupId !== -210007626 || typeof feed.generatedAt!=='string' || !Number.isFinite(Date.parse(feed.generatedAt)) || !Array.isArray(feed.items) || feed.items.length !== 10) return false;
  const ids = new Set<string>();
  return feed.items.every(item => {
    if (!item || typeof item.id !== "string" || !/^\d+$/.test(item.id) || ids.has(item.id) || policy.excludedPostIds.includes(item.id) || typeof item.text !== "string" || !item.text.trim() || item.text.length > 12000 || typeof item.publishedAt!=='string' || !Number.isFinite(Date.parse(item.publishedAt)) || item.url !== `https://vk.ru/wall-210007626_${item.id}`) return false;
    ids.add(item.id);
    return item.image === null || (Array.isArray(item.image?.variants) && item.image.variants.length > 0 && item.image.variants.length <= 3 && item.image.variants.every((v,i,variants) =>
      v && typeof v.url==='string' && /^\.\.\/media\/news\/[\da-f-]+\.webp$/.test(v.url) && Number.isInteger(v.width) && v.width > (i?variants[i-1].width:0) && v.width <= 1600 && Number.isInteger(v.height) && v.height > 0 && v.height <= 20000));
  });
}

export function newsImageURL(path: string, feedURL: string): string {
  return new URL(path, feedURL).href;
}

export function newsTitle(item: NewsItem): string {
  return item.text.split("\n").find(line => line.trim())?.trim() || "СОЮЗ";
}
// Native picture selection keeps desktop news off the compact video-only screen.
export const compactNewsPlaceholder='/brand/transparent.svg';
