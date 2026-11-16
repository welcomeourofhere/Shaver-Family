import { test } from "node:test";
import assert from "node:assert/strict";
import source from "../src/config/design.json" with { type: "json" };

for (const [name, theme] of Object.entries(source.teamThemes)) {
  test(`${name}: every resting and singly highlighted team card differs from all orthogonal neighbors`, () => {
    const { columns, base, active } = theme;
    assert.equal(base.length, 6);
    assert.equal(active.length, base.length);
    assert.equal(new Set(base).size, 4);
    const neighbors = base.map((_, i) =>
      base.flatMap((_, j) =>
        (Math.floor(i / columns) === Math.floor(j / columns) &&
          Math.abs(i - j) === 1) ||
        Math.abs(i - j) === columns
          ? [j]
          : [],
      ),
    );
    for (let highlighted = -1; highlighted < base.length; highlighted++) {
      const colors = base.map((color, i) =>
        i === highlighted ? active[i] : color,
      );
      if (highlighted >= 0)
        assert.notEqual(colors[highlighted], base[highlighted]);
      for (const [i, adjacent] of neighbors.entries()) {
        assert.ok(["blue", "red", "yellow", "ink"].includes(colors[i]));
        for (const j of adjacent)
          assert.notEqual(
            colors[i],
            colors[j],
            `${name}, highlighted ${highlighted}, neighbors ${i}/${j}`,
          );
      }
    }
  });
}
