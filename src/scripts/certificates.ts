import { numberToken as n, reducedMotion,textToken } from './motion';
import { stepSpring, spring } from '../config/spring';
import {certificateWaveLevels} from './certificate-order';
import {enableHorizontalSwipe} from './horizontal-swipe';
import {isMousePointer} from './interaction-intent';

const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
const compact = matchMedia('(max-width:960px)');
for (const stage of document.querySelectorAll<HTMLElement>('[data-certificate-scene]')) {
  const cards = [...stage.querySelectorAll<HTMLButtonElement>('[data-certificate]')];
  const art = cards.map(c=>c.querySelector<HTMLElement>('.certificate-art')!);
  const states = cards.map(() => ({value:0,velocity:0,target:0,pendingTarget:0,targetAt:0,x:0,y:0,vx:0,vy:0,targetX:0,targetY:0}));
  let selected:number|null=null, levels=certificateWaveLevels(cards.length,null);
  let frame=0,previous=0,visible=false;
  const config=()=>({scale:n('--certificate-selected-scale'),depth:n('--certificate-depth-scale-step'),delay:n('--certificate-wave-delay'),tiltX:n('--certificate-hover-tilt-x'),tiltY:n('--certificate-hover-tilt-y'),perspective:n('--size-1100')});
  let settings=config(),sizes=cards.map(c=>({width:c.offsetWidth,height:c.offsetHeight}));
  function stop(){cancelAnimationFrame(frame);frame=previous=0;}
  function schedule(){if(!frame&&visible&&!document.hidden)frame=requestAnimationFrame(draw);}
  function draw(now:number){
    frame=0;
    const dt=previous?(now-previous)/1000:1/60;previous=now;
    let moving=false;
    cards.forEach((_,i)=>{
      if(now>=states[i].targetAt)states[i].target=states[i].pendingTarget;
      const target=states[i].target;
      moving ||= now<states[i].targetAt;
      const next=reducedMotion.matches?{value:target,velocity:0}:stepSpring(states[i].value,states[i].velocity,target,dt,spring.certificateDamping);
      Object.assign(states[i],next);
      const x=stepSpring(states[i].x,states[i].vx,states[i].targetX,dt,spring.pointerDamping),y=stepSpring(states[i].y,states[i].vy,states[i].targetY,dt,spring.pointerDamping);
      Object.assign(states[i],{x:x.value,y:y.value,vx:x.velocity,vy:y.velocity});
      moving ||= Math.max(Math.abs(next.value-target),Math.abs(next.velocity),Math.abs(x.value-states[i].targetX),Math.abs(y.value-states[i].targetY),Math.abs(x.velocity),Math.abs(y.velocity))>spring.epsilon;
      // The artwork owns depth and tilt; its button never changes hit geometry.
      art[i].style.transform=reducedMotion.matches?'none':`perspective(${settings.perspective}px) translate3d(0,0,0) rotateX(${-y.value*settings.tiltX}deg) rotateY(${x.value*settings.tiltY}deg) scale(${1+next.value*(settings.scale-1)})`;
    });
    if(moving&&!reducedMotion.matches)schedule();else previous=0;
  }
  function select(index:number){
    if(selected===index)return;
    selected=index;levels=certificateWaveLevels(cards.length,index);
    cards.forEach((card,i)=>{
      card.classList.toggle('is-front',i===index);card.setAttribute('aria-pressed',String(i===index));
      card.style.zIndex=String(cards.length-levels[i]);card.dataset.certificateLevel=String(levels[i]);
      states[i].pendingTarget=i===index?1:-levels[i]*settings.depth/(settings.scale-1);
      states[i].targetAt=performance.now()+(reducedMotion.matches?0:levels[i]*settings.delay);
    });schedule();
  }
  let draggedArt:HTMLElement|null=null,returning:Animation|undefined,dragX=0,dragAngle=0;
  function returnArt(){
    if(!draggedArt)return;
    const element=draggedArt,style=getComputedStyle(element),from={translate:style.translate,rotate:style.rotate};
    draggedArt=null;returning?.cancel();element.style.removeProperty('translate');element.style.removeProperty('rotate');
    if(!reducedMotion.matches)returning=element.animate([from,{translate:'0 0',rotate:'0deg'}],{duration:n('--motion-card'),easing:textToken('--ease-drawer-spring')});
  }
  enableHorizontalSwipe(stage,direction=>{select(((selected??0)+direction+cards.length)%cards.length);returnArt();},{enabled:()=>compact.matches,motion:{
    start(){
      draggedArt=art[selected??0];const style=getComputedStyle(draggedArt);dragX=parseFloat(style.translate)||0;dragAngle=parseFloat(style.rotate)||0;
      returning?.cancel();draggedArt.style.translate=`${dragX}px 0`;draggedArt.style.rotate=`${dragAngle}deg`;
    },
    move(dx){if(draggedArt){draggedArt.style.translate=`${dragX+dx*.35}px 0`;draggedArt.style.rotate=`${dragAngle+dx/stage.clientWidth*8}deg`}},cancel:returnArt,
  }});
  const reset=()=>{states.forEach(s=>{s.targetX=s.targetY=0;if(reducedMotion.matches)s.targetAt=0;});if(reducedMotion.matches){stop();draw(performance.now());}else schedule();};
  new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)schedule();else stop();}).observe(stage);
  cards.forEach((card,i)=>{
    card.addEventListener('pointerenter',event=>{if(isMousePointer(event)&&finePointer.matches)select(i);});
    card.addEventListener('pointermove',event=>{
      if(!isMousePointer(event)||!finePointer.matches||reducedMotion.matches)return;
      states[i].targetX=Math.max(-1,Math.min(1,event.offsetX/sizes[i].width*2-1));
      states[i].targetY=Math.max(-1,Math.min(1,event.offsetY/sizes[i].height*2-1));schedule();
    });
    card.addEventListener('pointerleave',()=>{states[i].targetX=states[i].targetY=0;schedule();});
    card.addEventListener('focus',()=>select(i));card.addEventListener('click',()=>select(i));
  });
  new ResizeObserver(()=>{settings=config();sizes=cards.map(c=>({width:c.offsetWidth,height:c.offsetHeight}));schedule();}).observe(stage);
  finePointer.addEventListener('change',reset);reducedMotion.addEventListener('change',reset);
  document.addEventListener('visibilitychange',()=>document.hidden?stop():schedule());
  window.addEventListener('pagehide',stop);window.addEventListener('pageshow',schedule);
}
