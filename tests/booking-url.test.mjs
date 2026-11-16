import { test } from "node:test";
import assert from "node:assert/strict";
import { bookingURLs,certificateURLs } from "../src/scripts/booking-url.ts";
test("owner YCLIENTS link keeps its company and query while using the embedded host", () => {
  assert.deepEqual(bookingURLs("https://n2763199.yclients.ru"), {
    publicUrl: "https://n2763199.yclients.ru/",
    widgetUrl: "https://b2763199.yclients.ru/",
  });
  assert.equal(
    bookingURLs("https://n2763199.yclients.com/?staff=42").widgetUrl,
    "https://b2763199.yclients.ru/?staff=42",
  );
});

test('certificate purchase preserves the owner shop and rejects other forms or redirects',()=>{
 const url='https://o16013.yclients.ru/certificates';
 assert.deepEqual(certificateURLs(url),{publicUrl:url,widgetUrl:url});
 for(const value of [undefined,'http://o16013.yclients.ru/certificates','https://user:pass@o16013.yclients.ru/certificates','https://o16013.yclients.ru:8443/certificates','https://o16013.yclients.ru.example.org/certificates','https://o16013.yclients.ru/','https://o16013.yclients.ru/certificates?redirect=https://example.org','https://n2763199.yclients.ru/certificates'])assert.equal(certificateURLs(value),undefined);
});
test("booking provider rejects unsafe or unrelated navigation", () => {
  for (const value of [
    undefined,
    {},
    "javascript:alert(1)",
    "http://n2763199.yclients.ru",
    "https://x:n@n2763199.yclients.ru",
    "https://n2763199.yclients.ru:444",
    "https://n2763199.yclients.ru.attacker.example/",
  ])
    assert.equal(bookingURLs(value), undefined);
});
