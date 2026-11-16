import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const references = JSON.parse(
  readFileSync(new URL("../content/reference-assets.json", import.meta.url)),
);
test("selected reference resources match recorded exports without requiring the original library", () => {
  assert.deepEqual(Object.keys(references.images).sort(), [
    "certificate-1000",
    "certificate-3000",
    "certificate-back",
    "certificate-front",
    "gift-photo-4",
    "hero",
    "pioneer",
  ]);
  assert.deepEqual(references.giftPhotoIds, [4]);
  for (const asset of Object.values(references.images)) {
    const bytes = readFileSync(
      new URL(`../public${asset.url}`, import.meta.url),
    );
    assert.equal(bytes.length, asset.bytes);
    assert.equal(
      createHash("sha256").update(bytes).digest("hex"),
      asset.sha256,
    );
    assert.ok(asset.width > 0 && asset.height > 0);
  }
});

test("all six gift illustrations are original vector objects with no embedded raster or external references", () => {
  const manifest = JSON.parse(
    readFileSync(
      new URL("../content/gift-vector-sources.json", import.meta.url),
    ),
  );
  assert.equal(manifest.status, "verified-native-vector-export");
  assert.deepEqual(
    manifest.icons.map((icon) => icon.id),
    [1, 2, 3, 4, 5, 6],
  );
  for (const icon of manifest.icons) {
    const bytes = readFileSync(
      new URL(`../public${icon.url}`, import.meta.url),
    );
    assert.equal(createHash("sha256").update(bytes).digest("hex"), icon.sha256);
    const svg = bytes.toString("utf8");
    assert.match(svg, /<path\b/);
    assert.match(svg, /viewBox=/);
    assert.doesNotMatch(
      svg,
      /<image\b|<script\b|<foreignObject\b|data:|(?:xlink:)?href="(?!#)/i,
    );
    assert.equal(icon.embeddedImages, 0);
    assert.equal(icon.externalReferences, 0);
  }
});
test("built template contains requested sections, phrases, and has no nominal chooser or excluded sections", () => {
  const html = readFileSync(
    new URL("../dist/index.html", import.meta.url),
    "utf8",
  );
  for (const id of [
    "services",
    "offers",
    "masters",
    "about",
    "gifts",
    "certificates",
    "reviews",
    "contacts",
  ])
    assert.ok(html.includes(`id="${id}"`), id);
  const text=html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ');
  assert.ok(text.includes('Хорошие стрижки — норма жизни!'));
  assert.match(html.replaceAll('\u00a0',' '), /Стригись в СОЮЗе/);
  assert.doesNotMatch(
    html,
    /data-amount|id="lookbook"|id="models"|id="news"|data-product|запись подтверждена/i,
  );
});
