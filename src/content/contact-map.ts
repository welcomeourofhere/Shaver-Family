// Verified business point, read from the public Yandex business widget on 2026-11-09.
// The business widget and its external route share this verified location.
export const contactMap={
 longitude:49.669973,latitude:58.588674,
 source:'https://yandex.ru/maps/org/soyuz/116019915414/',
} as const;
export const contactMapEmbed=`https://yandex.ru/map-widget/v1/?ll=${encodeURIComponent(`${contactMap.longitude},${contactMap.latitude}`)}&mode=search&oid=116019915414&ol=biz&z=17`;
export const contactMapRoute=`https://yandex.ru/maps/?rtext=~${encodeURIComponent(`${contactMap.latitude},${contactMap.longitude}`)}`;
