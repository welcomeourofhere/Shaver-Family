import {numberToken,instantInteraction,textToken} from './motion';
import {requestFeedback} from './feedback';
import {popover} from './popover';

for(const root of document.querySelectorAll<HTMLElement>('[data-choice]')) {
  const native=root.querySelector<HTMLSelectElement>('select')!,trigger=root.querySelector<HTMLButtonElement>('.choice-trigger')!,list=root.querySelector<HTMLElement>('[role="listbox"]')!;
  const options=[...list.querySelectorAll<HTMLButtonElement>('[role="option"]')],label=trigger.querySelector<HTMLElement>('[data-choice-label]')!;
  let active=0,frame=0,typed='',typedAt=0,openOnPointerDown=false;
  const popup=popover(list,trigger),isOpen=popup.isOpen;
  function highlight(index:number){active=(index+options.length)%options.length;options.forEach((option,i)=>option.dataset.active=String(i===active));trigger.setAttribute('aria-activedescendant',options[active].id);options[active].scrollIntoView({block:'nearest'});}
  function sync(){
    const index=options.findIndex(option=>option.dataset.value===native.value);active=Math.max(0,index);
    label.textContent=options[active].querySelector('span')!.textContent;
    options.forEach((option,i)=>option.setAttribute('aria-selected',String(i===active)));
    if(isOpen())highlight(active);
  }
  function position(){
    frame=0;if(!isOpen())return;
    if(!trigger.getClientRects().length||trigger.closest('dialog:not([open])')){popup.close();return;}
    const r=trigger.getBoundingClientRect(),gap=numberToken('--size-8'),edge=numberToken('--size-16');
    list.style.width=`${Math.min(innerWidth-edge*2,Math.max(r.width,numberToken('--size-200')))}px`;
    const height=Math.min(list.scrollHeight,innerHeight-edge*2),above=innerHeight-r.bottom<height+gap&&r.top>height+gap;
    list.style.left=`${Math.max(edge,Math.min(innerWidth-list.offsetWidth-edge,r.left))}px`;
    list.style.top=`${Math.max(edge,Math.min(innerHeight-height-edge,above?r.top-height-gap:r.bottom+gap))}px`;
  }
  const schedule=()=>{if(isOpen()&&!frame)frame=requestAnimationFrame(position)};
  function open(){trigger.focus({preventScroll:true});popup.open();position();highlight(active);}
  function choose(index:number){native.value=options[index].dataset.value!;native.dispatchEvent(new Event('change',{bubbles:true}));sync();popup.close();trigger.focus({preventScroll:true});}
  trigger.addEventListener('pointerdown',()=>{openOnPointerDown=isOpen();});
  trigger.addEventListener('click',event=>{if(event.detail&&openOnPointerDown){if(isOpen())popup.close();return;}isOpen()?popup.close():open();});
  trigger.addEventListener('keydown',event=>{
    if(event.key==='Tab'){if(isOpen())popup.close();return;}
    if(event.key==='Escape'&&isOpen()){event.preventDefault();event.stopPropagation();popup.close();requestFeedback('close',event);return;}
    if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
      event.preventDefault();if(!isOpen()){open();requestFeedback('open',event);}
      highlight(event.key==='Home'?0:event.key==='End'?options.length-1:active+(event.key==='ArrowDown'?1:-1));return;
    }
    if((event.key==='Enter'||event.key===' ')&&isOpen()){event.preventDefault();choose(active);requestFeedback('select',event);return;}
    if(event.key.length===1&&!event.ctrlKey&&!event.altKey&&!event.metaKey){
      event.preventDefault();const now=performance.now();typed=now-typedAt>700?event.key:typed+event.key;typedAt=now;
      const index=options.findIndex(option=>option.textContent!.trim().toLocaleLowerCase('ru').startsWith(typed.toLocaleLowerCase('ru')));
      if(index>=0){if(!isOpen())open();highlight(index);}
    }
  });
  options.forEach((option,index)=>option.addEventListener('click',()=>choose(index)));
  list.addEventListener('toggle',()=>{
    const opened=isOpen();trigger.setAttribute('aria-expanded',String(opened));
    if(!opened){trigger.removeAttribute('aria-activedescendant');return;}
    position();if(!instantInteraction())list.animate([{opacity:0,transform:`translateY(${textToken('--size-6')})`},{opacity:1,transform:'none'}],{duration:numberToken('--motion-popover'),easing:textToken('--ease-out')});
  });
  native.addEventListener('change',sync);native.addEventListener('choice:sync',sync);
  addEventListener('scroll',schedule,{capture:true,passive:true});addEventListener('resize',schedule);window.visualViewport?.addEventListener('resize',schedule);
  native.parentElement!.hidden=true;trigger.hidden=false;sync();
}
