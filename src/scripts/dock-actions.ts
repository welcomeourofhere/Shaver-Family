export type DockAction = {label:string;action:string;primary?:boolean};
export function dockActions(section:string):readonly DockAction[] {
  const states:Record<string,readonly DockAction[]>={
    'welcome-offer':[{label:'Промокод',action:'promo'},{label:'Записаться',action:'welcome-booking'}],
    promotions:[{label:'Промокод',action:'promo'},{label:'Кешбэк',action:'cashback-info'},{label:'Записаться',action:'welcome-booking'}],
    cashback:[{label:'Об акции',action:'cashback-info'}],
    services:[{label:'Категории',action:'categories'},{label:'Записаться',action:'service-booking'}],
    offers:[{label:'Назад',action:'offer-prev'},{label:'Об акции',action:'offer-action',primary:true},{label:'Далее',action:'offer-next'}],
    masters:[{label:'Знакомство',action:'master-story'},{label:'Записаться',action:'master-booking'}],
    'first-visit':[{label:'К Соне',action:'visit-sonya'},{label:'К Свете',action:'visit-sveta'}],
    gifts:[{label:'Сертификат',action:'certificates'}],
    certificates:[{label:'Номинал',action:'certificate-next'},{label:'Приобрести',action:'certificate-buy'}],
    reviews:[{label:'Оставить отзыв',action:'review-write'}],
    faq:[{label:'Спросить',action:'contact'}],
    contacts:[{label:'Связаться',action:'contact'},{label:'Записаться',action:'booking'}],
    footer:[{label:'Связаться',action:'contact'},{label:'Записаться',action:'booking'}],
    article:[{label:'Мастера',action:'masters'},{label:'Записаться',action:'article-booking'}],
    about:[{label:'Записаться',action:'booking'}],
  };
  return states[section]??[{label:'Услуги',action:'services'},{label:'Записаться',action:'booking'}];
}
