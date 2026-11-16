export const navigation = [
  {id:'services',label:'Услуги и цены',short:'Цены'},
  {id:'masters',label:'Мастера',short:'Мастера'},
  {id:'works',label:'Работы',short:'Работы'},
  {id:'gifts',label:'Подарки',short:'Подарки'},
  {id:'offers',label:'Акции',short:'Акции'},
  {id:'about',label:'О СОЮЗе',short:'О СОЮЗе'},
  {id:'certificates',label:'Сертификаты',short:'Сертификат'},
  {id:'reviews',label:'Отзывы',short:'Отзывы'},
  {id:'faq',label:'Вопросы',short:'Вопросы'},
  {id:'contacts',label:'Контакты и карта',short:'Контакты'},
] as const;
export const footerNavigation=['services','masters','works','about','offers','gifts','certificates','reviews','faq','contacts'].map(id=>navigation.find(link=>link.id===id)!);
