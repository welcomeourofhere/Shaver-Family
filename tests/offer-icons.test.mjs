import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import test from "node:test";
import sharp from "sharp";

const manifest = JSON.parse(
  readFileSync(new URL("../content/offer-icon-sources.json", import.meta.url)),
);
const offers = JSON.parse(
  readFileSync(new URL("../content/offers.json", import.meta.url)),
).offers;
const sha256 = (data) => createHash("sha256").update(data).digest("hex");

test("every offer has a distinct, traceable and safe vector illustration", async () => {
  assert.deepEqual(
    manifest.icons.map(({ id }) => id),
    offers.filter(({sourceId}) => sourceId).map(({ id }) => id),
  );
  assert.equal(new Set(manifest.icons.map(({ sha256 }) => sha256)).size, 10);
  assert.equal(
    manifest.icons.filter(
      ({ artworkType }) => artworkType === "native-brandbook-vector",
    ).length,
    4,
  );
  for (const icon of manifest.icons) {
    const data = readFileSync(new URL(`../public${icon.url}`, import.meta.url));
    const svg = data.toString("utf8");
    assert.equal(sha256(data), icon.sha256, icon.id);
    assert.equal(data.length, icon.bytes, icon.id);
    assert.match(svg, /viewBox="0 0 512 512"/);
    assert.doesNotMatch(
      svg,
      /<(?:image|script|foreignObject|text|style)\b|\son\w+\s*=|(?:href="(?!#))|(?:url\((?!#))/i,
    );
    const ids = [...svg.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
    assert.equal(new Set(ids).size, ids.length, icon.id);
    for (const match of svg.matchAll(/(?:url\(#([^)]*)\)|href="#([^"]*)")/g)) {
      assert.ok(
        ids.includes(match[1] ?? match[2]),
        `${icon.id}: missing gradient / clip reference`,
      );
    }
    if (icon.artworkType === "new-svg-illustration") {
      assert.deepEqual(icon.sourceLayerChildIndices, []);
      assert.match(icon.authoring, /not extracted or traced/);
    } else {
      assert.ok(icon.sourceLayerChildIndices.length > 0);
    }
    const { data: pixels, info } = await sharp(data)
      .ensureAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true });
    let opaque = 0;
    const colors = new Set();
    for (let y = 0; y < info.height; y++)
      for (let x = 0; x < info.width; x++) {
        const offset = (y * info.width + x) * 4;
        if (pixels[offset + 3] > 0) {
          opaque++;
          assert.ok(
            x > 12 && y > 12 && x < info.width - 13 && y < info.height - 13,
            `${icon.id}: cropped artwork`,
          );
          if (pixels[offset + 3] === 255)
            colors.add(
              `${pixels[offset] >> 4},${pixels[offset + 1] >> 4},${pixels[offset + 2] >> 4}`,
            );
        }
      }
    assert.ok(
      opaque > 25000 && opaque < info.width * info.height * 0.75,
      `${icon.id}: empty or opaque background`,
    );
    assert.ok(
      colors.size > 6,
      `${icon.id}: missing colored gradients / facets`,
    );
  }
});

test("offer assets and provenance are reproducible from the untouched source", () => {
  assert.equal(
    sha256(
      readFileSync(new URL(`../${manifest.nativeExport}`, import.meta.url)),
    ),
    manifest.nativeExportSha256,
  );
  const result = spawnSync(
    "python",
    ["scripts/prepare-offer-icons.py", "--check"],
    { cwd: new URL("..", import.meta.url), encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stdout + result.stderr);
});
