import {boundedSpringProgress,spring} from '../config/spring.ts';

// Native details/name remains the only owner of the selected service.
export function animateServiceDisclosure(row:HTMLDetailsElement,reduced:boolean,duration:number){
 if(reduced||!row.open)return;
 const body=row.querySelector<HTMLElement>('.sd-description')!;
 row.dataset.serviceOpening='true';
 const frames=Array.from({length:spring.samples+1},(_,i)=>{const p=boundedSpringProgress(i/spring.samples);return{opacity:p,clipPath:`inset(0 0 ${(1-p)*100}% 0)`};});
 const reveal=body.animate(frames,{duration,easing:'linear'});
 const stop=()=>{reveal.cancel();delete row.dataset.serviceOpening;};
 void reveal.finished.then(stop,()=>{});
 return stop;
}
