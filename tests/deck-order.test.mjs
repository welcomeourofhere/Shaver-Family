import { test } from "node:test";
import assert from "node:assert/strict";
import { orderDeck } from "../src/scripts/deck-order.ts";

function permutations(items) {
  if (items.length === 0) return [[]];
  return items.flatMap((item, index) =>
    permutations(items.filter((_, other) => other !== index)).map((rest) => [item, ...rest]),
  );
}
function hasDistinctNeighbours(order, colors) {
  return order.every((item, index) => colors[item] !== colors[order[(index + 1) % order.length]]);
}

test("promoting a repeated red card also separates the first and last colours", () => {
  const colors = ["blue", "red", "ink", "yellow", "red"];
  const order = orderDeck([0, 1, 2, 3, 4], 1, colors);
  assert.equal(order[0], 1);
  assert.equal(order[1], 0);
  assert.ok(hasDistinctNeighbours(order, colors));
});

test("the previous front moves deeper when its colour matches the selected card", () => {
  const colors = ["blue", "red", "ink", "yellow", "red"];
  const order = orderDeck([1, 0, 2, 3, 4], 4, colors);
  assert.equal(order[0], 4);
  assert.notEqual(order[1], 1);
  assert.ok(hasDistinctNeighbours(order, colors));
});

test("an impossible cyclic palette reports the source error", () => {
  assert.throws(() => orderDeck([0, 1, 2], 0, ["red", "red", "blue"]), /cannot be separated/);
});

test("all five-card promotions preserve every card and cyclic colour separation with stable priorities", () => {
  const arrangements = permutations([0, 1, 2, 3, 4]);
  for (const repeated of ["blue", "red", "ink", "yellow"]) {
    const colors = Object.freeze(["blue", "red", "ink", "yellow", repeated]);
    for (const previous of arrangements) {
      const original = [...previous];
      Object.freeze(previous);
      for (let active = 0; active < colors.length; active++) {
        const order = orderDeck(previous, active, colors);
        assert.equal(order[0], active);
        assert.deepEqual([...order].sort(), [0, 1, 2, 3, 4]);
        assert.ok(hasDistinctNeighbours(order, colors), JSON.stringify({ previous, active, colors, order }));
        assert.deepEqual(previous, original);
        assert.deepEqual(orderDeck(previous, active, colors), order);
        const preferred = [active, ...previous.filter((item) => item !== active)];
        if (hasDistinctNeighbours(preferred, colors)) assert.deepEqual(order, preferred);
        if (previous[0] !== active) {
          const canKeepPrevious = arrangements.some((candidate) =>
            candidate[0] === active && candidate[1] === previous[0] && hasDistinctNeighbours(candidate, colors),
          );
          if (canKeepPrevious) assert.equal(order[1], previous[0]);
        }
      }
    }
  }
});
