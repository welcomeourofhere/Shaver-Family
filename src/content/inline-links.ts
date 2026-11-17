import site from '../../content/site.json' with {type:'json'};
import contacts from '../../content/contacts.json' with {type:'json'};

export type LinkPart={text:string;href?:string};
const map=(address:string)=>`https://yandex.ru/maps/?text=${encodeURIComponent(`${site.city}, ${address}`)}`;
const targets=new Map<string,string>([
 [site.phone,`tel:${site.phoneLink}`],
 [site.address,map(site.address)],
 [site.futureAddress,map(site.futureAddress)],
 ...contacts.people.map(person=>[person.phoneDisplay,`tel:${person.phoneTel}`]as[string,string]),
]);
const escape=(text:string)=>text.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const pattern=new RegExp([...targets.keys()].sort((a,b)=>b.length-a.length).map(escape).join('|')+'|https?:\\/\\/[^\\s<>"\'«»]+|[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}','g');
const urlLabel=(raw:string)=>{
 let label=raw.replace(/[.,!?;:]+$/,'');
 while(/[)\]]$/.test(label)){
  const close=label.at(-1)!,open=close===')'?'(':'[';
  if(label.split(close).length<=label.split(open).length)break;
  label=label.slice(0,-1).replace(/[.,!?;:]+$/,'');
 }
 return label;
};

/** Links remain structured text, never HTML supplied by a paragraph. */
export function inlineLinks(text:string):LinkPart[]{
 const parts:LinkPart[]=[];let cursor=0;
 for(const match of text.matchAll(pattern)){
  const start=match.index!,raw=match[0];
  if(start>cursor)parts.push({text:text.slice(cursor,start)});
  const label=raw.startsWith('http')?urlLabel(raw):raw;
  const href=targets.get(label)??(label.startsWith('http')?label:`mailto:${label}`);
  parts.push({text:label,href});
  if(label.length<raw.length)parts.push({text:raw.slice(label.length)});
  cursor=start+raw.length;
 }
 if(cursor<text.length)parts.push({text:text.slice(cursor)});
 return parts;
}
