import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { visibleOfferRange } from "../src/scripts/offer-range.ts";
import design from '../src/config/design.json' with { type: 'json' };
import site from '../content/site.json' with { type: 'json' };

test('fixed offer surfaces use brand colors without repeating cyclic neighbors', () => {
  const {base} = design.offerThemes;
  assert.equal(base.length, 11);
  for (let i = 0; i < base.length; i++) {
    assert.ok(['red','blue','yellow','ink'].includes(base[i]));
    assert.notEqual(base[i], base[(i + 1) % base.length]);
  }
});

const catalog = JSON.parse(
  readFileSync(new URL("../content/offers.json", import.meta.url), "utf8"),
);
const expectedIds = [
  "coffee",
  "first-visit",
  "cashback",
  "loyalty",
  "waxing",
  "father-son",
  "birthday",
  "veterans",
  "premium",
  "referral",
];

test("all ten source offer IDs are present once, with full conditions and local contact actions", () => {
  assert.deepEqual(
    catalog.offers.filter(offer => offer.sourceId).map((offer) => offer.id),
    expectedIds,
  );
  assert.deepEqual(catalog.metadata.sourceIds, expectedIds);
  for (const offer of catalog.offers.filter(offer => offer.sourceId)) {
    assert.equal(offer.sourceId, offer.id);
    assert.equal(offer.status, "unverified-live-local-template");
    assert.ok(
      offer.title && offer.summary && offer.description && offer.action,
    );
    assert.ok(offer.description.length > offer.summary.length);
    assert.doesNotMatch(
      JSON.stringify(offer),
      /https?:|BOOKING_|shaver|taplink|vk\.com|D404/i,
    );
    assert.ok(["blue", "red", "ink"].includes(offer.color));
  }
});

test('the coffee offer keeps the review dialog while optional review fillers are disabled',()=>{
  assert.equal(catalog.offers.find(offer=>offer.id==='coffee').actionType,'review');
  assert.ok(catalog.offers.every(offer=>['booking','contact','review','choose-master','vk'].includes(offer.actionType)));
  const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
  const article=html.match(/<article\b[^>]*id="offer-coffee"[^>]*>([\s\S]*?)<\/article>/)?.[1];
  assert.ok(article,'the coffee offer is rendered');
  const button=article.match(/<button\b[^>]*class="btn of-action"[^>]*>/)?.[0];
  assert.ok(button,'the coffee offer has its own action');
  assert.match(button,/data-open-reviews/);
  assert.match(button,/aria-controls="review-dialog"/);
  assert.match(button,/aria-haspopup="dialog"/);
  assert.doesNotMatch(button,/data-contact|data-booking/);
  assert.equal((html.match(/\bdata-open-reviews\b/g)||[]).length,catalog.offers.filter(offer=>offer.actionType==='review').length);
  assert.doesNotMatch(html,/\bdata-review-extra\b/);
  assert.doesNotMatch(html,/class="reviews-intro"/);
});

test("SOYUZ first visit uses the owner-confirmed 30 percent and СССР", () => {
  const firstVisit = catalog.offers.find((offer) => offer.id === "first-visit");
  assert.equal(site.firstVisitPercent, 30);
  assert.equal(firstVisit.value, `−${site.firstVisitPercent}%`);
  for(const text of [firstVisit.title,firstVisit.summary,firstVisit.description]){
    assert.ok(text.includes(`${site.firstVisitPercent}%`));
    assert.doesNotMatch(text,/50%|полцены/);
  }
  assert.match(firstVisit.description, /СССР/);
  assert.match(firstVisit.description, /один раз/);
  assert.equal(catalog.metadata.localFirstVisit.percent, 30);
  assert.equal(catalog.metadata.localFirstVisit.promo, "СССР");
});

test("source monetary, eligibility and period conditions survive adaptation", () => {
  const offers = Object.fromEntries(
    catalog.offers.map((offer) => [offer.id, offer]),
  );
  assert.match(offers.cashback.description, /5%/);
  assert.match(offers.cashback.description, /до 50%/);
  assert.match(offers["father-son"].description, /300 ₽/);
  assert.match(offers.birthday.description, /за 7 дней до и 7 дней после/);
  assert.match(
    offers.veterans.description,
    /ветеранов боевых действий и участников/,
  );
  assert.match(offers.premium.description, /25%/);
  assert.match(offers.premium.description,/купи косметику/);
  assert.doesNotMatch(offers.premium.description,/пятиэтапный|чем.*по отдельности/);
  assert.equal(offers.coffee.note,null);assert.equal(offers.loyalty.note,null);
  assert.equal(offers.waxing.actionType,'vk');assert.match(offers.waxing.summary,/подпишись|Подпишись/);
  assert.match(offers.waxing.note,/один раз/);assert.match(offers['father-son'].note,/от 4 до 18 лет/);
  for(const id of ['first-visit','cashback','waxing','father-son','birthday','veterans','honest-price'])assert.match(offers[id].note,/не суммируются/);
  assert.match(offers.referral.summary,/50%/);assert.match(offers.referral.summary,/200 баллов/);assert.match(offers.referral.note,/впервые/);
  assert.match(offers.waxing.description, /носа или ушей/);
  assert.match(offers.waxing.description, /За подписку/);
  assert.match(
    offers.coffee.description,
    /количество оставленных отзывов не ограничено/,
  );
  assert.match(offers.referral.description, /Порекомендуй СОЮЗ другу/);
  assert.match(offers.referral.description, /200 баллов/);
  assert.equal(catalog.metadata.currentSoyuzConditionsVerified, false);
});

test("rail position follows three, two or one visible cards and clamps at each end", () => {
  assert.deepEqual(visibleOfferRange(0, 1200, 407, 10), { first: 1, last: 3 });
  assert.deepEqual(visibleOfferRange(407 * 7, 1200, 407, 10), {
    first: 8,
    last: 10,
  });
  assert.deepEqual(visibleOfferRange(410, 800, 410, 10), { first: 2, last: 3 });
  assert.deepEqual(visibleOfferRange(304 * 9, 288, 304, 10), {
    first: 10,
    last: 10,
  });
  assert.deepEqual(visibleOfferRange(-20, 288, 304, 10), { first: 1, last: 1 });
  assert.deepEqual(visibleOfferRange(99999, 1200, 407, 10), {
    first: 8,
    last: 10,
  });
  assert.deepEqual(visibleOfferRange(0, 0, 0, 0), { first: 0, last: 0 });
});
