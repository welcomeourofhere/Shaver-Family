import {numberToken,reducedMotion,modalScrollLocked} from './motion';

// Smooth discrete mouse-wheel input only. Touch, precision trackpads and nested readers stay native.
let frame=0,position=0,target=0,last=0,lastWheel=-Infinity;
export const pageWheelActive=()=>frame!==0||performance.now()-lastWheel<numberToken('--motion-ui');
const stop=()=>{cancelAnimationFrame(frame);frame=0;};
function draw(now:number){
 if(modalScrollLocked()){stop();return;}
 const limit=Math.max(0,document.documentElement.scrollHeight-innerHeight);target=Math.min(limit,Math.max(0,target));
 const delta=target-position,alpha=1-Math.exp(-Math.min(40,now-last)/numberToken('--page-wheel-response'));last=now;
 position=Math.abs(delta)<.5?target:position+delta*alpha;scrollTo({top:position,behavior:'instant'});
 if(Math.abs(target-position)>.5)frame=requestAnimationFrame(draw);else frame=0;
}
addEventListener('wheel',event=>{
 if(!event.isTrusted||event.defaultPrevented||event.ctrlKey||event.metaKey||event.shiftKey||Math.abs(event.deltaX)>=Math.abs(event.deltaY)){stop();return;}
 const releasedReader=event.target instanceof Element&&event.target.closest('.reading-prose[data-reading-released="true"]');
 const smooth=!reducedMotion.matches&&matchMedia('(hover:hover) and (pointer:fine)').matches;
 if(!smooth&&!releasedReader){stop();return;}
 if(event.target instanceof Element&&event.target.closest('dialog,iframe,[contenteditable="true"],textarea,.choice-list,.hero-news-details,.reading-prose[data-reading-scrollable="true"]:not([data-reading-released="true"])')){stop();return;}
 const raw=event.deltaY*(event.deltaMode===1?parseFloat(getComputedStyle(document.documentElement).lineHeight):event.deltaMode===2?innerHeight:1);
 lastWheel=performance.now();
 if(!smooth||Math.abs(raw)<40){stop();if(releasedReader&&event.cancelable){event.preventDefault();scrollBy({top:raw,behavior:'instant'});}return;}
 const limit=numberToken('--page-wheel-limit'),amount=Math.max(-limit,Math.min(limit,raw*numberToken('--page-wheel-scale')));
 if(!event.cancelable)return;event.preventDefault();
 if(!frame||Math.sign(target-position)!==Math.sign(amount)){position=scrollY;target=position;}
 target=Math.max(0,Math.min(document.documentElement.scrollHeight-innerHeight,Math.min(position+innerHeight*.75,Math.max(position-innerHeight*.75,target+amount))));
 if(!frame){last=performance.now();frame=requestAnimationFrame(draw);}
},{passive:false});
for(const type of['pointerdown','keydown','pagehide','blur'])addEventListener(type,stop,{passive:true});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});reducedMotion.addEventListener('change',stop);
