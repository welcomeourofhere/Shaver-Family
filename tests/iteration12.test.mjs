import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import team from "../content/team.json" with { type: "json" };
import design from "../src/config/design.json" with { type: "json" };
import provenance from "../content/contact-icon-sources.json" with { type: "json" };

test("owner review counts and short personal notes are attached to the correct six people", () => {
  assert.equal(team.ownerFactsAsOf, "2026-11-04");
  const expected = {
    "souz-svetlana": [37, "Бесконечно строит дачу"],
    "souz-sonya-kid": [41, "Любит смешные шапки"],
    "souz-milena": [99, "Любит падел и борщ"],
    "souz-darya": [114, "Рубит кроликов"],
    "souz-sofya-shalaginova": [213, "Любит вайбить"],
      "souz-lyubov": [544, "Любит готовить и растягиваться"],
  };
  for (const person of team.masters)
    assert.deepEqual([person.reviewCount, person.hobby], expected[person.id]);
  const html = readFileSync(
    new URL("../dist/index.html", import.meta.url),
    "utf8",
  );
  for (const label of [
    "37 отзывов",
    "41 отзыв",
    "99 отзывов",
    "114 отзывов",
    "213 отзывов",
    "544 отзыва",
  ])
    assert.ok(html.includes(label), label);
});

test("contact logos are the four recorded safe original SF symbols", () => {
  const bytes = readFileSync(
    new URL("../public/brand/contact-icons.svg", import.meta.url),
  );
  assert.equal(
    createHash("sha256").update(bytes).digest("hex"),
    provenance.sha256,
  );
  const svg = bytes.toString();
  assert.equal((svg.match(/<symbol /g) || []).length, 4);
  for (const name of ["telegram", "max", "vk", "phone"])
    assert.ok(svg.includes(`id="contact-${name}"`));
  assert.doesNotMatch(svg, /<script|<image|onload=|(?:href|src)=["'](?:https?:|data:|javascript:)/i);
});

test("gift surfaces use only primary brand colors without orthogonal repeats", () => {
  const colors = Array.from(
    { length: 6 },
    (_, i) => design.base[`--gift-bg-${i + 1}`],
  );
  assert.equal(new Set(colors).size, 4);
  for (const [i, color] of colors.entries()) {
    assert.match(color, /^var\(--(?:red|yellow|blue|ink)\)$/);
    if (i % 3 < 2) assert.notEqual(color, colors[i + 1]);
    if (i + 3 < colors.length) assert.notEqual(color, colors[i + 3]);
  }
});
