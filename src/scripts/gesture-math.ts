// Match Shaver Family's deliberate travel and restrained velocity projection.
export function projectedSwipeDistance(distance:number,velocity:number,width:number) {
  return distance+(Math.sign(velocity)===Math.sign(distance)?Math.max(-width*.35,Math.min(width*.35,velocity*90)):0);
}
export function swipeDirection(distance:number,velocity:number,width:number,cancelled=false) {
  if(cancelled)return 0;
  const projected=projectedSwipeDistance(distance,velocity,width);
  return Math.abs(distance)>=Math.min(40,width*.18)||Math.abs(distance)>=12&&Math.abs(projected)>=width*.18 ? (distance<0?1:-1) : 0;
}
export function nearestRailStop(stops:number[],position:number,velocity=0) {
  const projected=position+Math.max(-120,Math.min(120,velocity*90));
  return stops.reduce((best,stop)=>Math.abs(stop-projected)<Math.abs(best-projected)?stop:best,stops[0]??0);
}
