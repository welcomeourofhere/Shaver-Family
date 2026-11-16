import {springProgress,spring} from '../config/spring.ts';
export function wrapOfferPhase(phase: number, count: number): number {
  return ((phase % count) + count) % count;
}

export function offerSlot(index:number,selected:number,count:number,stride:number,width:number){
  const offset=wrapOfferPhase(index-selected,count),x=offset*stride;
  return {offset,x,visible:x<width-1};
}

// Translation/opacity settle monotonically; only material depth carries the elastic response.
export function offerDealFrame(from:{x:number;y:number;scale:number;opacity:number},to:typeof from,progress:number,arrival:number,controlled=false){
  const travel=controlled?progress:springProgress(progress,spring.drawerDamping),elastic=controlled?progress:springProgress(progress);
  return {x:from.x+(to.x-from.x)*travel,y:from.y+(to.y-from.y)*travel,opacity:from.opacity+(to.opacity-from.opacity)*travel,
    scale:from.scale+(to.scale-from.scale)*elastic+arrival*(elastic-travel)};
}

