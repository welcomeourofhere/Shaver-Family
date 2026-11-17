import {numberToken} from './design-tokens';
import {setLoading} from './loading';

// The embedded map is a preview; the address and route open the full provider view.
for(const frame of document.querySelectorAll<HTMLIFrameElement>('iframe[data-map-src]')){
 const host=frame.parentElement!,fallback=host.querySelector<HTMLElement>('.contact-map-fallback');
 const delay=numberToken('--map-idle-delay'),timeout=numberToken('--loading-timeout');
 let near=false,started=false,timer=0,loadTimer=0,firstFrame=0,secondFrame=0;
 const finish=(state:'ready'|'error')=>{
  clearTimeout(loadTimer);cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  host.dataset.mapState=state;setLoading(host,false);
  if(fallback)fallback.hidden=state!=='error';
 };
 const loaded=()=>{
  if(!started||!frame.getAttribute('src'))return;
  cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  firstFrame=requestAnimationFrame(()=>{secondFrame=requestAnimationFrame(()=>finish(navigator.onLine?'ready':'error'));});
 };
 const failed=()=>{if(started)finish('error');};
 const stopWatching=()=>{clearTimeout(timer);observer?.disconnect();removeEventListener('scroll',schedule);document.removeEventListener('visibilitychange',schedule);};
 const start=()=>{
  if(started||!near||document.hidden)return;
  started=true;host.dataset.mapState='loading';setLoading(host,true);
  loadTimer=window.setTimeout(()=>finish('error'),timeout);
  frame.src=frame.dataset.mapSrc!;stopWatching();
 };
 const schedule=()=>{clearTimeout(timer);if(near&&!started&&!document.hidden)timer=window.setTimeout(start,delay);};
 const observer='IntersectionObserver'in window?new IntersectionObserver(([entry])=>{near=entry.isIntersecting;schedule();}):null;
 const cleanup=()=>{
  stopWatching();clearTimeout(loadTimer);cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  frame.removeEventListener('load',loaded);frame.removeEventListener('error',failed);removeEventListener('offline',failed);
  setLoading(host,false);
 };
 frame.addEventListener('load',loaded);frame.addEventListener('error',failed);addEventListener('offline',failed);
 addEventListener('scroll',schedule,{passive:true});document.addEventListener('visibilitychange',schedule);
 if(observer)observer.observe(host);else{near=true;schedule();}
 document.addEventListener('astro:before-swap',cleanup,{once:true});
}
