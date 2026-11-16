import{test}from'node:test';
import assert from'node:assert/strict';
import{publicAnalyticsHost,contactChannel,makeAnalyticsConsent,readAnalyticsConsent,analyticsNoticeVersion}from'../src/scripts/analytics.ts';
test('only the two public SOYUZ hosts produce custom analytics events',()=>{
 for(const host of['soyuz.hair','www.soyuz.hair'])assert.equal(publicAnalyticsHost(host),true);
 for(const host of['localhost','127.0.0.1','stay-tan-habanero.tilda.ws','shaverfamily.ru','soyuz.hair.example.com'])assert.equal(publicAnalyticsHost(host),false);
});
test('contact analytics returns a channel without exporting private path or query data',()=>{
 for(const [url,channel]of[['tel:+79229090043','phone'],['https://vk.me/soyuz_kirov','vk'],['https://t.me/example?private=fixture','telegram'],['https://max.ru/u/fixture','max']])assert.equal(contactChannel(url),channel);
 for(const url of['invalid','https://example.com','https://vk.ru.example.com','https://o16013.yclients.ru/certificates'])assert.equal(contactChannel(url),undefined);
});
test('analytics grants are versioned, per service and expire after 180 days',()=>{
 const now=Date.UTC(2026,10,16),choice=makeAnalyticsConsent(true,false,now);
 assert.equal(choice.notice,analyticsNoticeVersion);assert.equal(choice.expiresAt-now,180*86400000);
 assert.deepEqual(readAnalyticsConsent(JSON.stringify(choice),now),choice);
 assert.equal(readAnalyticsConsent(JSON.stringify(choice),choice.expiresAt),null);
 assert.equal(readAnalyticsConsent(JSON.stringify(choice),now-1),null);
 assert.deepEqual(makeAnalyticsConsent(false,true,now),{...choice,metrika:false,ga4:true});
 for(const raw of[null,'granted','denied','{}','[]','null','broken',JSON.stringify({...choice,notice:'old'}),JSON.stringify({...choice,ga4:'true'}),JSON.stringify({...choice,expiresAt:now+365*86400000})])assert.equal(readAnalyticsConsent(raw,now),null,raw);
});
