import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";

const assets = JSON.parse(
  readFileSync(new URL("../content/assets.json", import.meta.url)),
);
test("every selected resource exists with its recorded hash and dimensions", () => {
  const resources = [
    ...Object.values(assets.images).flatMap((image) => {
      assert.ok(image.sourceSha256.match(/^[a-f0-9]{64}$/));
      assert.equal(image.variants.length, 2);
      for (const variant of image.variants) {
        assert.ok(variant.width > 0 && variant.height > 0);
        assert.ok(
          Math.abs(
            variant.width / variant.height -
              image.sourceWidth / image.sourceHeight,
          ) < 0.005,
        );
      }
      return image.variants;
    }),
    ...Object.values(assets.logos),
    ...Object.values(assets.fonts),
  ];
  assert.equal(Object.keys(assets.images).length, 8);
  for (const resource of resources) {
    assert.ok(resource.url.startsWith("/") && !resource.url.includes(".."));
    const bytes = readFileSync(
      new URL(`../public${resource.url}`, import.meta.url),
    );
    assert.equal(bytes.length, resource.bytes);
    assert.equal(
      createHash("sha256").update(bytes).digest("hex"),
      resource.sha256,
    );
  }
});
test("functional preview builds without private sources or false confirmation", () => {
  for (const path of ["index.html"]) {
    const file = new URL(`../dist/${path}`, import.meta.url);
    assert.ok(existsSync(file), "Run build before tests");
    const html = readFileSync(file, "utf8");
    assert.match(html, /noindex, nofollow/);
    assert.doesNotMatch(
      html,
      /(?:J:[\\/]|file:\/\/|запись подтверждена|n521588\.yclients|\.psd|\.cdr)/i,
    );
    assert.match(html, /СОЮЗ/);
  }
});
