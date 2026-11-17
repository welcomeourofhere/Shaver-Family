import site from '../../content/site.json';
import operator from '../../content/legal/operator.json';
import registry from '../../content/legal/pages.json';
import policy from '../../content/legal/privacy-policy.json';
import consent from '../../content/legal/privacy-data.json';
import offer from '../../content/legal/oferta.json';

const values:Record<string,string>={BUSINESS_LEGAL_NAME:operator.legalName,BUSINESS_INN:operator.inn,BUSINESS_OGRNIP:operator.ogrnip,BUSINESS_LEGAL_ADDRESS:operator.legalAddress,BUSINESS_EMAIL:operator.email,BUSINESS_ADDRESS_FULL:`г. ${site.city}, ${site.address}`,BUSINESS_HOURS_LONG:`ежедневно ${site.hours}`,BUSINESS_MAIN_SITE_URL:'https://soyuz.hair/',BUSINESS_PHONE_DISPLAY:site.phone};
const resolve=(text:string)=>text.replace(/\{\{([A-Z_]+)\}\}/g,(_,key:string)=>{if(!(key in values))throw new Error(`Unknown legal field ${key}`);return values[key];});
interface Section {id:string;title:string;paragraphs:string[];links?:string[];requisites?:boolean;}
const documents:Record<string,{sections:Section[];revision:string}>={'privacy-policy':policy,'privacy-data':consent,oferta:offer};
export const legalDocuments=registry.pages.map(page=>({...page,revision:documents[page.slug].revision,sections:documents[page.slug].sections.map(section=>({...section,paragraphs:section.paragraphs.map(resolve)}))}));
export type LegalDocument=typeof legalDocuments[number];
export const requisites=[['Исполнитель',operator.legalName],['ИНН',operator.inn],['ОГРНИП',operator.ogrnip],['Адрес для обращений',operator.legalAddress],['Электронная почта',operator.email],['Телефон',site.phone],['Банк',operator.bank.name],['Расчётный счёт',operator.bank.account],['Корреспондентский счёт',operator.bank.correspondentAccount],['БИК',operator.bank.bic]];
