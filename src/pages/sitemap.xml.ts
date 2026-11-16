import type {APIRoute} from 'astro';
import production from '../../deploy/production.json' with {type:'json'};
export const GET:APIRoute=({site})=>new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${site?production.pages.filter(path=>path!='/404').map(path=>`<url><loc>${new URL(path,site).href}</loc></url>`).join(''):''}</urlset>`,{headers:{'Content-Type':'application/xml; charset=utf-8'}});
