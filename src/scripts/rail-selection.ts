import {isKeyboardActivation} from './interaction-intent.ts';
import {requestFeedback,beginSlideFeedback,type SlideFeedback} from './feedback.ts';
import {spring,springProgress} from '../config/spring.ts';
import {nearestRailStop} from './gesture-math.ts';
import {numberToken} from './design-tokens.ts';
export function railItems(rail:HTMLElement){return [...rail.children].filter((element):element is HTMLElement=>element instanceof HTMLElement&&!element.hidden&&!element.matches('script,style,template,[data-rail-spacer]'));}
export function visibleRailIndex(bounds:{left:number;right:number}[],left:number,right:number,current=0) {
  if(!bounds.length)return 0;
  let selected=Math.max(0,Math.min(current,bounds.length-1));
  let visible=Math.max(0,Math.min(right,bounds[selected].right)-Math.max(left,bounds[selected].left));
  for(const [index,b] of bounds.entries()) {
    const overlap=Math.max(0,Math.min(right,b.right)-Math.max(left,b.left));
    if(overlap>visible+.5){visible=overlap;selected=index;}
  }
  return selected;
}

// An initial press on a peeking card brings it into view; its controls remain available on the next press.
export function enableRailCardSelection(rail:HTMLElement,selector:string,enabled:()=>boolean,_select:(index:number)=>void,signal?:AbortSignal) {
  let pending:HTMLElement|null=null;
  rail.addEventListener('pointerdown',event=>{
    pending=null;if(!enabled()||!event.isPrimary||event.button!==0)return;
    const card=event.target instanceof Element?event.target.closest<HTMLElement>(selector):null;
    const cards=[...rail.querySelectorAll<HTMLElement>(selector)].filter(item=>!item.hidden),index=card?cards.indexOf(card):-1,r=rail.getBoundingClientRect();
    if(index>=0&&index!==visibleRailIndex(cards.map(item=>item.getBoundingClientRect()),r.left,r.right,Number(rail.dataset.railIndex)||0))pending=card;
  },{capture:true,passive:true,signal});
  rail.addEventListener('pointercancel',()=>{pending=null},{signal});
  rail.addEventListener('click',event=>{
    const card=pending;pending=null;
    if(!card||!enabled()||event.defaultPrevented||!event.detail||!(event.target instanceof Node)||!card.contains(event.target))return;
    event.preventDefault();event.stopImmediatePropagation();
    nativeRail(rail).goTo([...rail.querySelectorAll<HTMLElement>(selector)].filter(item=>!item.hidden).indexOf(card));
    requestFeedback('select',event);
  },{capture:true,signal});
}
export function observeRail(rail:HTMLElement,selector:string,select:(index:number)=>void) {
  const owner=nativeRail(rail);let previous:HTMLElement|undefined;
  owner.subscribe(index=>{const card=railItems(rail)[index];if(card&&[...rail.querySelectorAll(selector)].includes(card)&&card!==previous){previous=card;select(index)}});
  return (index:number)=>owner.choose(index);
}

export function connectRailControls(rail:HTMLElement) {
  const controls=document.querySelector<HTMLElement>(`[data-rail-controls="${rail.id}"]`)!;
  const items=()=>railItems(rail),buttons=[...controls.querySelectorAll<HTMLButtonElement>('[data-rail-step]')];
  const count=controls.querySelector('output')!,segments=[...controls.querySelectorAll<HTMLElement>('.rail-progress span')];
  const owner=nativeRail(rail);let current=-1,total=-1;
  const paint=(index:number)=>{
    const cards=items();index=owner.target??index;
    if(current===index&&total===cards.length)return;
    current=index;total=cards.length;
    count.textContent=`${String(current+1).padStart(2,'0')} / ${String(cards.length).padStart(2,'0')}`;
    count.setAttribute('aria-label',`${current+1} из ${cards.length}`);
    segments.forEach((segment,i)=>{segment.hidden=i>=cards.length;segment.dataset.current=String(i===current)});
    buttons.forEach(button=>button.disabled=Number(button.dataset.railStep)<0?current===0:current===cards.length-1);
  };
  owner.subscribe(paint);
  buttons.forEach(button=>button.addEventListener('click',event=>{
    const cards=items();if(!cards.length)return;
    const instant=isKeyboardActivation(event)||matchMedia('(prefers-reduced-motion:reduce)').matches;
    owner.goTo((owner.target??owner.index)+Number(button.dataset.railStep),instant);
    if(isKeyboardActivation(event)&&button.disabled)buttons.find(other=>!other.disabled)?.focus({preventScroll:true});
  }));
  new ResizeObserver(()=>{controls.hidden=rail.scrollWidth<=rail.clientWidth+1}).observe(rail);
  return paint;
}

