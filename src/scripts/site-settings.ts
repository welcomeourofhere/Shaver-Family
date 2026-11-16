import {pageScrollY} from './modal-scroll-lock.ts';
import {floatingTone,floatingTones,type FloatingTone} from './floating-tone';
import {requestFeedback} from './feedback';
import {numberToken} from './design-tokens';
const trigger=document.querySelector<HTMLButtonElement>('[data-site-settings]');
const panel=document.querySelector<HTMLElement>('#site-settings-panel');
if(trigger&&panel){
 const close=(restore=false)=>{panel.hidden=true;trigger.setAttribute('aria-expanded','false');if(restore)trigger.focus({preventScroll:true});};
 trigger.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;trigger.setAttribute('aria-expanded',String(open));});
 document.addEventListener('pointerdown',event=>{if(event.target instanceof Node&&!trigger.parentElement!.contains(event.target))close();},{passive:true});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden){event.preventDefault();close(true);requestFeedback('close',event);}});
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

const floating=[trigger,backTop].filter((button):button is HTMLButtonElement=>!!button);
if(floating.length){
 const compact=matchMedia('(max-width:960px)'),sections=[...document.querySelectorAll('main>section,footer')];
 const rgb=(color:string)=>color.startsWith('#')?color.slice(1).match(/../g)!.map(value=>parseInt(value,16)):color.match(/[\d.]+/g)?.slice(0,3).map(Number);
 const palette=floatingTones.map(tone=>({tone,color:rgb(getComputedStyle(document.documentElement).getPropertyValue(`--${tone}`).trim())!}));
 const ratio=numberToken('--golden-ratio'),cadence=numberToken('--motion-ui')/2;
 let frame=0,timer=0,lastPaint=-Infinity,section=0;
 function behind(button:HTMLElement):FloatingTone|undefined{
  const bounds=button.getBoundingClientRect();
  for(const element of document.elementsFromPoint(bounds.left+bounds.width/2,bounds.top+bounds.height/2)){
   if(element.closest('.site-settings,.back-to-top'))continue;
   const tone=(element.closest<HTMLElement>('[data-selection-surface]')?.dataset.selectionSurface);
   if(floatingTones.includes(tone as FloatingTone))return tone as FloatingTone;
   const color=getComputedStyle(element).backgroundColor;
   if(color==='transparent'||color==='rgba(0, 0, 0, 0)')continue;
   const channels=rgb(color);if(!channels)return;
   return palette.find(entry=>entry.color.every((value,index)=>Math.abs(value-channels[index])<24))?.tone;
  }
 }
 function paint(){
  frame=0;lastPaint=performance.now();if(compact.matches||document.hidden||document.querySelector('dialog[open]'))return;
  const target=document.elementsFromPoint(innerWidth/2,innerHeight/ratio).map(element=>element.closest('main>section,footer')).find(Boolean);
  if(target&&sections.includes(target))section=sections.indexOf(target);
  // Read both hit tests before changing either surface; scroll must not force a second layout.
  const updates=floating.flatMap((button,index)=>button.hidden?[]:[{button,surface:behind(button),index}]);
  for(const {button,surface,index}of updates){
   const tone=floatingTone(section,index===0?2:1,surface);
   if(button.dataset.floatingTone!==tone)button.dataset.floatingTone=tone;
   if(surface!==button.dataset.selectionSurface){if(surface)button.dataset.selectionSurface=surface;else delete button.dataset.selectionSurface;}
  }
 }
 const schedule=()=>{
  if(frame||timer||compact.matches||document.hidden)return;
  const delay=cadence-(performance.now()-lastPaint);
  if(delay<=0)frame=requestAnimationFrame(paint);
  else timer=window.setTimeout(()=>{timer=0;frame=requestAnimationFrame(paint)},delay);
 };
 addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);
 new MutationObserver(schedule).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
 compact.addEventListener('change',schedule);paint();
}
