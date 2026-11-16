import {nativeRail} from './rail-selection.ts';
import {isMousePointer} from './interaction-intent.ts';
import {numberToken} from './design-tokens.ts';
import {requestFeedback} from './feedback.ts';

/** Native touch stays native; mouse dragging uses the rail's one interruptible magnet. */
export function enableRailMouseDrag(rail:HTMLElement,compact:MediaQueryList){
 const owner=nativeRail(rail);
 let drag:{id:number;x:number;y:number;left:number;index:number;locked:boolean;lastX:number;lastTime:number;velocity:number}|null=null,blockedUntil=0,cancelledPointer:number|null=null;
 function finish(cancelled=false,event?:PointerEvent){const state=drag;drag=null;if(!state)return;if(state.locked){blockedUntil=performance.now()+numberToken('--motion-ui');if(cancelled)cancelledPointer=state.id;owner.release(cancelled||performance.now()-state.lastTime>100?0:state.velocity);if(!cancelled&&event&&(owner.target??owner.index)!==state.index)requestFeedback('select',event);}else if(rail.style.scrollSnapType==='none')owner.release();if(rail.hasPointerCapture(state.id))rail.releasePointerCapture(state.id);rail.classList.remove('is-dragging')}
 rail.addEventListener('pointerdown',event=>{
  if(!isMousePointer(event)){const previous=drag;drag=null;blockedUntil=0;cancelledPointer=null;if(previous){if(rail.hasPointerCapture(previous.id))rail.releasePointerCapture(previous.id);rail.classList.remove('is-dragging')}return;}
  if(!compact.matches||event.button!==0||!event.isPrimary||event.target instanceof Element&&event.target.closest('[data-rail-nested]'))return;
  finish(true);
  drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:rail.scrollLeft,index:owner.index,locked:false,lastX:event.clientX,lastTime:performance.now(),velocity:0};blockedUntil=0;cancelledPointer=null;
 });
 rail.addEventListener('pointermove',event=>{
  if(!drag||event.pointerId!==drag.id)return;
  if(!compact.matches||(event.buttons&1)===0){finish(true);return;}
  const dx=event.clientX-drag.x,dy=event.clientY-drag.y;
  if(!drag.locked){if(Math.max(Math.abs(dx),Math.abs(dy))<8)return;if(Math.abs(dy)>=Math.abs(dx)){finish(true);return;}drag.locked=true;owner.beginDrag();rail.setPointerCapture(event.pointerId);rail.classList.add('is-dragging')}
  const now=performance.now();drag.velocity=-(event.clientX-drag.lastX)/Math.max(16,now-drag.lastTime);drag.lastX=event.clientX;drag.lastTime=now;event.preventDefault();rail.scrollLeft=drag.left-dx;owner.track();
 });
 rail.addEventListener('pointerup',event=>{if(event.pointerId===drag?.id)finish(false,event)});
 rail.addEventListener('pointercancel',event=>{if(event.pointerId===drag?.id)finish(true)});
 rail.addEventListener('lostpointercapture',event=>{if(event.target===rail&&event.pointerId===drag?.id)finish(true)});
 rail.addEventListener('click',event=>{if(event.detail&&(cancelledPointer!==null||performance.now()<blockedUntil)){event.preventDefault();event.stopImmediatePropagation()}},{capture:true});
 rail.addEventListener('dragstart',event=>{if(compact.matches)event.preventDefault()});
 compact.addEventListener('change',()=>finish(true));addEventListener('blur',()=>finish(true));
 addEventListener('resize',()=>finish(true));addEventListener('keydown',()=>finish(true));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)finish(true)});
 // A release outside the window may be absent; a new primary press starts a fresh sequence.
 document.addEventListener('pointerdown',event=>{if(event.isPrimary){cancelledPointer=null;blockedUntil=0;}},{capture:true,passive:true});
 document.addEventListener('pointerup',event=>{if(event.pointerId===cancelledPointer){blockedUntil=performance.now()+numberToken('--motion-ui');cancelledPointer=null;}},{capture:true,passive:true});
 document.addEventListener('pointercancel',event=>{if(event.pointerId===cancelledPointer)cancelledPointer=null;},{passive:true});
}
