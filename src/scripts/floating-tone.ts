export const floatingTones = ['red', 'blue', 'yellow', 'ink'] as const;
export type FloatingTone = typeof floatingTones[number];

/** A section advances the palette; a matching underlying surface is skipped. */
export function floatingTone(section: number, offset: number, behind?: FloatingTone): FloatingTone {
  const index = ((section + offset) % floatingTones.length + floatingTones.length) % floatingTones.length;
  const tone = floatingTones[index];
  return tone === behind ? floatingTones[(index + 1) % floatingTones.length] : tone;
}
