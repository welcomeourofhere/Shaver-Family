import design from '../config/design.json' with {type:'json'};
export function newsActionTone(index:number,count:number){
  const tones=design.newsActionTones;
  const tone=tones[index%tones.length];
  return count>1&&index===count-1&&tone===tones[0]?tones[1]:tone;
}
