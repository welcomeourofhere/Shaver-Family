import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from 'parse5';
import {bookingURLs,certificateURLs} from '../src/scripts/booking-url.ts';

const root=new URL('../',import.meta.url),json=path=>JSON.parse(readFileSync(new URL(path,root),'utf8'));
const htmlRoot=resolve(process.env.SOYUZ_TEST_HTML_ROOT??fileURLToPath(new URL('../dist',import.meta.url)));
const site=json('content/site.json'),team=json('content/team.json').masters,offers=json('content/offers.json').offers;
const attr=(node,name)=>node.attrs?.find(a=>a.name===name)?.value;
const has=(node,name)=>node.attrs?.some(a=>a.name===name);
const nodes=node=>[node,...(node.childNodes??[]).flatMap(nodes)];
const hasClass=(node,name)=>attr(node,'class')?.split(/\s+/u).includes(name);
const document=path=>nodes(parse(readFileSync(resolve(htmlRoot,path),'utf8')));
const home=document('index.html');
const articles=readdirSync(new URL('../content/master-articles/',import.meta.url)).filter(name=>name.endsWith('.json')&&!name.endsWith('.media.json')).map(name=>json('content/master-articles/'+name));

function assertBookingLink(node,expected,label){
 assert.equal(node.tagName,'a',label+': native navigation must work before JavaScript');
 assert.equal(attr(node,'href'),bookingURLs(expected).publicUrl,label+': preserve company/path/query');
 assert.equal(attr(node,'aria-haspopup'),'dialog',label);
 assert.equal(attr(node,'aria-controls'),'booking-drawer',label);
 assert.ok(!has(node,'type'),label+': no button-only type on links');
}

test('every SSR booking action has a real native destination; the certificate keeps its new-tab contract',()=>{
 for(const [path,all]of [['index.html',home],...articles.map(article=>['masters/'+article.slug+'/index.html',document('masters/'+article.slug+'/index.html')])]){
  assert.equal(all.filter(n=>attr(n,'id')==='booking-drawer').length,1,path);
  const actions=all.filter(n=>has(n,'data-booking'));assert.ok(actions.length>0,path);
  for(const node of actions){
   if(attr(node,'data-booking-form')==='certificate'){
    assert.equal(node.tagName,'a');assert.equal(attr(node,'href'),certificateURLs(site.certificateUrl).publicUrl);
    assert.equal(attr(node,'target'),'_blank');assert.match(attr(node,'rel'),/noopener/);continue;
   }
   assertBookingLink(node,attr(node,'data-booking-url')??site.bookingUrl,path+' '+(attr(node,'class')??''));
   if(has(node,'data-master')){
    const master=team.find(master=>master.id===attr(node,'data-master'));assert.ok(master,path);
    assert.equal(attr(node,'data-booking-url'),master.bookingUrl,path);
    assert.equal(attr(node,'href'),bookingURLs(master.bookingUrl).publicUrl,path);
   }
  }
 }
});

test('master cards, dialogs, personal articles and fair-price links retain their distinct selected companies',()=>{
 const cardActions=home.filter(n=>hasClass(n,'team-book'));
 assert.equal(cardActions.length,team.length);
 for(const master of team){
  const actions=home.filter(n=>has(n,'data-booking')&&attr(n,'data-master')===master.id);
  assert.ok(actions.length>=2,master.id+': card and dialog');
  for(const action of actions)assertBookingLink(action,master.bookingUrl,master.id);
 }
 for(const article of articles){
  const all=document('masters/'+article.slug+'/index.html'),master=team.find(master=>master.id===article.masterId);
  assert.ok(all.some(n=>has(n,'data-booking')&&attr(n,'data-master')===master.id),article.slug);
 }
 const fair=home.find(n=>attr(n,'id')==='first-visit'),fairActions=nodes(fair).filter(n=>has(n,'data-booking'));
 assert.deepEqual(fairActions.map(n=>attr(n,'data-master')),offers.find(offer=>offer.id==='honest-price').eligibleMasterIds);
});

test('offer booking links preserve promo context while review and contact actions remain buttons',()=>{
 for(const offer of offers){
  const card=home.find(n=>attr(n,'data-offer-id')===offer.id),action=nodes(card).find(n=>hasClass(n,'of-action'));assert.ok(action,offer.id);
  if(offer.actionType==='booking'){
   assertBookingLink(action,site.bookingUrl,offer.id);assert.ok(attr(action,'data-context')?.includes(offer.title.replace(/^Акция:\s*/u,'')));
  }else if(['review','contact'].includes(offer.actionType)){
   assert.equal(action.tagName,'button',offer.id);assert.ok(!has(action,'href')&&!has(action,'data-booking'),offer.id);
   assert.ok(has(action,offer.actionType==='review'?'data-open-reviews':'data-contact'),offer.id);
  }
 }
});
