import {closeDialog,numberToken,reducedMotion,textToken} from './motion';

export function enableSheetDismiss(dialog:HTMLElement,close=()=>closeDialog(dialog as HTMLDialogElement,reducedMotion.matches)) {
  const compact=matchMedia('(max-width:960px)');
  let drag:{id:number;start:number;time:number;distance:number;limit:number}|null=null;
  let rebound:Animation|undefined,closing=false;
  const reset=()=>{drag=null;rebound?.cancel();rebound=undefined;dialog.style.removeProperty('translate')};
  dialog.addEventListener('pointerdown',event=>{
    const target=event.target as Element;
    if(!compact.matches||drag||closing||!event.isPrimary||event.button!==0||target.closest('button,a,input,select')||!target.closest('.menu-grip,.dialog-head'))return;
    const offset=parseFloat(getComputedStyle(dialog).translate.split(' ').at(-1)||'0')||0;
    rebound?.cancel();dialog.style.translate=`0 ${offset}px`;
    drag={id:event.pointerId,start:event.clientY-offset,time:performance.now(),distance:offset,limit:dialog.offsetHeight*.35};
    dialog.setPointerCapture(event.pointerId);
  });
  dialog.addEventListener('pointermove',event=>{
    if(!drag||event.pointerId!==drag.id)return;
    const raw=Math.max(0,event.clientY-drag.start);
    drag.distance=raw>drag.limit?drag.limit+Math.sqrt((raw-drag.limit)*numberToken('--size-12')):raw;
    dialog.style.translate=`0 ${drag.distance}px`;
  });
  async function release(event:PointerEvent,cancelled=false) {
    if(!drag||event.pointerId!==drag.id)return;
    const {distance,time}=drag;drag=null;
    if(dialog.hasPointerCapture(event.pointerId))dialog.releasePointerCapture(event.pointerId);
    const dismiss=!cancelled&&(distance>=numberToken('--size-64')||(distance>=numberToken('--size-20')&&distance/Math.max(1,performance.now()-time)>.11));
    if(dismiss){closing=true;await close();closing=false;reset();return;}
    if(reducedMotion.matches){reset();return;}
    rebound=dialog.animate([{translate:`0 ${distance}px`},{translate:'0 0'}],{duration:numberToken('--motion-window'),easing:textToken('--ease-window-spring')});
    const animation=rebound;
    try{await animation.finished;if(rebound===animation)reset()}catch{/* A new drag owns its current position. */}
  }
  dialog.addEventListener('pointerup',event=>void release(event));
  dialog.addEventListener('pointercancel',event=>void release(event,true));
  dialog.addEventListener('close',reset);
  compact.addEventListener('change',reset);
}
