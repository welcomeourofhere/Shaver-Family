import {updateReadingEdges} from './reading-edges.ts';

const generations=new WeakMap<HTMLElement,number>();
/** Keep the thumb quiet while its reading area changes; follow the real transition. */
export function beginReadingTransition(card:HTMLElement,prose:HTMLElement,settled:()=>void){
 if(matchMedia('(prefers-reduced-motion:reduce)').matches)return;
 const generation=(generations.get(card)??0)+1;generations.set(card,generation);
 prose.dataset.readingTransition='true';
 requestAnimationFrame(()=>requestAnimationFrame(()=>{
  const transitions=card.getAnimations().filter(animation=>(animation as CSSTransition).transitionProperty==='grid-template-rows');
  void Promise.allSettled(transitions.map(animation=>animation.finished)).then(()=>{
   if(generations.get(card)!==generation||!card.isConnected)return;
   delete prose.dataset.readingTransition;updateReadingEdges(prose);settled();
  });
 }));
}
