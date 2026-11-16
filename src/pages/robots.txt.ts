import type {APIRoute} from 'astro';
export const GET:APIRoute=({site})=>new Response(site?`User-agent: *\nAllow: /\nDisallow: /previews/\nDisallow: /404\n\nSitemap: ${new URL('/sitemap.xml',site).href}\n`:'User-agent: *\nDisallow: /\n',{headers:{'Content-Type':'text/plain; charset=utf-8'}});
