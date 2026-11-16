export function orderDeck(order: readonly number[], active: number, colors: readonly string[]): number[] {
  const placed = [active];
  function arrange(remaining: number[]): number[] | undefined {
    if (remaining.length === 0)
      return colors[placed[placed.length - 1]] !== colors[active] ? [...placed] : undefined;
    for (const [index, item] of remaining.entries()) {
      if (colors[item] === colors[placed[placed.length - 1]]) continue;
      placed.push(item);
      const result = arrange(remaining.filter((_, other) => other !== index));
      placed.pop();
      if (result) return result;
    }
  }
  // Try the previous front first, then keep the existing relative order where possible.
  const result = arrange(order.filter((item) => item !== active));
  if (!result) throw new Error("Adjacent service-card colours cannot be separated");
  return result;
}
