import {numberToken,reducedMotion} from './motion';
import {pageWheelActive} from './page-scroll';
import '../styles/reading.css';
export {updateReadingEdges} from './reading-edges';

/** Readers contain the current gesture; reviews can hand a continued edge gesture to the page. */
export function enableReadingScroll(element:HTMLElement,enabled:()=>boolean,signal:AbortSignal,{edgeChain='contained'}:{edgeChain?:'contained'|'buffered'}={}){
 let frame=0,target=0,position=0,last=0,time=0;
 let edgeDirection=0,edgeDistance=0;
 const release=(value:boolean)=>{element.dataset.readingReleased=String(value)};
 if(edgeChain==='buffered')element.dataset.readingChain='buffered';
 const resetEdge=()=>{edgeDirection=0;edgeDistance=0;release(false)};
 const stop=()=>{cancelAnimationFrame(frame);frame=0;};
 function draw(now:number){
  if(!enabled()||document.hidden){stop();return;}
  const range=Math.max(0,element.scrollHeight-element.clientHeight);target=Math.max(0,Math.min(range,target));
  position=Math.max(0,Math.min(range,position));
  const delta=target-position,alpha=1-Math.exp(-Math.min(40,now-last)/time);last=now;
  position=Math.abs(delta)<.5?target:position+delta*alpha;element.scrollTop=position;
  if(Math.abs(target-position)>.5)frame=requestAnimationFrame(draw);else{element.scrollTop=target;frame=0;}
 }
 element.addEventListener('wheel',event=>{
  const range=element.scrollHeight-element.clientHeight,tolerance=numberToken('--reading-scroll-tolerance');
  if(!enabled()||event.ctrlKey||Math.abs(event.deltaX)>=Math.abs(event.deltaY)||range<=tolerance){stop();return;}
  // Passing over a review during an existing page-wheel gesture must not capture that gesture.
  if(edgeChain==='buffered'&&pageWheelActive()){stop();resetEdge();release(true);return;}
  const direction=Math.sign(event.deltaY);
  const raw=event.deltaY*(event.deltaMode===1?parseFloat(getComputedStyle(element).lineHeight):event.deltaMode===2?element.clientHeight:1);
  if(direction<0&&element.scrollTop<=tolerance||direction>0&&element.scrollTop>=range-tolerance){
   stop();element.scrollTop=direction<0?0:range;
   if(edgeChain==='buffered'){
    if(edgeDirection!==direction){resetEdge();edgeDirection=direction;}
    edgeDistance+=Math.abs(raw);
    const released=edgeDistance>=numberToken('--reading-edge-distance');release(released);
    if(released)return;
   }
   if(event.cancelable)event.preventDefault();return;
  }
  resetEdge();
  const limit=Math.min(numberToken('--reading-wheel-limit'),element.clientHeight*.3);
  const amount=Math.max(-limit,Math.min(limit,raw*numberToken('--reading-wheel-scale')));
  if(!event.cancelable)return;event.preventDefault();
  if(!frame||Math.sign(target-position)!==direction){position=element.scrollTop;target=position;}
  target=Math.max(0,Math.min(range,target+amount));
  if(reducedMotion.matches){stop();element.scrollTop=target;return;}
  if(!frame){time=numberToken('--motion-ui')/3;last=performance.now();frame=requestAnimationFrame(draw);}
 },{signal,passive:false});
 if(edgeChain==='buffered'){
  // A swipe that starts in the text stays there. A new swipe at its edge can scroll the page.
  element.addEventListener('touchstart',()=>{stop();const range=element.scrollHeight-element.clientHeight,tolerance=numberToken('--reading-scroll-tolerance');resetEdge();release(range>tolerance&&(element.scrollTop<=tolerance||element.scrollTop>=range-tolerance));},{signal,passive:true});
  element.addEventListener('keydown',event=>{stop();const range=element.scrollHeight-element.clientHeight,tolerance=numberToken('--reading-scroll-tolerance');release((event.key==='ArrowUp'||event.key==='PageUp')&&element.scrollTop<=tolerance||(event.key==='ArrowDown'||event.key==='PageDown'||event.key===' ')&&element.scrollTop>=range-tolerance);},{signal,passive:true});
 }
 for(const name of ['pointerdown','keydown'])element.addEventListener(name,stop,{signal,passive:true});
 reducedMotion.addEventListener('change',stop,{signal});signal.addEventListener('abort',stop,{once:true});
}
