import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import offers from '../content/offers.json' with { type: 'json' };
import posters from '../content/offer-poster-sources.json' with { type: 'json' };

test('each offer has its own responsive poster with matching source and delivery hashes', () => {
  assert.deepEqual(posters.images.map(x => x.id), offers.offers.map(x => x.id));
  assert.equal(new Set(posters.images.map(x => x.composition)).size, 11);
  assert.equal(new Set(posters.images.map(x => x.sourceSha256)).size, 11);
  const digest = path => createHash('sha256').update(readFileSync(new URL('../' + path, import.meta.url))).digest('hex');
  for (const poster of posters.images) {
    assert.equal(digest(poster.source), poster.sourceSha256);
    assert.ok(Math.abs(poster.sourceSize[0] / poster.sourceSize[1] - 25 / 27) < .01);
    assert.deepEqual(poster.variants.map(x => x.width), [640, 1200]);
    for (const variant of poster.variants) {
      assert.equal(digest('public' + variant.url), variant.sha256);
      assert.ok(variant.bytes < 350000, variant.url);
    }
  }
});
