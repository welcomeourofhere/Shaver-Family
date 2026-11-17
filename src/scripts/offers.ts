import {numberToken as n,reducedMotion} from './motion';
import {offerSlot,offerDealFrame,wrapOfferPhase as wrap} from './offer-loop';
import {spring,drawerSpringCSS} from '../config/spring';
import {requestFeedback,beginSlideFeedback,type SlideFeedback} from './feedback';
import {enableHorizontalSwipe} from './horizontal-swipe';
import {observeRail,connectRailControls,enableRailCardSelection,nativeRail} from './rail-selection';
import {enableRailMouseDrag} from './native-rail-drag';
import {swipeDirection} from './gesture-math';

type Pose={transform:string;opacity:string;visible:boolean;leaving:boolean};
for(const section of document.querySelectorAll<HTMLElement>('[data-offers]')){
  const rail=section.querySelector<HTMLElement>('[data-of-rail]')!;
  const cards=[...rail.querySelectorAll<HTMLElement>('[data-offer-id]')];
  const position=section.querySelector<HTMLElement>('[data-of-position]')!;
  const controller=new AbortController(),{signal}=controller;
  const posterWindow=()=>{
    const reach=compact.matches?1:Math.ceil(rail.clientWidth/cards[0].clientWidth);
    cards.forEach((card,index)=>{
      const distance=compact.matches?Math.abs(index-selected):Math.min(wrap(index-selected,cards.length),wrap(selected-index,cards.length));
      if(distance>reach)return;
      const image=card.querySelector<HTMLImageElement>('img[data-offer-src]');if(!image)return;
      image.srcset=image.dataset.offerSrcset!;image.src=image.dataset.offerSrc!;
      delete image.dataset.offerSrc;delete image.dataset.offerSrcset;
    });
  };
  const compact=matchMedia('(max-width:960px)');
  let selected=0,stride=1,width=1,frameWidth=0,onScreen=true,revision=0,animations:Animation[]=[];
  let dragPoses:Pose[]|null=null,dragProgress=0,dragOrigin=0;
   let slideGesture:SlideFeedback|null=null;
   const finishGesture=(cancelled=false)=>{if(cancelled)slideGesture?.cancel();else slideGesture?.finish();slideGesture=null;};
  let cancelSwipe=()=>{};
  const readDealTokens=()=>({scale:n('--offer-fold-scale'),depth:n('--offer-fold-depth'),arrival:n('--offer-arrival-spring'),phi:n('--golden-ratio')});
  let dealTokens=readDealTokens();
  enableRailMouseDrag(rail,compact);
  const controls=connectRailControls(rail);
  const choose=observeRail(rail,'.of-card',index=>{if(compact.matches){showSelection(index);controls(index);}});
  const transform=(x:number,scale=1,y=0)=>`translate3d(${x}px,${y}px,0) scale(${scale})`;
  const layout=(index:number)=>offerSlot(index,selected,cards.length,stride,width);
  const snapshot=()=>cards.map(card=>{const s=getComputedStyle(card);return{transform:s.transform,opacity:s.opacity,leaving:card.dataset.offerLeaving==='true',visible:s.visibility!=='hidden'&&parseFloat(s.opacity)>.001};});
  function deal(i:number,previous:number,next:number,direction:number,poses:Pose[]){
    const slot=offerSlot(i,next,cards.length,stride,width),from=poses[i],distance=direction>0?wrap(next-previous,cards.length):wrap(previous-next,cards.length);
    const folded=!slot.visible&&from.visible&&(from.leaving||direction>0&&wrap(i-previous,cards.length)<distance),emerging=direction<0&&i===next&&!from.visible;
    const start=emerging?{transform:transform(0,dealTokens.scale,dealTokens.depth),opacity:'0'}:!from.visible&&slot.visible?{transform:transform(Math.min(width+stride,slot.x+distance*stride)),opacity:'1'}:from;
    const end=folded?{transform:transform(0,dealTokens.scale,dealTokens.depth),opacity:'0'}:{transform:transform(slot.x),opacity:'1'};
    const a=new DOMMatrix(start.transform),b=new DOMMatrix(end.transform);
    return{slot,folded,visible:from.visible||slot.visible,from:{x:a.m41,y:a.m42,scale:a.m11,opacity:Number(start.opacity)},to:{x:b.m41,y:b.m42,scale:b.m11,opacity:Number(end.opacity)}};
  }
  function cancel(){animations.forEach(a=>a.cancel());animations=[];}
  function showSelection(index:number){
    selected=index;section.dataset.offerIndex=String(index);position.textContent=`${index+1} / ${cards.length}`;
    posterWindow();
    cards.forEach((card,i)=>card.dataset.offerActive=String(i===index));
    section.querySelector<HTMLButtonElement>('[data-of-prev]')!.disabled=compact.matches&&index===0;
    section.querySelector<HTMLButtonElement>('[data-of-next]')!.disabled=compact.matches&&index===cards.length-1;
  }
  function rest(){
    cancel();dragPoses=null;section.dataset.offersMoving='false';section.dataset.offerLoop=String(!compact.matches);
    if(compact.matches){
      const focused=rail.contains(document.activeElement)?document.activeElement as HTMLElement:null;
      cards.forEach((card,i)=>{card.style.transform='none';card.style.opacity='1';card.style.visibility='visible';card.inert=false;card.setAttribute('aria-hidden','false');card.style.removeProperty('z-index');delete card.dataset.offerLeaving;if(rail.children[i]!==card)rail.insertBefore(card,rail.children[i]??null);});
      if(focused&&focused!==document.activeElement)focused.focus({preventScroll:true});
      rail.scrollTo({left:rail.scrollLeft+cards[selected].getBoundingClientRect().left-rail.getBoundingClientRect().left,behavior:'instant'});
      showSelection(selected);choose(selected);controls(selected);return;
    }
    rail.scrollLeft=0;showSelection(selected);
    cards.forEach((card,i)=>{
      const slot=layout(i);card.style.transform=transform(slot.x);card.style.opacity='1';card.style.visibility=slot.visible?'visible':'hidden';
      delete card.dataset.offerLeaving;card.inert=!slot.visible;card.setAttribute('aria-hidden',String(!slot.visible));card.style.zIndex=String(cards.length-slot.offset);
    });
    const focused=rail.contains(document.activeElement)?document.activeElement as HTMLElement:null;
    for(let offset=0;offset<cards.length;offset++){
      const card=cards[wrap(selected+offset,cards.length)];if(rail.children[offset]!==card)rail.insertBefore(card,rail.children[offset]??null);
    }
    if(focused&&focused!==document.activeElement)focused.focus({preventScroll:true});
  }
   function select(index:number,direction:number,animate=true,event?:Event,fromGesture=false){
    cancelSwipe();
    const next=compact.matches?Math.max(0,Math.min(cards.length-1,index)):wrap(index,cards.length);
    if(compact.matches){
      if(event&&next!==selected)requestFeedback('select',event);
      nativeRail(rail).goTo(next,!animate||reducedMotion.matches);return;
    }
    if(next===selected)return;
     if(event&&!fromGesture)requestFeedback('select',event);
    dealTokens=readDealTokens();
    const previous=selected,progress=dragPoses?dragProgress:0,poses=snapshot();
    const turn=++revision;cancel();dragPoses=null;showSelection(next);
    if(!animate||reducedMotion.matches||!onScreen||document.hidden){rest();return;}
    section.dataset.offersMoving='true';
    const duration=n('--motion-offer-deal')*Math.max(.25,1-progress),{arrival,phi}=dealTokens;
    cards.forEach((card,i)=>{
      const {slot,folded,visible,from,to}=deal(i,previous,next,direction,poses);card.dataset.offerLeaving=String(folded);
      card.style.visibility=visible?'visible':'hidden';card.inert=!slot.visible;card.setAttribute('aria-hidden',String(!slot.visible));
      card.style.zIndex=String(folded?0:i===next?cards.length+2:cards.length-slot.offset);
      if(!visible)return;
      const frames=Array.from({length:spring.samples+1},(_,sample)=>{
        const pose=offerDealFrame(from,to,sample/spring.samples,folded?0:arrival/phi**slot.offset);
        return {transform:transform(pose.x,pose.scale,pose.y),opacity:pose.opacity};
      });
      animations.push(card.animate(frames,{duration,easing:'linear',fill:'both'}));
    });
    void Promise.allSettled(animations.map(a=>a.finished)).then(()=>{if(turn===revision)rest();});
  }
  function step(direction:number,event?:Event){
    if(compact.matches){const button=section.querySelector<HTMLButtonElement>(`[data-rail-step="${direction}"]`)!;if(!button.disabled)button.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:(event as MouseEvent|undefined)?.detail??0}));return;}
    select(selected+direction,direction,(event as MouseEvent|undefined)?.detail!==0,event);
  }
  function measure(){
    const next=rail.clientWidth;if(next===frameWidth)return;frameWidth=next;
    cancelSwipe();
    ++revision;width=next;const cardWidth=parseFloat(getComputedStyle(cards[0]).width);stride=cardWidth+parseFloat(getComputedStyle(rail).columnGap);rest();
  }
  section.dataset.offerIndex='0';rail.dataset.loopReady='true';measure();
  function hash(){let id='';try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const i=cards.findIndex(c=>c.id===id);if(i>=0)select(i,1,false);}
  addEventListener('hashchange',hash,{signal});hash();
  section.querySelector('[data-of-prev]')?.addEventListener('click',e=>step(-1,e),{signal});
  section.querySelector('[data-of-next]')?.addEventListener('click',e=>step(1,e),{signal});
  rail.addEventListener('keydown',e=>{
    const next=e.key==='ArrowLeft'?selected-1:e.key==='ArrowRight'?selected+1:e.key==='Home'?0:e.key==='End'?cards.length-1:null;
    if(next===null)return;e.preventDefault();rail.focus({preventScroll:true});select(next,next<selected?-1:1,false,e);
  },{signal});
  rail.addEventListener('focusin',e=>{
    const control=e.target instanceof Element?e.target:null,card=control?.closest<HTMLElement>('[data-offer-id]');
    if(!card||!control?.matches(':focus-visible'))return;
    const r=card.getBoundingClientRect(),bounds=rail.getBoundingClientRect();
    if(r.right>bounds.right+1)select(cards.indexOf(card),1,false);
  },{signal});
  cancelSwipe=enableHorizontalSwipe(rail,(direction,event)=>select(selected+direction,direction,true,event),{signal,enabled:()=>!compact.matches,motion:{
    start(event){
      finishGesture(true);slideGesture=beginSlideFeedback(selected,event);
      dealTokens=readDealTokens();
      dragPoses=snapshot();dragProgress=0;dragOrigin=0;
      ++revision;cancel();section.dataset.offersMoving='true';
    },
    move(dx){
      if(!dragPoses)return;
      const unit=stride*.5;
      let travel=dx-dragOrigin;
      while(Math.abs(travel)>=unit){
        const direction=travel<0?1:-1;
        showSelection(wrap(selected+direction,cards.length));slideGesture?.cross(selected);rest();dragPoses=snapshot();
        dragOrigin-=direction*unit;travel=dx-dragOrigin;
        section.dataset.offersMoving='true';
      }
      const direction=travel<0?1:-1,next=wrap(selected+direction,cards.length);dragProgress=Math.abs(travel)/unit;
      cards.forEach((card,i)=>{
        const step=deal(i,selected,next,direction,dragPoses!),pose=offerDealFrame(step.from,step.to,dragProgress,step.folded?0:dealTokens.arrival/dealTokens.phi**step.slot.offset,true);
        card.style.visibility=step.visible?'visible':'hidden';card.style.opacity=String(pose.opacity);card.style.transform=transform(pose.x,pose.scale,pose.y);
        card.style.zIndex=String(step.folded?0:cards.length-step.slot.offset);
      });
    },
    release(dx,velocity,event){const direction=swipeDirection(dx-dragOrigin,velocity,stride*.5);if(direction){slideGesture?.cross(wrap(selected+direction,cards.length));select(selected+direction,direction,true,event,true);}else cancelDrag();finishGesture();},
    cancel:()=>{finishGesture(true);cancelDrag();},
  }});
  function cancelDrag(){
      if(!dragPoses)return;dragPoses=null;
      const turn=++revision;cancel();
      if(reducedMotion.matches){rest();return;}
      const duration=n('--motion-card');
      cards.forEach((card,i)=>{if(getComputedStyle(card).visibility==='hidden')return;const slot=layout(i),s=getComputedStyle(card);animations.push(card.animate([{transform:s.transform,opacity:s.opacity},{transform:transform(slot.x),opacity:slot.visible?'1':'0'}],{duration,easing:drawerSpringCSS,fill:'both'}));});
      void Promise.allSettled(animations.map(a=>a.finished)).then(()=>{if(turn===revision)rest();});
  }
  enableRailCardSelection(rail,'.of-card',()=>compact.matches,index=>choose(index),signal);
  rail.addEventListener('click',e=>{
    if(e.defaultPrevented||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    const origin=e.target instanceof Element?e.target:null;
    if(origin?.closest('button,a[href],summary,input,select,textarea,[role="button"],[contenteditable="true"]'))return;
    const card=origin?.closest<HTMLElement>('[data-offer-id]');if(card)select(cards.indexOf(card),1,true,e);
  },{signal});
  const resize=new ResizeObserver(measure);resize.observe(rail);
  const visibility=new IntersectionObserver(([entry])=>{onScreen=entry.isIntersecting;if(!onScreen){cancelSwipe();++revision;rest();}});visibility.observe(rail);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelSwipe();++revision;rest();}},{signal});
  reducedMotion.addEventListener('change',()=>{cancelSwipe();++revision;rest();},{signal});
  compact.addEventListener('change',()=>{cancelSwipe();++revision;rest();},{signal});
  document.addEventListener('astro:before-swap',()=>{++revision;cancel();resize.disconnect();visibility.disconnect();controller.abort();},{once:true,signal});
}
