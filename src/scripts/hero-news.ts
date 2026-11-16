import { numberToken, reducedMotion,textToken } from "./motion";
import { requestFeedback } from "./feedback";
import { validNewsFeed, newsImageURL,compactNewsPlaceholder,type NewsFeed } from "./news";

import {newsActionTone} from "./news-tone";
import {enableHorizontalSwipe} from './horizontal-swipe';
import {isMousePointer,isKeyboardActivation} from './interaction-intent';

const hero = document.querySelector<HTMLElement>(".hero-scene");
if (hero) {
  const rail = hero.querySelector<HTMLElement>(".hero-rail")!;
  const slides = [...hero.querySelectorAll<HTMLElement>(".hero-slide")];
  const bodies = [...hero.querySelectorAll<HTMLElement>(".hero-news-details")];
  const link = hero.querySelector<HTMLAnchorElement>(".hero-news-link")!;
  const position = hero.querySelector<HTMLElement>(".hero-position")!;
  const panel=hero.querySelector<HTMLElement>('.hero-news-panel')!;
  const controls=hero.querySelector<HTMLElement>('[data-rail-controls="hero-news-rail"]')!;
  const steps=[...controls.querySelectorAll<HTMLButtonElement>('[data-rail-step]')];
  steps.forEach(button=>{button.dataset.feedback='manual'});
  const video=hero.querySelector<HTMLVideoElement>('.hero-video')!,compact=matchMedia('(max-width:960px)');
  let newsReady=false;

  const section=hero.closest<HTMLElement>('.hero')!;
  const promoAction=section.querySelector<HTMLButtonElement>('.first-actions .btn')!,promoLabel=promoAction.querySelector<HTMLElement>('.hero-book-long')!;
  let layoutFrame=0;
  const fitMobileHero=()=>{
    layoutFrame=0;
    promoAction.removeAttribute('data-short-label');
    const style=getComputedStyle(promoAction);
    promoAction.toggleAttribute('data-short-label',promoLabel.scrollWidth+parseFloat(style.paddingLeft)+parseFloat(style.paddingRight)>promoAction.parentElement!.clientWidth+.5);
  };
  const scheduleLayout=()=>{if(!layoutFrame)layoutFrame=requestAnimationFrame(fitMobileHero)};
  const layoutSizes=new ResizeObserver(scheduleLayout);
  [promoAction,promoLabel,promoAction.parentElement].forEach(element=>{if(element)layoutSizes.observe(element)});
  addEventListener('resize',scheduleLayout);

  let current = 0, target = 0, timer = 0, visible = false, hovering = false;
  let heroDrag:{base:number;dx:number;neighbor:number}|null=null,swipeAnimations:Animation[]=[];
  function clearSwipe(){swipeAnimations.forEach(animation=>animation.cancel());swipeAnimations=[];slides.forEach(slide=>{for(const key of ['transform','opacity','transition'])slide.style.removeProperty(key)});heroDrag=null;}
  function returnSwipe(){
    if(!heroDrag)return;
    const neighbor=heroDrag.neighbor,sign=heroDrag.dx<0?-1:1,poses=[slides[current],slides[neighbor]].map(slide=>getComputedStyle(slide).transform);
    swipeAnimations.forEach(animation=>animation.cancel());
    if(reducedMotion.matches){clearSwipe();return;}
    const outgoing=slides[neighbor],active=slides[current];
    swipeAnimations=[active.animate([{transform:poses[0]},{transform:'translateX(0)'}],{duration:numberToken('--motion-card'),easing:textToken('--ease-drawer-spring')}),outgoing.animate([{transform:poses[1]},{transform:`translateX(${-sign*rail.clientWidth}px)`}],{duration:numberToken('--motion-card'),easing:textToken('--ease-drawer-spring')})];
    const running=swipeAnimations;
    void Promise.allSettled(running.map(animation=>animation.finished)).then(()=>{if(swipeAnimations===running)clearSwipe()});
  }
  let paused = reducedMotion.matches;
  const lifetime = new AbortController();
  const {signal} = lifetime;

  async function loadImage(index: number) {
    if(compact.matches)return;
    const image = slides[index].querySelector<HTMLImageElement>(".hero-photo");
    if (!image) return;
    image.loading = "eager";
    if (image.getAttribute("src") !== image.dataset.newsSrc) {
      image.srcset = image.dataset.newsSrcset || "";
      image.src = image.dataset.newsSrc!;
    }
    try { await image.decode(); image.hidden = false; }
    catch { image.hidden = true; }
  }
  function schedule() {
    clearTimeout(timer);
    const playing = newsReady && !compact.matches && !paused && !reducedMotion.matches;
    hero!.dataset.heroPaused = String(!playing || !visible || hovering || document.hidden);
    const playVideo=compact.matches&&current===0&&visible&&!paused&&!document.hidden&&!reducedMotion.matches;
    if(playVideo){if(!video.getAttribute('src'))video.src=video.dataset.videoSrc!;void video.play().catch(()=>{/* The poster remains available when autoplay is unavailable. */});}else video.pause();
    position.setAttribute("aria-live", playing ? "off" : "polite");
    if (!playing || !visible || hovering || document.hidden) return;
    void loadImage((current + 1) % slides.length);
    timer = window.setTimeout(() => void select(current + 1), compact.matches&&current===0?Math.max(numberToken('--hero-autoplay-interval'),(video.duration||26.134)*1000):numberToken("--hero-autoplay-interval"));
  }
  function pause() { paused = true; schedule(); }
  function paintControls(){
    const count=controls.querySelector('output')!;
    count.textContent=`${String(current+1).padStart(2,'0')} / ${String(slides.length).padStart(2,'0')}`;
    count.setAttribute('aria-label',`${current+1} из ${slides.length}`);
    controls.querySelectorAll<HTMLElement>('.rail-progress span').forEach((segment,index)=>{segment.hidden=index>=slides.length;segment.dataset.current=String(index===current)});
    steps.forEach(button=>{button.disabled=!newsReady||slides.length<2});
    const tone=newsActionTone(current,slides.length);panel.dataset.newsTone=panel.dataset.selectionSurface=tone;
  }
  const togglePlayback=()=>{paused=!paused;schedule();};
  rail.addEventListener('click',event=>{if(compact.matches&&event.target instanceof Element&&!event.target.closest('button,a')){togglePlayback();requestFeedback('select',event);}},{signal});
  function select(next: number, event?: Event) {
    if(!newsReady)return;
    if (event) pause();
    const index = (next + slides.length) % slides.length;
    target = index;
    if (index === current) { returnSwipe();schedule(); return; }
    clearTimeout(timer);
    // Selection is immediate; decoding belongs to the slide's shared media loader.
    void loadImage(index);
    rail.dataset.selectionInstant=String(reducedMotion.matches||!!event&&isKeyboardActivation(event));
    if (event) requestFeedback("select", event);
    const previous=current,gesture=heroDrag,poses=gesture?[getComputedStyle(slides[current]).transform,getComputedStyle(slides[index]).transform]:[];
    if(!gesture)clearSwipe();
    current = target = index;
    slides.forEach((slide, i) => {
      slide.dataset.heroActive = String(i === index);
      slide.inert = i !== index;
      slide.setAttribute("aria-hidden", String(i !== index));
      bodies[i].dataset.newsActive = String(i === index);
      bodies[i].inert = i !== index;
      bodies[i].setAttribute("aria-hidden", String(i !== index));
    });
    link.href=slides[index].dataset.newsUrl!;
    paintControls();
    position.textContent = `${index + 1} / ${slides.length}`;
    if(gesture){
      swipeAnimations.forEach(animation=>animation.cancel());
      if(reducedMotion.matches)clearSwipe();else{
        const sign=gesture.dx<0?-1:1;
        swipeAnimations=[slides[previous].animate([{transform:poses[0]},{transform:`translateX(${sign*rail.clientWidth}px)`}],{duration:numberToken('--motion-card'),easing:textToken('--ease-drawer-spring')}),slides[index].animate([{transform:poses[1]},{transform:'translateX(0)'}],{duration:numberToken('--motion-card'),easing:textToken('--ease-drawer-spring')})];
        const running=swipeAnimations;heroDrag=null;
        void Promise.allSettled(running.map(animation=>animation.finished)).then(()=>{if(swipeAnimations===running)clearSwipe()});
      }
    }
    schedule();
    void commitFeed();
  }
  steps.forEach(button=>button.addEventListener('click',event=>void select(target+Number(button.dataset.railStep),event),{signal}));
  rail.addEventListener("keydown", event => {
    if(event.code==='Space'&&event.target===rail){event.preventDefault();togglePlayback();requestFeedback('select',event);return;}
    if (!compact.matches && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
      event.preventDefault(); void select(target + (event.key === "ArrowLeft" ? -1 : 1), event);
    }
  }, {signal});
  enableHorizontalSwipe(rail,(direction,event)=>void select(target+direction,event),{signal,enabled:()=>newsReady&&!compact.matches,motion:{
    start(){
      target=current;pause();const poses=slides.map(slide=>({transform:getComputedStyle(slide).transform,opacity:getComputedStyle(slide).opacity}));swipeAnimations.forEach(animation=>animation.cancel());swipeAnimations=[];
      slides.forEach((slide,i)=>{slide.style.transform=poses[i].transform;slide.style.opacity=poses[i].opacity;slide.style.transition='none'});
      const base=new DOMMatrix(poses[current].transform).m41;heroDrag={base,dx:base,neighbor:(current+1)%slides.length};void loadImage((current+1)%slides.length);void loadImage((current+slides.length-1)%slides.length);
    },
    move(dx){if(!heroDrag)return;heroDrag.dx=heroDrag.base+dx;const sign=heroDrag.dx<0?-1:1,index=(current+(sign<0?1:-1)+slides.length)%slides.length;heroDrag.neighbor=index;
      slides.forEach((slide,i)=>{slide.style.opacity=String(i===current||i===index?1:0)});slides[current].style.transform=`translateX(${heroDrag.dx}px)`;slides[index].style.transform=`translateX(${-sign*rail.clientWidth+heroDrag.dx}px)`;
    },cancel:returnSwipe,
  }});
  hero.addEventListener("pointerenter", event => { if (isMousePointer(event)) { hovering = true; schedule(); } }, {signal});
  hero.addEventListener("pointerleave", () => { hovering = false; schedule(); }, {signal});
  hero.addEventListener("focusin", pause, {signal});
  const observer = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting && entry.intersectionRatio >= .5; schedule();
  }, {threshold: [0, .5]});
  observer.observe(hero);
  document.addEventListener("visibilitychange", schedule, {signal});
  reducedMotion.addEventListener("change",()=>{clearSwipe();pause()}, {signal});
  const configureHero=()=>{hero.setAttribute('aria-label',compact.matches?'Видео из барбершопа СОЮЗ':'Публикации СОЮЗа во ВКонтакте');if(compact.matches)hero.removeAttribute('aria-roledescription');else hero.setAttribute('aria-roledescription','карусель');position.hidden=compact.matches;rail.setAttribute('aria-label',compact.matches?'Атмосфера СОЮЗа. Пробел — пауза или продолжение видео.':'Публикации ВК. Стрелки влево и вправо — сменить слайд, пробел — пауза и продолжение');if(compact.matches&&current!==0)void select(0);if(!compact.matches)void loadImage(current);schedule();scheduleLayout();};
  compact.addEventListener('change',configureHero,{signal});configureHero();
  window.addEventListener("pagehide", () => {clearTimeout(timer);video.pause()}, {signal});
  window.addEventListener("pageshow", schedule, {signal});
  document.addEventListener("astro:before-swap", () => { clearTimeout(timer); observer.disconnect(); lifetime.abort(); clearSwipe(); layoutSizes.disconnect();cancelAnimationFrame(layoutFrame);removeEventListener('resize',scheduleLayout); }, {once: true, signal});
  schedule();

  // Public snapshot refresh never interrupts reading, dragging or a focused control.
  const endpoint = hero.dataset.newsFeed;
  let newsTimer=0,newsLoading=false,pendingFeed:{feed:NewsFeed;url:string}|null=null;
  async function commitFeed(){
    if(!pendingFeed||signal.aborted||(newsReady&&(hovering||heroDrag||current!==target||hero!.contains(document.activeElement))))return;
    const {feed,url}=pendingFeed;pendingFeed=null;
    if(Date.parse(feed.generatedAt)<=(Date.parse(hero!.dataset.newsRevision||'')||0))return;
    for (const [index,item] of feed.items.entries()) {
      if(!slides[index]){const slide=document.createElement('article');slide.className='hero-slide photo-frame';slide.setAttribute('data-loading-media','');rail.append(slide);slides.push(slide);}
      if(!bodies[index]){const body=document.createElement('div');body.className='hero-news-details';const text=document.createElement('p');text.setAttribute('data-news-text','');body.append(document.createElement('time'),text);hero!.querySelector('#hero-news-bodies')!.append(body);bodies.push(body);}
      const slide=slides[index],body=bodies[index];slide.dataset.newsId=item.id;
      const active=index===current;slide.dataset.heroActive=body.dataset.newsActive=String(active);slide.inert=body.inert=!active;slide.setAttribute('aria-hidden',String(!active));body.setAttribute('aria-hidden',String(!active));slide.setAttribute('role','group');slide.setAttribute('aria-roledescription','слайд');slide.setAttribute('aria-label',`${index+1} из ${feed.items.length}`);
      body.querySelector('[data-news-text]')!.textContent=item.text;
      const time=body.querySelector('time')!;time.dateTime=item.publishedAt;time.textContent=new Date(item.publishedAt).toLocaleDateString('ru-RU',{day:'numeric',month:'long',year:'numeric',timeZone:'Europe/Moscow'});
      slide.dataset.newsUrl=item.url;
      let image=slide.querySelector<HTMLImageElement>('.hero-photo');
      if(!item.image)image?.remove();else{
        if(!image){image=new Image();image.className='photo-image hero-photo';image.alt='';const picture=document.createElement('picture'),source=document.createElement('source');source.media=compact.media;source.srcset=compactNewsPlaceholder;picture.append(source,image);slide.prepend(picture);}
        image.dataset.newsSrc=newsImageURL(item.image.variants[0].url,url);image.dataset.newsSrcset=item.image.variants.map(v=>`${newsImageURL(v.url,url)} ${v.width}w`).join(', ');
        image.sizes='(max-width:960px) 100vw, 760px';image.width=item.image.variants[0].width;image.height=item.image.variants[0].height;
      }
    }
    hero!.dataset.newsRevision=feed.generatedAt;link.href=slides[current].dataset.newsUrl!;
    await loadImage(current);const restoreFocus=hero!.querySelector('.hero-news-state')!.contains(document.activeElement);newsReady=true;hero!.dataset.newsState='ready';hero!.setAttribute('aria-busy','false');paintControls();position.textContent=`${current+1} / ${slides.length}`;if(restoreFocus)rail.focus({preventScroll:true});schedule();
  }
  function scheduleNews(){clearTimeout(newsTimer);if(endpoint&&!compact.matches&&!document.hidden&&!signal.aborted)newsTimer=window.setTimeout(()=>void refreshNews(),numberToken('--hero-news-refresh-interval'));}
  async function refreshNews(){
    if(!endpoint||compact.matches||newsLoading||signal.aborted)return;newsLoading=true;
    if(!newsReady){if(hero!.querySelector('.hero-news-state')!.contains(document.activeElement))rail.focus({preventScroll:true});hero!.dataset.newsState='pending';hero!.setAttribute('aria-busy','true');hero!.querySelector<HTMLElement>('.hero-news-state [data-loading-indicator]')!.hidden=false;for(const node of hero!.querySelectorAll<HTMLElement>('.hero-news-failure,.hero-news-retry'))node.hidden=true;}
    try {
      for(const source of [endpoint,hero!.dataset.newsFallback].filter((value):value is string=>!!value)){
        const url=new URL(source,location.href);
        if(url.origin!==location.origin&&!(url.protocol==='https:'&&(url.hostname==='raw.githubusercontent.com'||url.hostname==='storage.yandexcloud.net'&&/^\/shaver\/Soyuz\/releases\/[\da-f]{20}\/data\/news\.json$/.test(url.pathname))))continue;
        const request=new AbortController(),abort=()=>request.abort();signal.addEventListener('abort',abort,{once:true});const deadline=setTimeout(abort,numberToken('--hero-news-refresh-timeout'));
        try{
          const response=await fetch(url,{signal:request.signal,credentials:'omit',cache:'no-cache'});if(!response.ok)continue;
          const text=await response.text();if(text.length>200000)continue;
          const feed:unknown=JSON.parse(text);if(!validNewsFeed(feed)||signal.aborted)continue;
          if(Date.parse(feed.generatedAt)<=Math.max(Date.parse(hero!.dataset.newsRevision||'')||0,Date.parse(pendingFeed?.feed.generatedAt||'')||0))return;
          pendingFeed={feed,url:url.href};await commitFeed();return;
        }catch{/* Try the separately fetched local snapshot; no post is embedded in HTML. */}
        finally{clearTimeout(deadline);signal.removeEventListener('abort',abort);}
        if(signal.aborted)return;
      }
    } finally{
      newsLoading=false;scheduleNews();
      if(!newsReady&&!signal.aborted){hero!.dataset.newsState='error';hero!.setAttribute('aria-busy','false');hero!.querySelector<HTMLElement>('.hero-news-state [data-loading-indicator]')!.hidden=true;for(const node of hero!.querySelectorAll<HTMLElement>('.hero-news-failure,.hero-news-retry'))node.hidden=false;}
    }
  }
  hero.addEventListener('pointerleave',()=>void commitFeed(),{signal});
  hero.addEventListener('focusout',()=>queueMicrotask(()=>void commitFeed()),{signal});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clearTimeout(newsTimer);else void refreshNews()},{signal});
  compact.addEventListener('change',()=>{if(compact.matches)clearTimeout(newsTimer);else void refreshNews()},{signal});
  signal.addEventListener('abort',()=>{clearTimeout(newsTimer);pendingFeed=null},{once:true});
  hero.querySelector('.hero-news-retry')!.addEventListener('click',()=>void refreshNews(),{signal});
  if(endpoint)void refreshNews();
}
