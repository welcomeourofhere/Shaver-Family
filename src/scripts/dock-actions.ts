export type DockAction = {label:string;action:string;primary?:boolean;short?:string};
export function dockActions(section:string):readonly DockAction[] {
  const states:Record<string,readonly DockAction[]>={
    top:[{label:'Промокод',short:'Код',action:'promo'},{label:'Записаться',short:'Запись',action:'booking'}],
    'welcome-offer':[{label:'Промокод',action:'promo'},{label:'Записаться',action:'welcome-booking'}],
    promotions:[{label:'Промокод',action:'promo'},{label:'Кешбэк',action:'cashback-info'},{label:'Записаться',action:'welcome-booking'}],
    cashback:[{label:'Об акции',action:'cashback-info'}],
    services:[{label:'Категории',short:'Цены',action:'categories'},{label:'Записаться',short:'Запись',action:'service-booking'}],
    offers:[{label:'Назад',action:'offer-prev'},{label:'Об акции',short:'Акция',action:'offer-action',primary:true},{label:'Далее',action:'offer-next'}],
    masters:[{label:'Знакомство',short:'Мастер',action:'master-story'},{label:'Записаться',short:'Запись',action:'master-booking'}],
    works:[{label:'Назад',action:'work-prev'},{label:'К мастеру',short:'Запись',action:'work-booking',primary:true},{label:'Далее',action:'work-next'}],
    'first-visit':[{label:'К Соне',action:'visit-sonya'},{label:'К Свете',action:'visit-sveta'}],
    gifts:[{label:'Сертификат',action:'certificates'}],
    certificates:[{label:'Номинал',action:'certificate-next'},{label:'Приобрести',action:'certificate-buy'}],
    reviews:[{label:'Оставить отзыв',short:'Отзыв',action:'review-write'}],
    faq:[{label:'Спросить',action:'contact'}],
    contacts:[{label:'Маршрут',action:'map-route'},{label:'Записаться',short:'Запись',action:'booking'}],
    footer:[{label:'Маршрут',action:'map-route'},{label:'Записаться',short:'Запись',action:'booking'}],
    article:[{label:'Мастера',action:'masters'},{label:'Записаться',short:'Запись',action:'article-booking'}],
    about:[{label:'Записаться',action:'booking'}],
  };
  return states[section]??[{label:'Услуги',action:'services'},{label:'Записаться',action:'booking'}];
}
