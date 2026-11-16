// Preview-only map point, read from the public business widget on 2026-11-09.
// The live site and its existing map are unchanged until a concept is selected.
export const contactMap={
 longitude:49.669973,latitude:58.588674,
 bounds:[49.6666,58.5871,49.6734,58.5903],
 source:'https://yandex.ru/maps/org/soyuz/116019915414/',
} as const;
export const contactMapEmbed=`https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(contactMap.bounds.join(','))}&layer=mapnik&marker=${encodeURIComponent(`${contactMap.latitude},${contactMap.longitude}`)}`;
