import site from '../../content/site.json';
export const reviewYandex='https://yandex.ru/maps/?text=Союз+барбершоп+Киров';
export type ReviewExtraContent={id:string;title:string;name:string;copy:string;href?:string};
export const reviewExtrasEnabled=false;
export const reviewExtras:ReviewExtraContent[]=[
 {id:'reviews-yandex',title:'Ещё больше на Яндексе',name:'Яндекс Карты',href:reviewYandex,copy:'Впечатления гостей, оценки и фотографии после стрижки.'},
 {id:'reviews-coffee',title:'Кофе за отзыв',name:'Оставить отзыв',copy:'Поделись честным впечатлением о СОЮЗе. В благодарность приготовим зерновой кофе с собой.'},
 {id:'reviews-vk',title:'Истории во ВКонтакте',name:'ВКонтакте',href:site.vk,copy:'Отзывы, фотографии и истории в нашем сообществе.'},
];
