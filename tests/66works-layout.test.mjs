import {test} from 'node:test';
import assert from 'node:assert/strict';
import {workOffset,workIndex,workOrder,workDepth,workTilt,workDragTravel} from '../src/scripts/works-layout.ts';
import {projectedSwipeDistance,swipeDirection} from '../src/scripts/gesture-math.ts';
import {headlines} from '../src/config/headlines.ts';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {workPhotos,workSequence,workMasters,worksSourceStatus,workCategories,mergeVerifiedWorks,applyReviewedWorkTitles} from '../src/content/works.ts';
const read=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
const catalog=JSON.parse(read('content/work-photos.json')),ownerCatalog=JSON.parse(read('content/work-photos-owner.json')),titleCatalog=JSON.parse(read('content/work-photo-titles.json'));

test('every cyclic selection has one center and distinct fan positions through two complete turns',()=>{
 for(const total of [5,7,12,20])for(let turn=0;turn<total*2;turn++){
  const selected=turn%total,offsets=Array.from({length:total},(_,index)=>workOffset(index,selected,total));
  assert.equal(offsets[selected],0);assert.equal(offsets.filter(value=>value===0).length,1);assert.equal(new Set(offsets).size,total);
  assert.equal(offsets[(selected+1)%total],1);assert.equal(offsets[(selected+total-1)%total],-1);
  assert.equal(offsets.filter(value=>Math.abs(value)<=2).length,5);
 }
});

test('fractional fan positions remain cyclic through long held drags and reversals',()=>{
 for(const total of [5,7,12])for(const position of [-101.75,-12.5,-.25,0,.5,2.75,99.25]){
  const offsets=Array.from({length:total},(_,index)=>workOffset(index,position,total));
  assert.ok(offsets.every(value=>value>=-total/2&&value<total/2));
  assert.equal(new Set(offsets).size,total);assert.ok(workIndex(position,total)>=0&&workIndex(position,total)<total);
  assert.ok(Math.abs(workOffset(workIndex(position,total),position,total))<=.5);
 }
 assert.ok(projectedSwipeDistance(-400,-20,150)>=-452.5);assert.equal(projectedSwipeDistance(-400,2,150),-400);
 assert.equal(swipeDirection(-25,-.5,200),1);assert.equal(swipeDirection(25,.5,200),-1);
});

test('touch travel uses the actual portrait width instead of the densely overlapped fan spacing',()=>{
 for(const cardWidth of[238,296,360,400,440])for(const spacing of[1,12,28,65]){
  const travel=workDragTravel(cardWidth,spacing,true,84);assert.ok(travel>=84&&travel>=cardWidth*.35);assert.ok(Math.abs(projectedSwipeDistance(20,0,travel)/travel)<.25);assert.equal(Math.round(20/travel),0);assert.equal(workDragTravel(cardWidth,spacing,false,84),spacing);
 }
 assert.equal(workDragTravel(296,0,false,84),1);
});

test('filtered fan depths fit the real photo count and each stable photo key keeps its small individual tilt',()=>{
 for(let total=0;total<=12;total++)for(const limit of [1,2,4]){
  const depth=workDepth(total,limit);assert.ok(depth>=0&&depth<=limit);if(total)assert.ok(depth*2+1<=total);
 }
 const ids=['review-01-1','review-02-1','review-03-1','review-04-1'];
 assert.ok(new Set(ids.map(workTilt)).size>1);
 for(const id of ids){assert.ok([-2,-1,1,2].includes(workTilt(id)));assert.equal(workTilt(id),workTilt(id));}
});

test('random logical order preserves the SSR center and includes every photo once per complete turn',()=>{
 for(const total of [5,7,12])for(const value of [0,.25,.5,.999]){
  const order=workOrder(total,()=>value);assert.equal(order[0],0);assert.equal(order.length,total);assert.equal(new Set(order).size,total);
  assert.deepEqual([...order].sort((a,b)=>a-b),Array.from({length:total},(_,index)=>index));
  assert.deepEqual(Array.from({length:total},(_,index)=>order[workIndex(index,total)]),order);
 }
 assert.notDeepEqual(workOrder(12,()=>0),workOrder(12,()=>.999));
});

