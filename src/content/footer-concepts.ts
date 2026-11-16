import site from '../../content/site.json';
import legal from '../../content/legal/pages.json';
import operator from '../../content/legal/operator.json';
import {footerNavigation} from '../config/navigation';
import {bookingURLs} from '../scripts/booking-url';

export const footerFacts={brand:site.brand,city:site.city,address:site.address,hours:site.hours,phone:site.phone,phoneHref:`tel:${site.phoneLink}`,booking:bookingURLs(site.bookingUrl)!.publicUrl};
const phoneBreak=footerFacts.phone.indexOf(')')+1;
export const footerPhoneLines=phoneBreak?[footerFacts.phone.slice(0,phoneBreak),footerFacts.phone.slice(phoneBreak).trim()]:[footerFacts.phone];
export const footerDisplayAddress=footerFacts.address.replace(' ','\u00a0');
export const footerLegal=legal.pages.map(page=>({title:page.title,href:`/${page.slug}`}));
export const footerOperator={name:operator.legalName,inn:operator.inn,ogrnip:operator.ogrnip};
export const footerLinks=footerNavigation.map(link=>({...link,label:link.id==='gifts'?'Подарки за визиты':link.label,href:`/#${link.id}`}));
export const footerLinkGroups=[footerLinks.slice(0,3),footerLinks.slice(3,6),footerLinks.slice(6,9)];
export const footerConcepts=[
 {id:'01',name:'Большая марка',signature:'masthead',tone:'ink',density:1.1,description:'Большая марка занимает верхнюю полосу. Под ней — навигационный пояс, факты и действия.'},
 {id:'02',name:'Главный телефон',signature:'telephone',tone:'paper',density:1,description:'Телефон становится главным типографским объектом слева. Справа — адрес и спокойный справочник.'},
 {id:'03',name:'Газетная полоса',signature:'gazette',tone:'paper',density:1,description:'Четыре непрерывные колонки, общие линейки и распределённые контакты. Композиция напоминает печатную полосу.'},
 {id:'04',name:'Билет СОЮЗа',signature:'ticket',tone:'red',density:1,description:'Адрес и часы собраны в корешке. Основное поле билета содержит разделы сайта и запись.'},
 {id:'05',name:'Указатель',signature:'wayfinding',tone:'ink',density:1,description:'Главный элемент — девять направлений по сайту. Указательные стрелки ведут к нужному разделу.'},
 {id:'06',name:'Прямая запись',signature:'booking',tone:'paper',density:1,description:'Сначала — широкая полоса онлайн-записи. Под ней расположен компактный справочник без второго крупного акцента.'},
 {id:'07',name:'Два поля',signature:'split',tone:'ink',density:1,description:'Левое поле посвящено посещению и связи, правое — разделам сайта и документам. Две функции разделены цветом и структурой.'},
 {id:'08',name:'Три колонки',signature:'columns',tone:'paper',density:1,description:'Три функциональные вертикали: услуги и адрес, визиты и запись, вопросы и связь. Навигация распределена между ними.'},
 {id:'09',name:'Адрес-плакат',signature:'address',tone:'red',density:1.1,description:'Справочная часть открывает подвал, крупный адрес завершает его как плакат. Главный акцент находится внизу.'},
 {id:'10',name:'Две полосы',signature:'compact',tone:'ink',density:.85,description:'Две плотные зоны: факты и действия сверху, навигация и документы снизу. Компактная композиция без большого героя.'},
] as const;
export type FooterConcept=typeof footerConcepts[number];
