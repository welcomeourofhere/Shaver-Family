import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dockActions} from '../src/scripts/dock-actions.ts';
import {visibleRailIndex,railItems} from '../src/scripts/rail-selection.ts';
import {navigation,footerNavigation} from '../src/config/navigation.ts';

test('the compact bar has one to three meaningful actions and keeps each original owner',()=>{
  const cases={top:['promo','booking'],services:['categories','service-booking'],masters:['master-story','master-booking'],works:['work-prev','work-booking','work-next'],offers:['offer-prev','offer-action','offer-next'],contacts:['map-route','booking'],footer:['map-route','booking'],'first-visit':['visit-sonya','visit-sveta'],certificates:['certificate-next','certificate-buy'],reviews:['review-write'],article:['masters','article-booking'],about:['booking'],faq:['contact'],gifts:['certificates']};
  for(const [section,expected] of Object.entries(cases)) {
    const actions=dockActions(section);
    assert.deepEqual(actions.map(item=>item.action),expected);
    assert.ok(actions.every(item=>item.label.trim()&&!/[\r\n]/u.test(item.label)));
  }
  assert.deepEqual(dockActions('unknown').map(item=>item.action),['services','booking']);
  assert.equal(dockActions('top')[0].label,'Промокод');
  assert.deepEqual(dockActions('welcome-offer').map(item=>item.action),['promo','welcome-booking']);
  assert.deepEqual(dockActions('cashback').map(item=>item.action),['cashback-info']);
  assert.deepEqual([...new Set(Object.keys(cases).map(section=>dockActions(section).length))].sort(),[1,2,3]);
  assert.equal(dockActions('offers').find(item=>item.primary)?.action,'offer-action');
  assert.equal(dockActions('works').find(item=>item.primary)?.action,'work-booking');
  assert.equal(dockActions('masters').find(item=>item.action==='master-story')?.label,'Знакомство');
});

test('native galleries select the most visible card without flickering at a tie',()=>{
  const bounds=[{left:-180,right:100},{left:112,right:392},{left:404,right:684}];
  assert.equal(visibleRailIndex(bounds,0,360),1);
  assert.equal(visibleRailIndex([{left:0,right:100},{left:100,right:200}],0,200,1),1);
  assert.equal(visibleRailIndex([],0,320),0);
  assert.equal(visibleRailIndex([{left:500,right:800}],0,320),0);
});

test('rail controls ignore hidden cards and Astro service nodes after reordering',()=>{
 const previous=globalThis.HTMLElement;
 class Item{constructor(id,tag='ARTICLE',hidden=false){this.id=id;this.tag=tag;this.hidden=hidden;}matches(){return ['SCRIPT','STYLE','TEMPLATE'].includes(this.tag);}}
 globalThis.HTMLElement=Item;
 try{
  const a=new Item('a'),b=new Item('b'),hidden=new Item('hidden','ARTICLE',true),script=new Item('module','SCRIPT');
  const rail={children:[a,script,hidden,b]};assert.deepEqual(railItems(rail).map(c=>c.id),['a','b']);
  rail.children=[b,script,a,hidden];hidden.hidden=false;assert.deepEqual(railItems(rail).map(c=>c.id),['b','a','hidden']);
 }finally{globalThis.HTMLElement=previous;}
});

test('an explicit gallery choice survives equally visible neighboring cards',()=>{
  const bounds=[{left:0,right:320},{left:332,right:652}];
  assert.equal(visibleRailIndex(bounds,0,748,0),0);
  assert.equal(visibleRailIndex(bounds,0,748,1),1);
  assert.equal(visibleRailIndex(bounds,0,748,99),1);
  assert.equal(visibleRailIndex(bounds,0,748,-1),0);
  assert.equal(visibleRailIndex(bounds,330,748,0),1);
});

test('header, footer and compact menu share real, unique destinations',()=>{
  const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
  assert.equal(new Set(navigation.map(link=>link.id)).size,navigation.length);
  assert.deepEqual(new Set(footerNavigation.map(link=>link.id)),new Set(navigation.map(link=>link.id)));
  for(const link of navigation)assert.ok(html.includes(`id="${link.id}"`));
  assert.ok(html.includes('id="review-dialog"'));
  assert.ok(html.includes('id="service-categories"'));
});
