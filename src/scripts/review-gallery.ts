import {enableHorizontalSwipe} from './horizontal-swipe';
import {bindSlideIndicator,selectSlideIndicator} from './slide-indicator';
import {numberToken,textToken,reducedMotion,isKeyboardActivation} from './motion';
import {requestFeedback} from './feedback';

/** The gallery owns its selected medium; the outer review rail owns only the review. */
export function createReviewGallery(gallery:HTMLElement,signal:AbortSignal){
 const slides=[...gallery.querySelectorAll<HTMLElement>('[data-review-slide]')],indicator=gallery.querySelector<HTMLElement>('[data-slide-indicator]');
 const video=gallery.querySelector<HTMLVideoElement>('video'),status=gallery.querySelector<HTMLElement>('[data-review-video-status]')!;
 const phone=matchMedia('(max-width:960px)'),label=gallery.getAttribute('aria-label')!;
 let current=0,visible=false,paused=false,manualPlayback=false,timer=0,animations:Animation[]=[],drag:{base:number;dx:number;neighbor:number}|null=null;
 const wrap=(index:number)=>(index+slides.length)%slides.length;
 const canPlay=()=>visible&&!document.hidden&&!gallery.inert&&current===0&&!paused&&(!reducedMotion.matches||manualPlayback);
 function playback(){
  clearTimeout(timer);
  if(video&&visible&&!video.poster)video.poster=video.dataset.videoPoster!;
  if(video&&canPlay()){
   if(!video.getAttribute('src'))video.src=video.dataset.videoSrc!;
   void video.play().catch(()=>{/* The supplied poster remains visible if autoplay is denied. */});
  }else video?.pause();
  if(phone.matches&&slides.length>1&&visible&&!document.hidden&&!gallery.inert&&!paused&&!reducedMotion.matches){
   const duration=video&&current===0?Math.max(numberToken('--review-photo-interval'),(video.duration||0)*1000):numberToken('--review-photo-interval');
   timer=window.setTimeout(()=>select(current+1),duration);
  }
 }
 function clear(){animations.forEach(animation=>animation.cancel());animations=[];drag=null;slides.forEach(slide=>{slide.style.removeProperty('transform');slide.style.removeProperty('opacity')});}
 function animate(poses:{slide:HTMLElement;from:string;to:string}[]){
  animations.forEach(animation=>animation.cancel());
  if(reducedMotion.matches){clear();return;}
  animations=poses.map(({slide,from,to})=>slide.animate([{transform:from,opacity:1},{transform:to,opacity:1}],{duration:numberToken('--motion-panel'),easing:textToken('--ease-drawer-spring')}));
  const running=animations;
  void Promise.allSettled(running.map(animation=>animation.finished)).then(()=>{if(animations===running)clear()});
 }
 function cancel(){
  if(!drag)return;
  const next=drag.neighbor,sign=drag.dx<0?-1:1,poses=[current,next].map(i=>getComputedStyle(slides[i]).transform);
  animate([{slide:slides[current],from:poses[0],to:'translateX(0)'},{slide:slides[next],from:poses[1],to:`translateX(${-sign*gallery.clientWidth}px)`}]);drag=null;
 }
 function select(index:number,event?:Event){
  const forward=index>current;
  index=wrap(index);
  if(index===0&&video?.error){video.removeAttribute('src');status.textContent='';}
  if(index===current){if(isKeyboardActivation(event))clear();else cancel();playback();return;}
  const previous=current,gesture=drag,sign=gesture?(gesture.dx<0?-1:1):(forward?-1:1);
  if(gesture)index=wrap(current+(sign<0?1:-1));
  const moving=!!gesture||animations.length>0,enter=getComputedStyle(slides[index]);
  const poses=[moving?getComputedStyle(slides[previous]).transform:'translateX(0)',moving&&Number(enter.opacity)>0?enter.transform:`translateX(${-sign*gallery.clientWidth}px)`];
  clear();current=index;
  slides.forEach((slide,i)=>{slide.dataset.active=String(i===current);slide.inert=i!==current;slide.setAttribute('aria-hidden',String(i!==current));});
  if(indicator)selectSlideIndicator(indicator,current);
  gallery.dataset.slideIndex=String(current);playback();
  if(event)requestFeedback('select',event);
  if(!isKeyboardActivation(event))animate([{slide:slides[previous],from:poses[0],to:`translateX(${sign*gallery.clientWidth}px)`},{slide:slides[current],from:poses[1],to:'translateX(0)'}]);
 }
 slides.forEach((slide,i)=>{slide.inert=i!==0;slide.setAttribute('aria-hidden',String(i!==0));});
 gallery.dataset.slideIndex='0';
 if(indicator)bindSlideIndicator(indicator,select,signal);
 gallery.addEventListener('keydown',event=>{
  if(event.target!==gallery)return;
  if(event.code==='Space'&&(video||phone.matches&&slides.length>1)){event.preventDefault();event.stopPropagation();paused=video&&current===0?!video.paused:!paused;manualPlayback=!paused;playback();}
  if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){
   event.preventDefault();event.stopPropagation();select(event.key==='Home'?0:event.key==='End'?slides.length-1:current+(event.key==='ArrowRight'?1:-1),event);
  }
 },{signal});
 if(slides.length>1)enableHorizontalSwipe(gallery,(direction,event)=>select(current+direction,event),{signal,enabled:()=>!phone.matches&&!gallery.inert,motion:{
  start(){
   const poses=slides.map(slide=>({transform:getComputedStyle(slide).transform,opacity:getComputedStyle(slide).opacity}));
   animations.forEach(animation=>animation.cancel());animations=[];
   slides.forEach((slide,i)=>{slide.style.transform=poses[i].transform;slide.style.opacity=poses[i].opacity;});
   const base=new DOMMatrix(poses[current].transform).m41;drag={base,dx:base,neighbor:wrap(current+1)};
  },
  move(dx){
   if(!drag)return;drag.dx=drag.base+dx;const sign=drag.dx<0?-1:1,next=wrap(current+(sign<0?1:-1));drag.neighbor=next;
   slides.forEach((slide,i)=>{slide.style.opacity=String(i===current||i===next?1:0);});
   slides[current].style.transform=`translateX(${drag.dx}px)`;slides[next].style.transform=`translateX(${-sign*gallery.clientWidth+drag.dx}px)`;
  },cancel,
 }});
 const observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting&&entry.intersectionRatio>=.5;playback();},{threshold:[0,.5]});observer.observe(gallery);
 function configure(){clear();gallery.toggleAttribute('data-rail-nested',slides.length>1&&!phone.matches);if(indicator){indicator.inert=phone.matches;indicator.setAttribute('aria-hidden',String(phone.matches));}gallery.setAttribute('aria-label',phone.matches&&slides.length>1?label+'. Слайды меняются автоматически. Пробел — пауза или продолжение, стрелки — выбор слайда.':label);playback();}
 phone.addEventListener('change',configure,{signal});configure();
 gallery.addEventListener('pointerdown',()=>clearTimeout(timer),{signal,passive:true});
 document.addEventListener('pointerup',playback,{signal,passive:true});document.addEventListener('pointercancel',playback,{signal,passive:true});
 video?.addEventListener('loadedmetadata',playback,{signal});
 video?.addEventListener('error',()=>{status.textContent='Видео не загрузилось. Показываем фотографию.';if(current===0&&slides.length>1)select(1);},{signal});
 document.addEventListener('visibilitychange',playback,{signal});
 reducedMotion.addEventListener('change',()=>{manualPlayback=false;clear();playback();},{signal});
 window.addEventListener('pagehide',()=>{clearTimeout(timer);video?.pause();},{signal});window.addEventListener('pageshow',playback,{signal});
 const size=new ResizeObserver(()=>{if(animations.length||drag)clear();});size.observe(gallery);
 signal.addEventListener('abort',()=>{clearTimeout(timer);clear();observer.disconnect();size.disconnect();video?.pause();},{once:true});
 return {playback};
}
