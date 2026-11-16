import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import site from '../content/site.json' with {type:'json'};
import seo from '../content/seo.json' with {type:'json'};
const html=()=>readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
test('local SEO metadata is unique and does not invent a production address or rating',()=>{
 const h=html();assert.equal((h.match(/<h1\b/g)||[]).length,1);assert.ok(h.includes(seo.title));assert.ok(h.includes(seo.description));
 const data=JSON.parse(h.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);
 assert.equal(data.address.streetAddress,site.address);assert.equal(data.telephone,site.phoneLink);assert.equal(data.aggregateRating,undefined);assert.equal(data.url,undefined);
 assert.match(h,/name="robots" content="noindex, nofollow"/);assert.doesNotMatch(h, /rel="canonical"/);
});
test('service media descriptions identify selected artwork or reviewed photography',()=>{
 const photos=JSON.parse(readFileSync(new URL('../content/service-photos.json',import.meta.url)));
 const catalog=JSON.parse(readFileSync(new URL('../content/service-catalog.json',import.meta.url)));
 assert.equal(Object.keys(photos.images).length,catalog.categories.flatMap(category=>category.services).length+catalog.archivedServices.length);for(const image of Object.values(photos.images)){assert.ok(image.alt.length>15);assert.ok(image.altSource.startsWith(image.artwork?'owner-selected service artwork':'visual review'));assert.doesNotMatch(image.alt,/Фотосессия СОЮЗа:/);}
});
