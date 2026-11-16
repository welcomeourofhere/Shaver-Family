import {numberToken} from './design-tokens';

// Native iframe lazy-loading starts several screens early, during the approach scroll.
for(const frame of document.querySelectorAll<HTMLIFrameElement>('iframe[data-map-src]')){
 const host=frame.parentElement!,delay=numberToken('--map-idle-delay');
 let near=false,started=false,timer=0;
 const start=()=>{if(started||!near||document.hidden)return;started=true;frame.src=frame.dataset.mapSrc!;frame.removeAttribute('aria-hidden');frame.removeAttribute('tabindex');cleanup();};
 const schedule=()=>{clearTimeout(timer);if(near&&!started&&!document.hidden)timer=window.setTimeout(start,delay);};
 const observer=new IntersectionObserver(([entry])=>{near=entry.isIntersecting;schedule();});
 const cleanup=()=>{clearTimeout(timer);observer.disconnect();removeEventListener('scroll',schedule);document.removeEventListener('visibilitychange',schedule);frame.removeEventListener('focus',start);};
 observer.observe(host);addEventListener('scroll',schedule,{passive:true});document.addEventListener('visibilitychange',schedule);frame.addEventListener('focus',start);
 document.addEventListener('astro:before-swap',cleanup,{once:true});
}
