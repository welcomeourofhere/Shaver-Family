import test from 'node:test';import assert from 'node:assert/strict';
import {planReviews,planReviewBatches,planReviewCarousel,reviewNeighbors,colorReviews,reviewLayoutRules} from '../src/scripts/review-layout.ts';
import {readFileSync} from 'node:fs';
const reviews=JSON.parse(readFileSync(new URL('../content/reviews.json',import.meta.url),'utf8')),ids=reviews.map(r=>r.id),rules=reviewLayoutRules(reviews);

function rectangle(plan){
 const cells=Array(plan.rows*plan.columns).fill(0);
 assert.equal(new Set(plan.tiles.map(t=>t.id)).size,plan.tiles.length);
 for(const tile of plan.tiles){
  assert.ok(tile.w<=2&&tile.h<=2,'no full-width strips or three-unit towers');
  assert.ok(tile.x>=0&&tile.y>=0&&tile.x+tile.w<=plan.columns&&tile.y+tile.h<=plan.rows);
  for(let y=tile.y;y<tile.y+tile.h;y++)for(let x=tile.x;x<tile.x+tile.w;x++)cells[y*plan.columns+x]++;
 }
 assert.ok(cells.every(n=>n===1),'all cells covered exactly once');
 for(const a of plan.tiles)for(const b of plan.tiles)if(a!==b&&reviewNeighbors(a,b))assert.notEqual(a.tone,b.tone);
}

test('desktop selects a varied six-to-eight review pool and packs only normal modules',()=>{
 for(const columns of [2,3,4]){
  const omissions=new Set(),orders=new Set(),seen=new Set();
  for(let seed=0;seed<500;seed++){
   const plan=planReviewBatches(ids,[],columns,seed,rules),first=plan.tiles.filter(t=>plan.initialIds.includes(t.id)),counts={};
   assert.ok(plan.tiles.length>=6&&plan.tiles.length<=8);
   if(columns===4)assert.equal(plan.tiles.length,7);
   if(columns===3)assert.equal(plan.tiles.length,6);
   assert.equal(first.length,columns===3?3:4);assert.ok(plan.initialIds.includes('review-07'));
   assert.equal(new Set(first.map(t=>t.tone)).size,first.length);
   assert.equal(new Set(plan.tiles.map(t=>t.tone)).size,4);
   assert.ok(first.every(t=>t.y+t.h<=plan.initialRows));assert.ok(plan.tiles.filter(t=>!plan.initialIds.includes(t.id)).every(t=>t.y>=plan.initialRows));
   assert.equal(first.reduce((n,t)=>n+t.w*t.h,0),columns*plan.initialRows);
   assert.equal(plan.tiles.filter(t=>t.w===2&&t.h===2).length,columns===4?1:0);
   assert.ok(first.every(t=>t.w*t.h===2),'the desktop feature belongs below the fixed preview');
   for(const tile of plan.tiles){
    assert.ok(ids.includes(tile.id)&&!tile.extra);seen.add(tile.id);
    if(rules.verticalIds.includes(tile.id))assert.ok(tile.w===1&&tile.h===2);
    if(tile.w*tile.h===2)counts[tile.w+'x'+tile.h]=(counts[tile.w+'x'+tile.h]||0)+1;
   }
   assert.equal(Object.keys(counts).length,2);assert.ok(Math.max(...Object.values(counts))<=Math.floor(2*plan.tiles.length/3));
   rectangle(plan);
   assert.deepEqual(planReviewBatches(ids,[],columns,seed,rules),plan);
   omissions.add(ids.filter(id=>!plan.tiles.some(t=>t.id===id)).join(','));orders.add(plan.tiles.map(t=>t.id).join(','));
  }
  assert.equal(seen.size,ids.length,'every source review participates across page seeds');
  assert.ok(omissions.size>4&&orders.size>100,'selection and order vary rather than permanently hiding the same reviews');
 }
});

test('compact carousel always keeps all source reviews, independent of desktop selection',()=>{
 for(let seed=0;seed<300;seed++){
  const tiles=planReviewCarousel(ids,seed,rules);
  assert.deepEqual(tiles.map(t=>t.id).sort(),[...ids].sort());assert.equal(new Set(tiles.map(t=>t.tone)).size,4);
  assert.ok(tiles.findIndex(t=>t.id==='review-07')<4);
  for(let i=0;i<tiles.length;i++){assert.equal(tiles[i].w,1);assert.equal(tiles[i].h,1);if(i)assert.notEqual(tiles[i].tone,tiles[i-1].tone);}
  assert.deepEqual(planReviewCarousel(ids,seed,rules),tiles);
 }
});

test('review captions use the correct master; Sonya and Sofya remain distinct identities',()=>{
 const team=JSON.parse(readFileSync(new URL('../content/team.json',import.meta.url),'utf8')).masters;
 for(const review of reviews){const master=team.find(m=>m.id===review.masterId);assert.ok(master);assert.equal(review.about,'О барбере '+master.bookingNameDative);}
 assert.equal(reviews.find(r=>r.id==='review-07').masterId,reviews.find(r=>r.id==='review-08').masterId);
 assert.notEqual(reviews.find(r=>r.id==='review-01').masterId,reviews.find(r=>r.id==='review-03').masterId);
});

test('exact packing rejects impossible areas instead of stretching a review into a strip',()=>{
 assert.equal(planReviews(ids,[],4,50,rules),null,'eight dominoes plus one feature occupy eighteen cells, not a four-column rectangle');
 assert.equal(planReviews(ids,[],3,50,rules),null,'sixteen cells cannot fill three columns without an extra or an omitted review');
 for(const [count,columns,extras,feature]of [[7,4,[],true],[8,4,['extra-a','extra-b'],true],[7,3,['extra-a'],false],[8,3,['extra-a','extra-b'],false],[8,2,[],false]])for(let seed=0;seed<100;seed++){
  const selected=ids.slice(0,count),plan=planReviews(selected,extras,columns,seed,{...rules,allowFeature:feature});
  assert.ok(plan);rectangle(plan);
  assert.deepEqual(plan.tiles.filter(t=>!t.extra).map(t=>t.id).sort(),[...selected].sort());
  assert.equal(plan.tiles.filter(t=>t.w===2&&t.h===2).length,feature?1:0);
  for(const tile of plan.tiles)if(rules.verticalIds.includes(tile.id))assert.ok(tile.w===1&&tile.h===2);
 }
 assert.deepEqual(planReviewBatches([],[],4,50).tiles,[]);
});

test('phone neighbours stay distinct while the palette varies between page seeds',()=>{
 const line=ids.map((id,x)=>({id,x,y:0,w:1,h:1,extra:false})),used=new Set();
 for(let seed=0;seed<100;seed++){const tones=colorReviews(line,seed);tones.forEach(tile=>used.add(tile.tone));for(let i=1;i<tones.length;i++)assert.notEqual(tones[i].tone,tones[i-1].tone);}
 assert.equal(used.size,4);
});

test('up to three videos stay near the top; larger video collections occupy separate groups',()=>{
 const selected=ids.slice(0,7);
 for(const count of [2,3,4])for(let seed=0;seed<80;seed++){
  const videos=selected.slice(0,count),p=planReviews(selected,[],4,seed,{videoIds:videos});assert.ok(p);
  const ordered=[...p.tiles].sort((a,b)=>a.y-b.y||a.x-b.x),ranks=ordered.flatMap((t,i)=>videos.includes(t.id)?[i]:[]);
  if(count<=3)assert.ok(ranks.every(i=>i<4));else assert.equal(new Set(ranks.map(i=>Math.floor(i*count/selected.length))).size,count);
 }
});
