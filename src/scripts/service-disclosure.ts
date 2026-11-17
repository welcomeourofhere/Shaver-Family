import {boundedSpringProgress,spring} from '../config/spring.ts';

// Native details/name remains the only owner of the selected service.
export function animateServiceDisclosure(row:HTMLDetailsElement,reduced:boolean,duration:number){
 if(reduced||!row.open)return;
 const summary=row.querySelector('summary')!,body=row.querySelector<HTMLElement>('.sd-description')!;
 const from=parseFloat(getComputedStyle(summary).height),to=parseFloat(getComputedStyle(row).height);
 if(to<=from+1)return;
 row.dataset.serviceOpening='true';
 const frames=Array.from({length:spring.samples+1},(_,i)=>({height:`${from+(to-from)*boundedSpringProgress(i/spring.samples)}px`}));
 const size=row.animate(frames,{duration,easing:'linear'});
 const reveal=body.animate(Array.from({length:spring.samples+1},(_,i)=>({opacity:boundedSpringProgress(i/spring.samples)})),{duration,easing:'linear'});
 const stop=()=>{size.cancel();reveal.cancel();delete row.dataset.serviceOpening;};
 void size.finished.then(stop,()=>{});
 return stop;
}
