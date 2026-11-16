export function certificateWaveLevels(count:number,selected:number|null){
  return Array.from({length:count},(_,index)=>selected===null?index:Math.abs(index-selected));
}
