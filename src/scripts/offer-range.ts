export function visibleOfferRange(
  scrollLeft: number,
  viewportWidth: number,
  cardStep: number,
  total: number,
): { first: number; last: number } {
  if (total <= 0 || cardStep <= 0) return { first: 0, last: 0 };
  const visible = Math.max(1, Math.round(viewportWidth / cardStep));
  const first = Math.max(
    1,
    Math.min(total - visible + 1, Math.round(scrollLeft / cardStep) + 1),
  );
  return { first, last: Math.min(total, first + visible - 1) };
}