const owners=new WeakMap<HTMLElement,ReturnType<typeof createNativeRail>>();
export function nativeRail(rail:HTMLElement){let owner=owners.get(rail);if(!owner){owner=createNativeRail(rail);owners.set(rail,owner)}return owner;}

/** One position, target and clock for buttons, native touch, mouse magnet and indicators. */
function createNativeRail(rail:HTMLElement){
 const compact=matchMedia('(max-width:960px)'),reduced=matchMedia('(prefers-reduced-motion:reduce)'),listeners=new Set<(index:number)=>void>();
 let current=Number(rail.dataset.railIndex)||0,target:number|null=null,stops:number[]=[],frame=0,measureFrame=0,timer=0,phase='idle',snap='',width=-1,touchHeld=false;
 let touchStart:{x:number;y:number;index:number}|null=null,slideGesture:SlideFeedback|null=null;
 const nearest=(velocity=0)=>Math.max(0,stops.indexOf(nearestRailStop(stops,rail.scrollLeft,velocity)));
 const clamp=(index:number)=>Math.max(0,Math.min(railItems(rail).length-1,index));
 const cancelGesture=()=>{slideGesture?.cancel();slideGesture=null;touchStart=null;};
 const finishGesture=()=>{slideGesture?.finish();slideGesture=null;};
 // A later action must never confirm an earlier touch.
 document.addEventListener('pointerdown',cancelGesture,{capture:true,passive:true});
 document.addEventListener('keydown',cancelGesture,{capture:true});
 const publish=(index:number)=>{current=clamp(index);rail.dataset.railIndex=String(current);for(const listener of listeners)listener(current);slideGesture?.cross(current)};
 const track=()=>{if(!compact.matches||phase==='programmatic'||!stops.length)return;const index=nearest();if(index!==current)publish(index)};
 const restore=()=>{rail.style.scrollSnapType=snap;rail.dataset.railSettling='false'};
 const stop=()=>{cancelAnimationFrame(frame);frame=0;clearTimeout(timer);target=null;rail.dataset.railSettling='false'};
 function measure(){
  measureFrame=0;const cards=railItems(rail);rail.style.setProperty('--rail-count',String(cards.length));rail.style.setProperty('--rail-gap',getComputedStyle(rail).columnGap);
  const rect=rail.getBoundingClientRect();stops=cards.map(card=>Math.max(0,Math.min(rail.scrollWidth-rail.clientWidth,rail.scrollLeft+card.getBoundingClientRect().left-rect.left)));
  if(phase==='idle'&&compact.matches)publish(Math.min(current,cards.length-1));
 }
 const scheduleMeasure=()=>{if(!measureFrame)measureFrame=requestAnimationFrame(measure)};
 function goTo(index:number,instant=false,fromGesture=false){
   if(!fromGesture)cancelGesture();
  stop();if(measureFrame){cancelAnimationFrame(measureFrame);measure();}else if(!stops.length)measure();if(!stops.length)return;
  index=clamp(index);target=index;phase='programmatic';if(rail.style.scrollSnapType!=='none')snap=rail.style.scrollSnapType;rail.style.scrollSnapType='none';publish(index);
  const from=rail.scrollLeft,to=stops[index],start=performance.now();
   const finish=()=>{rail.scrollLeft=to;target=null;phase='idle';frame=0;restore();publish(index);if(fromGesture)finishGesture()};
  if(instant||reduced.matches||!compact.matches||Math.abs(to-from)<.5){finish();return;}
  rail.dataset.railSettling='true';
  const duration=numberToken('--motion-rail');
  const draw=(now:number)=>{const p=Math.min(1,(now-start)/duration);rail.scrollLeft=from+(to-from)*springProgress(p,spring.drawerDamping);if(p<1)frame=requestAnimationFrame(draw);else finish()};frame=requestAnimationFrame(draw);
 }
 function finishNative(){
  clearTimeout(timer);if(phase==='programmatic'||phase==='dragging'||touchHeld||!compact.matches||!stops.length)return;
  const index=nearest();
  // Native snap may round a fractional stop. Writing it again can emit scroll/scrollend forever.
   if(Math.abs(rail.scrollLeft-stops[index])<1){stop();phase='idle';restore();if(index!==current)publish(index);finishGesture();return;}
   goTo(index,false,true);
 }
 rail.style.setProperty('--rail-count',String(railItems(rail).length));rail.classList.add('compact-rail');
 rail.addEventListener('scroll',()=>{if(phase==='programmatic'||!compact.matches)return;track();if(phase==='dragging')return;phase='native';clearTimeout(timer);timer=window.setTimeout(finishNative,130)},{passive:true});
 rail.addEventListener('scrollend',finishNative);
 rail.addEventListener('focusin',event=>{
  const control=event.target instanceof Element?event.target:null;
  if(!compact.matches||!control?.matches(':focus-visible'))return;
  const index=railItems(rail).findIndex(card=>card.contains(control));
  if(index>=0)goTo(index,true);
 });
 rail.addEventListener('pointerdown',()=>{stop();phase='native';track()},{passive:true});
 rail.addEventListener('touchstart',event=>{touchHeld=compact.matches;cancelGesture();if(!compact.matches)return;const touch=event.touches[0];touchStart=event.touches.length===1?{x:touch.clientX,y:touch.clientY,index:current}:null;},{passive:true});
 rail.addEventListener('touchmove',event=>{
   if(!compact.matches||!touchStart||event.touches.length!==1)return;
   if(!slideGesture){const touch=event.touches[0],dx=Math.abs(touch.clientX-touchStart.x),dy=Math.abs(touch.clientY-touchStart.y);if(Math.max(dx,dy)<8)return;if(dy>=dx){cancelGesture();return;}slideGesture=beginSlideFeedback(touchStart.index,event);}
   slideGesture.cross(current);
 },{passive:true});
 for(const type of['touchend','touchcancel'])rail.addEventListener(type,event=>{
   if(!compact.matches){touchHeld=false;cancelGesture();return;}
  const touchEvent=event as TouchEvent;if(touchEvent.touches.length)return;
  const touch=touchEvent.changedTouches[0],start=touchStart;touchStart=null;touchHeld=false;
   if(type==='touchcancel')cancelGesture();
   else if(!slideGesture&&start&&touch&&Math.abs(touch.clientX-start.x)>Math.max(8,Math.abs(touch.clientY-start.y))){slideGesture=beginSlideFeedback(start.index,event);slideGesture.cross(current);}
  clearTimeout(timer);timer=window.setTimeout(finishNative,130);
 },{passive:true});
 rail.addEventListener('wheel',()=>{cancelGesture();stop();phase='native';restore()},{passive:true});
 new ResizeObserver(([entry])=>{if(Math.abs(entry.contentRect.width-width)<.5)return;width=entry.contentRect.width;cancelGesture();stop();phase='idle';restore();scheduleMeasure()}).observe(rail);
 new MutationObserver(scheduleMeasure).observe(rail,{childList:true});
 compact.addEventListener('change',()=>{cancelGesture();stop();phase='idle';restore();scheduleMeasure()});
 reduced.addEventListener('change',()=>{if(target!==null)goTo(target,true)});
 scheduleMeasure();
 return {get index(){return phase==='native'||phase==='dragging'?nearest():current},get target(){return target},goTo,choose(index:number){if(target===null)publish(index)},subscribe(listener:(index:number)=>void){listeners.add(listener)},track,beginDrag(event:PointerEvent){stop();slideGesture=beginSlideFeedback(current,event);phase='dragging';if(rail.style.scrollSnapType!=='none')snap=rail.style.scrollSnapType;rail.style.scrollSnapType='none'},release(velocity=0,cancelled=false){if(cancelled)cancelGesture();goTo(nearest(velocity),false,!cancelled)},interrupt(){cancelGesture();stop();phase='native';restore()},measure:scheduleMeasure};
}
