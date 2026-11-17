import {enableHorizontalSwipe} from './horizontal-swipe';
import {projectedSwipeDistance} from './gesture-math';
import {workOffset,workIndex,workOrder,workDepth,workDragTravel} from './works-layout';
import {stepSpring} from '../config/spring';
import {reducedMotion,instantInteraction,isKeyboardActivation,numberToken} from './motion';
import {requestFeedback,beginSlideFeedback,type SlideFeedback} from './feedback';

const root=document.querySelector<HTMLElement>('[data-works]');
if(root){
 const controller=new AbortController(),{signal}=controller;
 const layoutStyle=root.style;
 const fan=root.querySelector<HTMLElement>('.works-fan')!,cards=[...fan.querySelectorAll<HTMLButtonElement>('[data-work-card]')];
 const sequence=workOrder(cards.length).map(index=>cards[index]);let order=sequence,slots=new Map(order.map((card,index)=>[card,index]));
 const controls=root.querySelector<HTMLElement>('[data-work-controls]')!,count=controls.querySelector<HTMLOutputElement>('[data-work-count]')!,steps=[...controls.querySelectorAll<HTMLButtonElement>('[data-work-step]')];
 const author=root.querySelector<HTMLElement>('[data-work-author]')!,caption=root.querySelector<HTMLElement>('.works-caption [data-work-caption]')!,empty=root.querySelector<HTMLElement>('[data-work-empty]')!;
 const tabs=[...root.querySelectorAll<HTMLButtonElement>('[data-work-master-tab]')];let master='all';
 let neighborLimit=Number.parseInt(getComputedStyle(root).getPropertyValue('--works-neighbor-limit'))||1;
 let current=-1,position=0,target=0,velocity=0,onScreen=false,frame=0,lastFrame=0,dragFrame=0;
  let dragStart=0,dragStep=1,dragDistance=0,cancelSwipe=()=>{};
  let slideGesture:SlideFeedback|null=null;
  const finishGesture=(cancelled=false)=>{if(cancelled)slideGesture?.cancel();else slideGesture?.finish();slideGesture=null;};
 const depth=()=>workDepth(order.length,neighborLimit);
 function stop(){cancelAnimationFrame(frame);cancelAnimationFrame(dragFrame);frame=dragFrame=0;lastFrame=0;fan.dataset.workMoving='false';}
 function render(){
  const index=order.length?workIndex(position,order.length):-1,edge=depth(),fadeEnd=Math.min(edge+.5,Math.max(.5,order.length/2));
  fan.dataset.workPosition=String(position);fan.dataset.workTarget=String(target);fan.dataset.workIndex=String(index);
  for(const card of cards){
   const slot=slots.get(card);
   if(slot===undefined){card.hidden=true;card.inert=true;card.setAttribute('aria-hidden','true');card.dataset.workCurrent='false';card.tabIndex=-1;continue;}
   const offset=workOffset(slot,position,order.length),distance=Math.abs(offset),visible=distance<fadeEnd;
   card.hidden=!visible;card.dataset.workSlot=String(slot);card.style.setProperty('--work-offset',String(offset));card.style.setProperty('--work-distance',String(distance));card.style.zIndex=String(100-Math.round(distance*10));
   card.dataset.workDistance=String(distance);card.dataset.workVisible=String(visible);card.inert=!visible;card.setAttribute('aria-hidden',String(!visible));
  }
   slideGesture?.cross(index);
   if(current===index)return;
  current=index;
  for(const card of cards){const selected=card===order[current];card.dataset.workCurrent=String(selected);card.tabIndex=selected?0:-1;card.setAttribute('aria-current',String(selected));}
  author.textContent=order[current]?.dataset.workMaster??'';caption.textContent=order[current]?.dataset.workCaption??'';
  count.textContent=`${current+1} / ${order.length}`;count.setAttribute('aria-label',`${current+1} из ${order.length}`);
 }
 function tick(now:number){
  const state=stepSpring(position,velocity,target,lastFrame?(now-lastFrame)/1000:1/60);lastFrame=now;position=state.value;velocity=state.velocity;render();
   if(position===target&&velocity===0){frame=0;lastFrame=0;fan.dataset.workMoving='false';finishGesture();return;}
  frame=requestAnimationFrame(tick);
 }
 function settle(next:number,event?:Event){
  target=next;cancelAnimationFrame(dragFrame);dragFrame=0;
   if(instantInteraction()||event&&isKeyboardActivation(event)||!onScreen||document.hidden){stop();position=target;velocity=0;render();finishGesture();return;}
  fan.dataset.workMoving='true';if(!frame){lastFrame=0;frame=requestAnimationFrame(tick);}
 }
 function select(next:number,event:Event){
  if(!order.length||next===target)return;settle(next,event);requestFeedback('select',event);
  if(isKeyboardActivation(event))order[current].focus({preventScroll:true});
 }
 function applyMaster(){
   const selected=order[current];finishGesture(true);cancelSwipe();stop();
  order=sequence.filter(card=>master==='all'||card.dataset.workMasterId===master);
  slots=new Map(order.map((card,index)=>[card,index]));position=target=Math.max(0,order.indexOf(selected));velocity=0;current=-2;
  layoutStyle.setProperty('--works-total',String(order.length));layoutStyle.setProperty('--works-available-depth',String(workDepth(order.length,4)));
  empty.hidden=order.length>0;steps.forEach(button=>button.disabled=order.length<2);render();
 }
 function chooseMaster(tab:HTMLButtonElement,event:Event){
  if(master===tab.dataset.workMasterTab)return;
  master=tab.dataset.workMasterTab!;applyMaster();fan.setAttribute('aria-labelledby',tab.id);
  tabs.forEach(button=>{const selected=button===tab;button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;});requestFeedback('select',event);
 }
 fan.addEventListener('click',event=>{
  const card=event.target instanceof Element?event.target.closest<HTMLButtonElement>('[data-work-card]'):null;
  if(!card||event.defaultPrevented)return;
  const slot=slots.get(card);if(slot===undefined||slot===current)return;event.preventDefault();select(Math.round(position+workOffset(slot,position,order.length)),event);
 },{signal});
 controls.addEventListener('click',event=>{
  const button=event.target instanceof Element?event.target.closest<HTMLButtonElement>('[data-work-step]'):null;
  if(button&&!button.disabled){event.preventDefault();select((isKeyboardActivation(event)?Math.round(position):target)+Number(button.dataset.workStep),event);}
 },{signal});
 fan.addEventListener('keydown',event=>{
  if(!order.length||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)||event.altKey||event.ctrlKey||event.metaKey)return;
  event.preventDefault();select(event.key==='Home'?0:event.key==='End'?order.length-1:Math.round(position)+(event.key==='ArrowRight'?1:-1),event);
 },{signal});
 tabs.forEach((tab,index)=>{
  tab.addEventListener('click',event=>{event.preventDefault();chooseMaster(tab,event);},{signal});
  tab.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;chooseMaster(tabs[next],event);tabs[next].focus({preventScroll:true});},{signal});
 });
 root.querySelector<HTMLButtonElement>('[data-work-reset]')!.addEventListener('click',event=>{event.preventDefault();chooseMaster(tabs[0],event);},{signal});
  function renderDrag(){dragFrame=0;position=dragStart-dragDistance/dragStep;target=Math.round(position);velocity=0;render();}
 cancelSwipe=enableHorizontalSwipe(fan,()=>{}, {signal,enabled:()=>order.length>1,motion:{
   start(event){finishGesture(true);stop();dragStart=position;slideGesture=beginSlideFeedback(current,event);const a=workOffset(current,position,order.length),next=(current+(a>0?-1:1)+order.length)%order.length,b=workOffset(next,position,order.length),width=order[current].offsetWidth,spacing=depth()?Math.abs((new DOMMatrix(getComputedStyle(order[next]).transform).m41-new DOMMatrix(getComputedStyle(order[current]).transform).m41)/(b-a)):width;dragStep=workDragTravel(width,spacing,event.pointerType==='touch',numberToken('--size-84'));},
  move(dx){dragDistance=dx;if(!dragFrame)dragFrame=requestAnimationFrame(renderDrag);},
   release(dx,speed,event){cancelAnimationFrame(dragFrame);dragDistance=dx;renderDrag();velocity=-speed*1000/dragStep;settle(Math.round(dragStart-projectedSwipeDistance(dx,speed,dragStep)/dragStep),event);},
   cancel(event){finishGesture(true);cancelAnimationFrame(dragFrame);dragFrame=0;velocity=0;settle(Math.round(position),event);},
 }});
  function reset(){neighborLimit=Number.parseInt(getComputedStyle(root!).getPropertyValue('--works-neighbor-limit'))||1;finishGesture(true);cancelSwipe();stop();target=position=Math.round(position);velocity=0;render();}
 const visibility=new IntersectionObserver(([entry])=>{onScreen=entry.isIntersecting;if(!onScreen)reset();});visibility.observe(root);
 reducedMotion.addEventListener('change',reset,{signal});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();},{signal});addEventListener('resize',reset,{signal});
 document.addEventListener('astro:before-swap',()=>{controller.abort();visibility.disconnect();stop();},{once:true,signal});
 render();
}
