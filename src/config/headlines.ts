import site from '../../content/site.json' with {type:'json'};
// Desktop copy and independent short mobile slogans have one explicit owner.
export const headlines = {
  services:{desktop:['Хорошие стрижки','— норма жизни!'],mobile:['Стрижка —','норма жизни!']},
  offers:{desktop:['Хорошему','товарищу','— особое','внимание'],tablet:['Хорошему товарищу','— особое внимание'],mobile:['Своим —','всё лучшее!']},
  masters:{desktop:['Твой стиль','— в хороших руках'],mobile:['Стиль в','наших руках']},
  works:{desktop:['Мастерство в деле','— результат налицо'],mobile:['Мастерство','налицо']},
  fair:{desktop:['Хорошая стрижка','— дело чести!'],mobile:['Стрижка','— дело чести!']},
  about:{desktop:['СОЮЗ стиля','и характера'],mobile:['Союз стиля','и характера']},
  gifts:{desktop:['Стригись в СОЮЗе','получай подарки'],mobile:['Стрижки','и подарки']},
  reviews:{desktop:['Нас рекомендуют.','Нам доверяют.'],mobile:['Наши гости','рекомендуют']},
  faq:{desktop:['Знание — сила.','Спрашивай, товарищ!'],mobile:['Спрашивай,','товарищ!']},
  contacts:{desktop:['СОЮЗ рядом,','заходи на стрижку'],mobile:['Союз рядом,','заходи!']},
  promo:{desktop:['Первый визит',`со скидкой ${site.firstVisitPercent}%`],mobile:['Первый визит',`со скидкой ${site.firstVisitPercent}%`]},
  certificate:{desktop:['Подарочные','сертификаты'],mobile:['Подарочные','сертификаты']},
} as const;
