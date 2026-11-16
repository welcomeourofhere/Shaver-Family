import{test}from'node:test';import assert from'node:assert/strict';import{readFileSync,readdirSync}from'node:fs';
const content=name=>JSON.parse(readFileSync(new URL('../content/'+name+'.json',import.meta.url),'utf8'));
test('authored marketing prose follows the SF language filter without rewriting supplied quotations',()=>{
 const fields=[...content('about').cards.flatMap(c=>c.paragraphs),...content('faq').items.flatMap(c=>c.answer),...content('offers').offers.flatMap(c=>[c.summary,c.description,c.note].filter(Boolean)),...content('service-catalog').categories.flatMap(c=>c.services.map(s=>s.description))];
 for(const text of fields){assert.doesNotMatch(text,/[;:]| — |это не просто|это не только|это больше,? чем/i,text);assert.ok(text.trim().length>15);}
 assert.ok(content('about').cards.every(c=>c.paragraphs.every(p=>p.length<400)));
});
test('brand declension preserves the uppercase root and lowercase case ending',()=>{
 for(const file of readdirSync(new URL('../content/',import.meta.url)).filter(f=>f.endsWith('.json'))){const text=readFileSync(new URL('../content/'+file,import.meta.url),'utf8');assert.doesNotMatch(text,/СОЮЗ(?:А|Е|ОМ|У)(?![А-Яа-яЁё])/u,file);}
});
