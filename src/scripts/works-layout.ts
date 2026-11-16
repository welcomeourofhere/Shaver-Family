/** Nearest cyclic position; one item remains central through every full turn. */
export function workOffset(index:number,selected:number,count:number){
 const half=count/2;
 return ((index-selected+half)%count+count)%count-half;
}

export const workIndex=(position:number,count:number)=>((Math.round(position)%count)+count)%count;
export const workDepth=(count:number,limit:number)=>Math.max(0,Math.min(limit,Math.floor((count-1)/2)));
export const workDragTravel=(cardWidth:number,spacing:number,touch:boolean,minimumTouchTravel:number)=>touch?Math.max(minimumTouchTravel,cardWidth*.35):Math.max(1,spacing);
export function workTilt(id:string){let hash=0;for(const letter of id)hash=(Math.imul(hash,31)+letter.codePointAt(0)!)>>>0;return [-2,-1,1,2][hash%4];}

/** Preserve the SSR center; shuffle logical slots without moving DOM nodes. */
export function workOrder(count:number,random:()=>number=Math.random){
 const order=Array.from({length:count},(_,index)=>index);
 for(let index=count-1;index>1;index--){const next=1+Math.floor(random()*index);[order[index],order[next]]=[order[next],order[index]];}
 return order;
}
