import {pageScrollY} from './modal-scroll-lock.ts';
const trigger=document.querySelector<HTMLButtonElement>('[data-site-settings]');
const panel=document.querySelector<HTMLElement>('#site-settings-panel');
if(trigger&&panel){
 const close=(restore=false)=>{panel.hidden=true;trigger.setAttribute('aria-expanded','false');if(restore)trigger.focus({preventScroll:true});};
 trigger.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;trigger.setAttribute('aria-expanded',String(open));});
 document.addEventListener('pointerdown',event=>{if(event.target instanceof Node&&!trigger.parentElement!.contains(event.target))close();},{passive:true});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden){event.preventDefault();close(true);}});
 panel.addEventListener('click',event=>{if((event.target as Element).closest('[data-analytics-settings]'))close();});
}
const backTop=document.querySelector<HTMLButtonElement>('[data-back-to-top]');
if(backTop){
 let frame=0;
 const update=()=>{frame=0;backTop.hidden=pageScrollY()<innerHeight*.7;};
 addEventListener('scroll',()=>{if(!frame)frame=requestAnimationFrame(update);},{passive:true});
 backTop.addEventListener('click',()=>{document.querySelector<HTMLElement>('#top,h1')?.focus({preventScroll:true});scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});});
 update();
}
