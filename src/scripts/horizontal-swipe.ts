import {numberToken} from './motion';
import {swipeDirection} from './gesture-math';

type SwipeMotion={start?:(event:PointerEvent)=>void;move?:(dx:number,dy:number,event:PointerEvent)=>void;release?:(dx:number,velocity:number,event:PointerEvent)=>void;cancel?:(event?:PointerEvent)=>void};

export function enableHorizontalSwipe(
  element:HTMLElement,
  select:(direction:number,event:PointerEvent)=>void,
  {enabled=()=>true,signal,motion}:{enabled?:()=>boolean;signal?:AbortSignal;motion?:SwipeMotion}={},
) {
  let gesture:{id:number;x:number;y:number;locked:boolean;lastX:number;lastTime:number;velocity:number}|null=null;
  let blockClickUntil=0,cancelledPointer:number|null=null;
  function reset(cancelled=false,event?:PointerEvent) {
    const previous=gesture;gesture=null;if(previous)element.classList.remove('is-dragging');
    if(previous?.locked){blockClickUntil=performance.now()+numberToken('--motion-ui');if(cancelled)cancelledPointer=previous.id;}
    if(previous&&element.hasPointerCapture(previous.id))element.releasePointerCapture(previous.id);
    if(previous?.locked&&cancelled)motion?.cancel?.(event);
  }
  // A second finger belongs to browser pinch zoom, including one outside the rail.
  document.addEventListener('pointerdown',event=>{
    if(!event.isPrimary)reset(true,event);
    else{cancelledPointer=null;blockClickUntil=0;}
  },{signal,capture:true,passive:true});
  element.addEventListener('pointerdown',event=>{
    if(!event.isPrimary||event.button!==0||!enabled()||(event.target as Element).closest('input,textarea,select,[contenteditable="true"]'))return;
    reset(true,event);
    blockClickUntil=0;cancelledPointer=null;gesture={id:event.pointerId,x:event.clientX,y:event.clientY,locked:false,lastX:event.clientX,lastTime:performance.now(),velocity:0};
  },{signal,passive:true});
  element.addEventListener('pointermove',event=>{
    if(!gesture||gesture.id!==event.pointerId)return;
    if(!enabled()||(event.pointerType!=='touch'&&(event.buttons&1)===0)){reset(true,event);return;}
    const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y;
    if(!gesture.locked){
      if(Math.max(Math.abs(dx),Math.abs(dy))<numberToken('--swipe-lock-threshold'))return;
      if(Math.abs(dy)>=Math.abs(dx)){reset();return;}
      gesture.locked=true;motion?.start?.(event);element.setPointerCapture(event.pointerId);element.classList.add('is-dragging');
      const selection=getSelection();if(selection?.anchorNode&&element.contains(selection.anchorNode))selection.removeAllRanges();
    }
    const now=performance.now();gesture.velocity=(event.clientX-gesture.lastX)/Math.max(16,now-gesture.lastTime);gesture.lastX=event.clientX;gesture.lastTime=now;
    motion?.move?.(dx,dy,event);
    if(event.cancelable)event.preventDefault();
  },{signal});
  element.addEventListener('pointerup',event=>{
    if(!gesture||gesture.id!==event.pointerId)return;
    const {x,y,locked,velocity,lastTime}=gesture,dx=event.clientX-x,dy=event.clientY-y;reset();
    const speed=performance.now()-lastTime<100?velocity:0;
    if(locked&&enabled()&&motion?.release){motion.release(dx,speed,event);return;}
    const direction=locked&&enabled()&&Math.abs(dx)>Math.abs(dy)?swipeDirection(dx,speed,element.clientWidth):0;
    if(direction)select(direction,event);else if(locked)motion?.cancel?.(event);
  },{signal});
  element.addEventListener('pointercancel',event=>{if(gesture?.id===event.pointerId)reset(true,event);},{signal});
  // Implicit touch capture is transferred from a child image/button to the rail.
  element.addEventListener('lostpointercapture',event=>{if(event.target===element&&gesture?.id===event.pointerId)reset(true,event);},{signal});
  addEventListener('blur',()=>reset(true),{signal});
  addEventListener('resize',()=>reset(true),{signal});
  addEventListener('keydown',()=>reset(true),{signal});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)reset(true);},{signal});
  // A cancelled hold can be released much later than the short post-drag click buffer.
  document.addEventListener('pointerup',event=>{if(event.pointerId===cancelledPointer){blockClickUntil=performance.now()+numberToken('--motion-ui');cancelledPointer=null;}},{signal,capture:true,passive:true});
  document.addEventListener('pointercancel',event=>{if(event.pointerId===cancelledPointer)cancelledPointer=null;},{signal,passive:true});
  element.addEventListener('dragstart',event=>{if(enabled())event.preventDefault();},{signal});
  element.addEventListener('click',event=>{
    if(event.detail&&(cancelledPointer!==null||performance.now()<blockClickUntil)){event.preventDefault();event.stopImmediatePropagation();}
  },{signal,capture:true});
  signal?.addEventListener('abort',()=>reset(true),{once:true});
  return ()=>reset(true);
}
