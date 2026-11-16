export const reviewPalette=['red','blue','yellow','ink'] as const;
export type ReviewTone=typeof reviewPalette[number];
export type ReviewTile={id:string;x:number;y:number;w:number;h:number;extra:boolean;tone:ReviewTone};
type Rect=Omit<ReviewTile,'tone'>;
type ReviewRules={verticalIds?:readonly string[];videoIds?:readonly string[];featureIds?:readonly string[];allowFeature?:boolean;formatLimits?:readonly [number,number]};
export function reviewLayoutRules(reviews:readonly {id:string;text:readonly string[];videoLocal?:string}[]):ReviewRules{
 const length=(review:{text:readonly string[]})=>review.text.join(' ').trim().length;
 return {verticalIds:reviews.filter(r=>length(r)<=220).map(r=>r.id),videoIds:reviews.filter(r=>r.videoLocal).map(r=>r.id),featureIds:reviews.filter(r=>length(r)>450).map(r=>r.id)};
}
export function reviewRandom(seed:number){return()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
export function shuffleReviews<T>(items:readonly T[],random:()=>number){const result=[...items];for(let i=result.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}return result;}
export function reviewNeighbors(a:Rect,b:Rect){return ((a.x+a.w===b.x||b.x+b.w===a.x)&&Math.max(a.y,b.y)<Math.min(a.y+a.h,b.y+b.h))||((a.y+a.h===b.y||b.y+b.h===a.y)&&Math.max(a.x,b.x)<Math.min(a.x+a.w,b.x+b.w));}

// Colour the actual shared-edge graph; palette order changes once per page load.
export function colorReviews(rects:Rect[],seed:number,fixed:ReadonlyMap<string,ReviewTone>=new Map()):ReviewTile[]|null{
 const random=reviewRandom(seed),palette=shuffleReviews(reviewPalette,random);
 const graph=rects.map((tile,i)=>rects.flatMap((other,j)=>i!==j&&reviewNeighbors(tile,other)?[j]:[]));
 const assigned:number[]=rects.map(tile=>fixed.has(tile.id)?palette.indexOf(fixed.get(tile.id)!):-1),order=rects.flatMap((_,i)=>assigned[i]<0?[i]:[]).sort((a,b)=>graph[b].length-graph[a].length);
 const colors=[...new Set(assigned.filter(color=>color>=0))];
 for(let color=0;colors.length<Math.min(4,rects.length);color++)if(!colors.includes(color))colors.push(color);
 const counts=palette.map(()=>0),preferences=rects.map(()=>shuffleReviews(colors,random));
 for(const [i,color]of assigned.entries())if(color>=0){counts[color]++;if(graph[i].some(j=>assigned[j]===color))return null;}
 const paint=(step:number):boolean=>{
  if(step===order.length)return colors.every(color=>counts[color]>0);
  const i=order[step];
  for(const color of [...colors].sort((a,b)=>counts[a]-counts[b]||preferences[i].indexOf(a)-preferences[i].indexOf(b)))if(graph[i].every(j=>assigned[j]!==color)){assigned[i]=color;counts[color]++;if(paint(step+1))return true;counts[color]--;assigned[i]=-1;}
  return false;
 };
 if(!paint(0))return null;
 return rects.map((tile,i)=>({...tile,tone:palette[assigned[i]]}));
}

/** Fixed modules cover the whole rectangle. Extras fill only the remaining area. */
export function planReviews(reviewIds:readonly string[],extraIds:readonly string[],columns:number,seed:number,rules:ReviewRules={}){
 columns=Math.max(2,Math.min(4,Math.floor(columns)));
 if(!reviewIds.length)return {columns,rows:0,tiles:[] as ReviewTile[],mode:'empty'};
 const random=reviewRandom(seed),ids=shuffleReviews(reviewIds,random),extras=shuffleReviews(extraIds,random);
 const vertical=new Set(rules.verticalIds),videos=new Set(rules.videoIds),featureIds=ids.filter(id=>!vertical.has(id)&&(!rules.featureIds?.length||rules.featureIds.includes(id)));
 const modes=columns===4&&rules.allowFeature!==false?['feature']:['compact'];
 for(const mode of modes){
  const bonus=mode==='feature'?2:0,rows=Math.ceil((ids.length*2+bonus)/columns),missing=columns*rows-ids.length*2-bonus;
  if(missing>extras.length)continue;
  const featureId=mode==='feature'?featureIds[0]:'';
  if(mode==='feature'&&!featureId)continue;
  const items=[...ids.map(id=>({id,extra:false,shapes:id===featureId?[[2,2]]:vertical.has(id)?[[1,2]]:shuffleReviews([[1,2],[2,1]],random)})),...extras.slice(0,missing).map(id=>({id,extra:true,shapes:[[1,1]]}))];
  const videoCount=ids.filter(id=>videos.has(id)).length,shapeCounts=[0,0],limit=ids.length>=4?Math.floor(ids.length*2/3):ids.length;
  const limits=rules.formatLimits??[limit,limit];
  const full=(1n<<BigInt(columns*rows))-1n,allItems=(1n<<BigInt(items.length))-1n,memo=new Set<string>(),placed:Rect[]=[];
  let visits=0,result:ReviewTile[]|null=null;
  const search=(occupied:bigint,remaining:bigint):boolean=>{
   if(++visits>12000)return false;
   if(!remaining){if(occupied!==full)return false;result=colorReviews(placed,seed^0x51A7);return !!result;}
   const key=occupied.toString(36)+':'+remaining.toString(36)+':'+shapeCounts.join(',');if(memo.has(key))return false;
   let first=0;while(occupied&(1n<<BigInt(first)))first++;
   const x=first%columns,y=Math.floor(first/columns);
   for(let i=0;i<items.length;i++){
    const bit=1n<<BigInt(i);if(!(remaining&bit))continue;
    // One video belongs near the top; several videos occupy separate, evenly spaced groups.
    const rank=placed.length;
    if(videos.has(items[i].id)&&(videoCount<=3?rank>3:placed.some((tile,index)=>videos.has(tile.id)&&Math.floor(index*videoCount/items.length)===Math.floor(rank*videoCount/items.length))))continue;
    for(const [w,h]of items[i].shapes){
     if(x+w>columns||y+h>rows)continue;
     let mask=0n;for(let dy=0;dy<h;dy++)for(let dx=0;dx<w;dx++)mask|=1n<<BigInt((y+dy)*columns+x+dx);
     if(occupied&mask)continue;
     const shape=items[i].extra||items[i].id===featureId?-1:w===1&&h===2?0:w===2&&h===1?1:-1;
     if(shape!==-1&&shapeCounts[shape]>=limits[shape])continue;
     if(shape>=0)shapeCounts[shape]++;
     placed.push({id:items[i].id,x,y,w,h,extra:items[i].extra});
     if(search(occupied|mask,remaining^bit))return true;
     placed.pop();
     if(shape>=0)shapeCounts[shape]--;
    }
   }
   memo.add(key);return false;
  };
  if(search(0n,allItems))return {columns,rows,tiles:result!,mode};
 }
 return null;
}

/** Select a dense desktop pool; compact rails always use the complete source pool below. */
export function planReviewBatches(reviewIds:readonly string[],extraIds:readonly string[],columns:number,seed:number,rules:ReviewRules={}){
 columns=Math.max(2,Math.min(4,Math.floor(columns)));
 const random=reviewRandom(seed),videos=new Set(rules.videoIds),videoIds=reviewIds.filter(id=>videos.has(id)),others=reviewIds.filter(id=>!videos.has(id));
 const count=Math.min(reviewIds.length,columns===4?7:columns===3?6:6+Math.floor(random()*3)),initialCount=columns===3?3:4;
 if(!reviewIds.length)return {columns,rows:0,initialRows:0,initialIds:[] as string[],tiles:[] as ReviewTile[]};
 for(let attempt=0;attempt<64;attempt++){
  const selected=[...shuffleReviews(videoIds,random),...shuffleReviews(others,random).slice(0,count-videoIds.length)],initialIds=selected.slice(0,initialCount),remaining=selected.slice(initialCount);
  const first=planReviews(initialIds,[],columns,seed+attempt,{...rules,allowFeature:false});
  if(!first)continue;
  const formatLimit=Math.floor(count*2/3),formatCounts=[first.tiles.filter(t=>t.w===1&&t.h===2).length,first.tiles.filter(t=>t.w===2&&t.h===1).length];
  const formatLimits:readonly [number,number]=[formatLimit-formatCounts[0],formatLimit-formatCounts[1]];
  const rest=planReviews(remaining,extraIds,columns,seed+attempt+64,{...rules,allowFeature:columns===4,formatLimits});
  if(!rest)continue;
  const groups=[...first.tiles,...rest.tiles.map(tile=>({...tile,y:tile.y+first.rows}))],fixed=new Map(first.tiles.map(tile=>[tile.id,tile.tone]));
  const tiles=colorReviews(groups,seed^0xB47C,fixed);
  if(tiles)return {columns,rows:first.rows+rest.rows,initialRows:first.rows,initialIds,tiles};
 }
 throw new Error('Cannot form complete review groups from the available pool');
}

export function planReviewCarousel(reviewIds:readonly string[],seed:number,rules:ReviewRules={}){
 const random=reviewRandom(seed),videos=new Set(rules.videoIds),ids=shuffleReviews(reviewIds,random);
 const ordered=[...ids.filter(id=>videos.has(id)),...ids.filter(id=>!videos.has(id))];
 return colorReviews(ordered.map((id,x)=>({id,x,y:0,w:1,h:1,extra:false})),seed^0xC010)!;
}
