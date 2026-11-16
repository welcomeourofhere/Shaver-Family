import {numberToken,instantInteraction,textToken} from './motion';
import {isMousePointer} from './interaction-intent';
import {popover,closePopoversWithin} from './popover';

let active:HTMLElement|null=null;
let lastOpenedAt=-Infinity;
for(const root of document.querySelectorAll<HTMLElement>('[data-info-tip]')){
  const button=root.querySelector<HTMLButtonElement>('button')!,panel=root.querySelector<HTMLElement>('[popover]')!;
  const popup=popover(panel,button);
  let pinned=false,dismissed=false;
  let animation:Animation|undefined;
  let hoverTimer:ReturnType<typeof setTimeout>|undefined,closeTimer:ReturnType<typeof setTimeout>|undefined;
  const open=(instant=false)=>{
    clearTimeout(closeTimer);
    clearTimeout(hoverTimer);hoverTimer=undefined;
    if(popup.isOpen())return;
    if(active&&active!==root)closePopoversWithin(active);
    popup.open();
    active=root;lastOpenedAt=performance.now();button.setAttribute('aria-expanded','true');
    const edge=numberToken('--size-16'),gap=numberToken('--size-8'),r=button.getBoundingClientRect();
    panel.style.maxHeight=`${innerHeight-edge*2}px`;
    const w=panel.offsetWidth,h=panel.offsetHeight;
    panel.style.left=`${Math.max(edge,Math.min(innerWidth-w-edge,r.left+r.width/2-w/2))}px`;
    panel.style.top=`${Math.max(edge,Math.min(innerHeight-h-edge,r.bottom+gap+h>innerHeight-edge?r.top-h-gap:r.bottom+gap))}px`;
    panel.tabIndex=panel.scrollHeight>panel.clientHeight?0:-1;
    animation?.cancel();animation=undefined;
    if(!instant&&!instantInteraction())animation=panel.animate([{opacity:0,transform:`translateY(${textToken('--size-4')})`},{opacity:1,transform:'translateY(0)'}],{duration:numberToken('--motion-popover'),easing:textToken('--ease-out')});
  };
  const close=()=>{clearTimeout(hoverTimer);clearTimeout(closeTimer);hoverTimer=undefined;pinned=false;animation?.cancel();animation=undefined;if(popup.isOpen()){popup.close();lastOpenedAt=performance.now();}button.setAttribute('aria-expanded','false');if(active===root)active=null;};
  const leave=(event:PointerEvent)=>{
    if(!isMousePointer(event)||pinned||button.matches(':focus-visible'))return;
    if(event.relatedTarget instanceof Node&&(root.contains(event.relatedTarget)||panel.contains(event.relatedTarget)))return;
    clearTimeout(hoverTimer);hoverTimer=undefined;clearTimeout(closeTimer);
    closeTimer=setTimeout(close,numberToken('--motion-ui'));
  };
  button.addEventListener('click',()=>{if(popup.isOpen()&&pinned){dismissed=true;close();}else{dismissed=false;open();pinned=true;}});
  button.addEventListener('focus',()=>{if(button.matches(':focus-visible')){if(!popup.isOpen())dismissed=false;open();}});
  button.addEventListener('blur',event=>{if(!(event.relatedTarget instanceof Node&&panel.contains(event.relatedTarget)))close()});
  button.addEventListener('keydown',event=>{if(event.key==='ArrowDown'&&popup.isOpen()&&panel.tabIndex===0){event.preventDefault();panel.focus()}});
  panel.addEventListener('focusout',event=>{if(!(event.relatedTarget instanceof Node&&(root.contains(event.relatedTarget)||panel.contains(event.relatedTarget))))close()});
  panel.addEventListener('keydown',event=>{if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','PageUp','PageDown','Home','End',' '].includes(event.key))event.stopPropagation()});
  // Selecting tooltip text must not start the carousel gesture underneath it.
  panel.addEventListener('pointerdown',event=>event.stopPropagation());
  root.addEventListener('pointerenter',event=>{clearTimeout(closeTimer);if(!dismissed&&isMousePointer(event)&&matchMedia('(hover:hover)').matches){if(active||performance.now()-lastOpenedAt<numberToken('--tooltip-warm-window'))open(true);else{const delay=Number(root.dataset.infoDelay??numberToken('--tooltip-delay'));if(delay===0)open();else hoverTimer=setTimeout(()=>open(),delay);}}});
  root.addEventListener('pointerleave',leave);
  panel.addEventListener('pointerenter',()=>clearTimeout(closeTimer));
  panel.addEventListener('pointerleave',leave);
  panel.addEventListener('toggle',()=>{if(!popup.isOpen()){pinned=false;button.setAttribute('aria-expanded','false');if(active===root)active=null;}});
  document.addEventListener('pointerdown',event=>{if(active===root&&event.target instanceof Node&&!root.contains(event.target)&&!panel.contains(event.target))close()},{passive:true});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&active===root){event.preventDefault();event.stopPropagation();dismissed=true;button.focus({preventScroll:true});close()}});
  document.addEventListener('pointermove',event=>{if(dismissed&&event.target instanceof Node&&!root.contains(event.target)&&!panel.contains(event.target))dismissed=false;},{passive:true});
  addEventListener('scroll',event=>{if(event.target instanceof Node&&panel.contains(event.target))return;if(active===root||hoverTimer)close()},{capture:true,passive:true});
  addEventListener('resize',close);
}