test('production Works and isolated concepts share one verified merged catalog without duplicate frames or fabricated VK IDs',()=>{
 const source=read('src/content/works.ts'),concepts=read('src/content/works-concepts.ts');
 assert.match(concepts,/export \{workPhotos,workMasters,workSequence\} from '\.\/works'/);
 assert.equal(worksSourceStatus,'verified-combined');assert.equal(workPhotos.length,catalog.photos.length+ownerCatalog.photos.length);assert.equal(new Set(workPhotos.map(photo=>photo.id)).size,workPhotos.length);assert.equal(workPhotos,workSequence);assert.equal(workMasters.length,6);
 assert.deepEqual(workCategories.map(category=>category.id),['haircuts','beards','kids'].filter(id=>workPhotos.some(photo=>photo.categories.includes(id))));assert.ok(!/review-media|reviews\.json|length!==12/.test(source));
 for(const photo of workPhotos){
  const original=[...catalog.photos,...ownerCatalog.photos].find(item=>item.id===photo.id),assessment=titleCatalog.photos.find(item=>item.id===photo.id),style=titleCatalog.catalog.find(item=>item.id===assessment.primaryId);assert.equal(photo.caption,`${style.en} (${style.displayRu??style.ru})`);assert.deepEqual(photo.titleAssessment,assessment);assert.equal(photo.provenance[0].title,original.title);assert.deepEqual(photo.categories,original.categories);assert.ok(photo.masterName&&photo.alt.includes(photo.masterName));
  assert.deepEqual(photo.variants,original.variants);assert.ok(photo.provenance.length>=1);
  if(photo.id.startsWith('owner-')){assert.ok(!('photoId'in photo)&&!('postId'in photo)&&!('albumId'in photo));assert.deepEqual(photo.provenance,[original]);}
  else assert.deepEqual(photo.provenance[0],{...original,source:'vk-public-wall'});
 }
 for(const duplicate of ownerCatalog.duplicates){const canonical=workPhotos.find(photo=>photo.id===duplicate.duplicateOf);assert.deepEqual(canonical.provenance.find(item=>item.sourceSha256===duplicate.sourceSha256),duplicate);assert.ok(!workPhotos.some(photo=>photo.id===duplicate.id));assert.equal(canonical.masterId,duplicate.masterId);}
 assert.ok(workPhotos.some(photo=>photo.categories.includes('haircuts')&&photo.categories.includes('beards')));
 const index=read('src/pages/index.astro');assert.match(index,/<ServiceDeck \/><Offers \/><Masters \/><Works \/>/);
 const component=read('src/components/Works.astro');assert.ok(!component.includes('RailControls'));assert.match(component,/data-work-controls/);assert.ok(!/work-tint|<dialog|href=|MaterialSurface/.test(component));
 assert.ok(!/SelectControl|data-work-filter/.test(component));assert.match(component,/data-work-master-tab/);assert.match(component,/<button class="work-card/);assert.match(component,/data-press-target/);assert.match(component,/data-press-surface/);
 assert.match(component,/hidden=\{distance>depth\}/);
 const css=read('src/styles/works.css');assert.ok(!/gradient|backdrop-filter|--work-tone|--work-border/.test(css));assert.match(css,/aspect-ratio:3\/4/);assert.match(css,/overflow:visible/);assert.match(css,/border:0/);
 assert.match(component,/aria-label=\{`Выбрать фото: \$\{photo.caption\}\. \$\{photo.masterName\}`\}/);
 assert.match(component,/String\(import\.meta\.env\.SOYUZ_RELEASE\)==='1'&&String\(worksSourceStatus\)!=='verified-combined'/);assert.match(component,/throw new Error\('SOYUZ release requires verified combined work photographs/);
 assert.equal(headlines.works.desktop.length,2);assert.equal(headlines.works.mobile.length,2);
 assert.deepEqual(headlines.works.desktop,['Мастерство в деле','— результат налицо']);assert.deepEqual(headlines.works.mobile,['Мастерство','налицо']);
});

test('catalog merge rejects missing authority, unknown credits, unconfirmed joins and duplicate frames',()=>{
 const invalid=mutate=>{const wall=structuredClone(catalog),owner=structuredClone(ownerCatalog);mutate(wall,owner);assert.throws(()=>mergeVerifiedWorks(wall,owner));};
 invalid((wall,owner)=>{owner.ownerCreditAuthority=false;});
 invalid((wall,owner)=>{owner.photos[0].evidence.masterId='souz-sonya-kid';});
 invalid((wall,owner)=>{owner.photos[0].masterId='invented-master';});
 invalid((wall,owner)=>{owner.photos[0].variants[0].url='/wrong-source.webp';});
 invalid((wall,owner)=>{owner.photos.push(structuredClone(owner.photos[0]));});
 invalid((wall,owner)=>{owner.photos[1].pixelSha256=owner.photos[0].pixelSha256;});
 invalid((wall,owner)=>{owner.duplicates[0].frameMatches[0].confirmed=false;});
 invalid((wall,owner)=>{owner.duplicates[0].duplicateOf='vk-999';});
 invalid((wall,owner)=>{owner.duplicates[0].frameMatches[0].sourceSha256='0'.repeat(64);});
 invalid((wall,owner)=>{owner.photos[0].frameMatches=[structuredClone(owner.duplicates[0].frameMatches[0])];});
});

test('a confirmed explicit owner credit override wins without rewriting API lineage or reusing owner derivatives',()=>{
 const wall=structuredClone(catalog),owner=structuredClone(ownerCatalog),duplicate=owner.duplicates[0];
 const original=wall.photos.find(photo=>photo.id===duplicate.duplicateOf),different=workMasters.find(master=>master.id!==original.masterId).id;
 duplicate.masterId=different;duplicate.evidence.masterId=different;
 assert.throws(()=>mergeVerifiedWorks(wall,owner),/requires explicit reviewed override/);
 owner.overrides.push({vkId:duplicate.duplicateOf,masterId:different,evidence:duplicate.ownerFilename,sourceSha256:duplicate.sourceSha256,match:duplicate.frameMatches[0].match,confirmed:true});
 const merged=mergeVerifiedWorks(wall,owner),row=merged.find(photo=>photo.id===duplicate.duplicateOf);
 assert.equal(row.masterId,different);assert.equal(row.caption,original.title);assert.deepEqual(row.variants,original.variants);assert.equal(row.provenance[0].masterId,original.masterId);assert.equal(row.provenance[1].evidence.masterId,different);assert.equal(original.masterId,catalog.photos.find(photo=>photo.id===original.id).masterId);
 owner.overrides[0].confirmed=false;assert.throws(()=>mergeVerifiedWorks(wall,owner),/requires explicit reviewed override/);
});

test('display labels cover the exact source union, use one catalog primary, and preserve raw source captions',()=>{
 const merged=mergeVerifiedWorks(catalog,ownerCatalog),reviewed=applyReviewedWorkTitles(merged,titleCatalog);
 assert.equal(reviewed.length,merged.length);assert.equal(titleCatalog.photos.length,merged.length);
 for(let i=0;i<reviewed.length;i++){assert.deepEqual(reviewed[i].provenance,merged[i].provenance);assert.equal(reviewed[i].masterId,merged[i].masterId);assert.equal(reviewed[i].variants,merged[i].variants);assert.ok(!reviewed[i].caption.includes(' · '));assert.ok(reviewed[i].alt.startsWith(reviewed[i].caption));}
 const invalid=mutate=>{const review=structuredClone(titleCatalog);mutate(review);assert.throws(()=>applyReviewedWorkTitles(merged,review));};
 invalid(review=>review.photos.pop());invalid(review=>{review.photos[0].id='unknown-photo';});invalid(review=>{review.photos[0].primaryId='unknown-style';});invalid(review=>{review.photos[0].confidence='unreviewed';});invalid(review=>{review.photos[0].secondaryIds=['unknown-style'];});invalid(review=>{review.photos[0].basis='';});invalid(review=>review.photos.push(structuredClone(review.photos[0])));
});

test('the actual SSR release guard rejects provisional/single-source photographs and permits the verified union or private preview',()=>{
 const component=readFileSync(new URL('../src/components/Works.astro',import.meta.url),'utf8');
 const guard=component.split(/\r?\n/).find(line=>line.startsWith("if(String(import.meta.env.SOYUZ_RELEASE)==='1'"));assert.ok(guard);
 const check=(release,status)=>runInNewContext(guard.replace('import.meta.env','environment'),{environment:{SOYUZ_RELEASE:release},worksSourceStatus:status});
 for(const status of['review-provisional','vk-albums','vk-public-wall','owner-supplied'])assert.throws(()=>check('1',status),/requires verified combined work photographs/);
 assert.throws(()=>check(1,'review-provisional'),/requires verified combined work photographs/);
 assert.doesNotThrow(()=>check('1','verified-combined'));assert.doesNotThrow(()=>check(undefined,'review-provisional'));
});
