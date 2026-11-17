import {test}from'node:test';
import assert from'node:assert/strict';
import {inlineLinks}from'../src/content/inline-links.ts';
import {hasSitePreviousPage}from'../src/scripts/page-back.ts';
import site from'../content/site.json'with{type:'json'};

test('FAQ links preserve every character and use current phone/address targets',()=>{
 const text=`Телефон ${site.phone}; адрес ${site.address}.`;
 const parts=inlineLinks(text);assert.equal(parts.map(p=>p.text).join(''),text);
 assert.equal(parts.find(p=>p.text===site.phone).href,`tel:${site.phoneLink}`);
 assert.equal(parts.find(p=>p.text===site.address).href,`https://yandex.ru/maps/?text=${encodeURIComponent(`${site.city}, ${site.address}`)}`);
});
test('URL and email punctuation stays outside actionable links; script text is never HTML',()=>{
 const text='Почта hello@example.com. Ссылка https://example.com/help?a=1. javascript:alert(1) <img onerror=alert(1)>';
 const parts=inlineLinks(text);assert.equal(parts.map(p=>p.text).join(''),text);
 assert.deepEqual(parts.filter(p=>p.href).map(p=>p.href),['mailto:hello@example.com','https://example.com/help?a=1']);
});
test('Back requires a same-site referrer and an available previous history entry',()=>{
 assert.equal(hasSitePreviousPage('https://soyuz.hair/','https://soyuz.hair',2),true);
 for(const ref of['','https://example.com/','not a URL'])assert.equal(hasSitePreviousPage(ref,'https://soyuz.hair',2),false);
 assert.equal(hasSitePreviousPage('https://soyuz.hair/','https://soyuz.hair',1),false);
});
test('balanced parentheses stay in a URL while surrounding punctuation stays in the paragraph',()=>{
 for(const [text,href]of[
  ['(https://example.com/Foo_(bar)).','https://example.com/Foo_(bar)'],
  ['https://example.com/?q=foo(bar).','https://example.com/?q=foo(bar)'],
  ['[https://example.com/path].','https://example.com/path'],
 ]){
  const parts=inlineLinks(text);assert.equal(parts.map(p=>p.text).join(''),text);
  assert.deepEqual(parts.filter(p=>p.href).map(p=>p.href),[href]);
 }
});
