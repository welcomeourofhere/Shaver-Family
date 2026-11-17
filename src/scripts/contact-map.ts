import {numberToken,openDialog,closeDialog} from './motion';
import {setLoading} from './loading';
import {requestFeedback} from './feedback';

// Wheel stays with the page; touch exploration uses the same map in a closeable dialog.
for(const frame of document.querySelectorAll<HTMLIFrameElement>('iframe[data-map-src]')){
 const host=frame.parentElement!,fallback=host.querySelector<HTMLElement>('.contact-map-fallback');
 const slot=host.parentElement!,credit=host.querySelector<HTMLAnchorElement>('.contact-map-credit')!;
 const dialog=document.querySelector<HTMLDialogElement>('#contacts-map-dialog'),expanded=dialog?.querySelector<HTMLElement>('[data-map-expanded-content]');
 const compact=matchMedia('(max-width:960px)');
 const delay=numberToken('--map-idle-delay'),timeout=numberToken('--loading-timeout');
 let near=false,started=false,restoreAtMap=false,timer=0,loadTimer=0,firstFrame=0,secondFrame=0;
 const finish=(state:'ready'|'error')=>{
  clearTimeout(loadTimer);cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  host.dataset.mapState=state;setLoading(host,false);
  if(fallback)fallback.hidden=state!=='error';
  syncMode();
 };
 function syncMode(){
  const enlarged=!!dialog?.open,preview=compact.matches&&!enlarged,interactive=!preview&&host.dataset.mapState==='ready';
  host.dataset.mapMode=enlarged?'expanded':preview?'preview':'inline';
  frame.setAttribute('aria-hidden',String(!interactive));frame.tabIndex=interactive?0:-1;
  if(preview&&dialog&&typeof dialog.showModal==='function'){credit.setAttribute('aria-haspopup','dialog');credit.setAttribute('aria-controls',dialog.id);}
  else{credit.removeAttribute('aria-haspopup');credit.removeAttribute('aria-controls');}
  if(preview&&document.activeElement===frame)credit.focus({preventScroll:true});
 }
 const beginLoading=()=>{clearTimeout(loadTimer);host.dataset.mapState='loading';setLoading(host,true);loadTimer=window.setTimeout(()=>finish('error'),timeout);syncMode();};
 const loaded=()=>{
  if(!started||!frame.getAttribute('src'))return;
  cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  firstFrame=requestAnimationFrame(()=>{secondFrame=requestAnimationFrame(()=>finish(navigator.onLine?'ready':'error'));});
 };
 const failed=()=>{if(started)finish('error');};
 const stopWatching=()=>{clearTimeout(timer);observer?.disconnect();removeEventListener('scroll',schedule);document.removeEventListener('visibilitychange',schedule);};
 const start=()=>{
  if(started||!near||document.hidden)return;
  started=true;beginLoading();
  frame.src=frame.dataset.mapSrc!;stopWatching();
 };
 const schedule=()=>{clearTimeout(timer);if(near&&!started&&!document.hidden)timer=window.setTimeout(start,delay);};
 const observer='IntersectionObserver'in window?new IntersectionObserver(([entry])=>{near=entry.isIntersecting;schedule();}):null;
 const moveMap=(parent:HTMLElement)=>{
  if(host.parentElement===parent)return;
  const target=parent as HTMLElement&{moveBefore?:(node:Node,child:Node|null)=>void};
  if(typeof target.moveBefore==='function')target.moveBefore(host,null);
  else{if(started)beginLoading();parent.append(host);}
 };
 const openMap=(event:MouseEvent)=>{
  const target=event.target instanceof Element?event.target:null;
  if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||!compact.matches||!dialog||!expanded||dialog.open||typeof dialog.showModal!=='function'||target?.closest('.contact-map-fallback'))return;
  event.preventDefault();moveMap(expanded);near=true;start();openDialog(dialog);syncMode();requestFeedback('open',event);
 };
 const restoreMap=()=>{moveMap(slot);syncMode();credit.focus({preventScroll:true});if(restoreAtMap)credit.scrollIntoView({block:'nearest',behavior:'instant'});restoreAtMap=false;};
 const resizeMode=()=>{if(!compact.matches&&dialog?.open){restoreAtMap=true;void closeDialog(dialog,true);}syncMode();};
 const cleanup=()=>{
  stopWatching();clearTimeout(loadTimer);cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);
  frame.removeEventListener('load',loaded);frame.removeEventListener('error',failed);removeEventListener('offline',failed);
  host.removeEventListener('click',openMap);dialog?.removeEventListener('close',restoreMap);compact.removeEventListener('change',resizeMode);
  if(dialog?.open)void closeDialog(dialog,true);
  frame.removeAttribute('src');if(host.parentElement!==slot)slot.append(host);
  setLoading(host,false);
 };
 frame.addEventListener('load',loaded);frame.addEventListener('error',failed);addEventListener('offline',failed);
 host.addEventListener('click',openMap);dialog?.addEventListener('close',restoreMap);compact.addEventListener('change',resizeMode);syncMode();
 addEventListener('scroll',schedule,{passive:true});document.addEventListener('visibilitychange',schedule);
 if(observer)observer.observe(host);else{near=true;schedule();}
 document.addEventListener('astro:before-swap',cleanup,{once:true});
}
