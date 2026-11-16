import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aboutStickyTop } from '../src/scripts/about.ts';
import { bookingURLs } from '../src/scripts/booking-url.ts';

const read = (path) => readFileSync(new URL('../' + path, import.meta.url), 'utf8');

test('the four story cards reserve equal sticky steps and keep the last bottom readable', () => {
  for (const height of [400, 680, 1000, 1500])
    for (const viewport of [600, 900, 1200]) {
      const step = 12, safeTop = 96, safeBottom = 104;
      const base = aboutStickyTop(height, viewport, safeTop, safeBottom, step * 3);
      const tops = Array.from({ length: 4 }, (_, i) => base + i * step);
      assert.equal(tops[0], Math.min(Math.max(safeTop, (viewport - height) / 2), viewport - height - safeBottom - step * 3));
      assert.ok(tops[3] + height <= viewport - safeBottom);
      assert.deepEqual(tops.slice(1).map((top, i) => top - tops[i]), [step, step, step]);
    }
});

test('all six owner booking destinations preserve their identity in the drawer', () => {
  const people = JSON.parse(read('content/team.json')).masters;
  const expected = {
    'souz-svetlana': '2440449', 'souz-sonya-kid': '2266404',
    'souz-milena': '1761477', 'souz-darya': '1597224',
    'souz-sofya-shalaginova': '1208807', 'souz-lyubov': '1079132',
  };
  assert.equal(people.length, 6);
  for (const person of people) {
    const id = expected[person.id];
    assert.ok(id, person.id);
    assert.deepEqual(bookingURLs(person.bookingUrl), {
      publicUrl: `https://n${id}.yclients.ru/`, widgetUrl: `https://b${id}.yclients.ru/`,
    });
  }
});

test('short story copy keeps four indexed topics and only local mobile disclosure controls', () => {
  const about = JSON.parse(read('content/about.json'));
  const words = about.cards.map((card) => card.paragraphs.join(' ').split(/\s+/).length);
  assert.equal(about.cards.length, 4);
  assert.ok(words.reduce((a, b) => a + b, 0) < 400);
  const html = read('dist/index.html');
  for (const card of about.cards) assert.ok(html.includes(`id="about-${card.id}-title"`));
  const region = html.slice(html.indexOf('id="about"'), html.indexOf('id="gifts"'));
  assert.doesNotMatch(region, /data-booking|data-contact|<a\s/);
  assert.equal((region.match(/data-about-tab=/g)||[]).length,0);
  assert.equal((region.match(/data-about-more/g)||[]).length,4);
});

test('the article icon uses the ready Lucide file-text geometry', () => {
  const provenance = JSON.parse(read('content/ui-icon-sources.json'));
  const source = read('src/components/Icon.astro');
  for (const path of provenance.article.paths) assert.ok(source.includes(path));
  assert.ok(provenance.article.source.endsWith('lucide\\file-text.svg'));
});

test('long story dialogs start native reading at their heading inside the scrollport', () => {
  const story = read('src/components/MasterStory.astro');
  assert.match(story, /<Title[^>]*tabindex=\{dialog\?-1:undefined\}[^>]*autofocus=\{dialog\}/);
  const masters = read('src/components/Masters.astro');
  assert.match(masters, /<MaterialSurface>[\s\S]*<MasterStory article=\{story\} dialog/);
});
