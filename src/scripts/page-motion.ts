import { numberToken as n, textToken, reducedMotion,pageScrollY } from "./motion";
import './page-scroll';
import { spring, springProgress, springShape } from '../config/spring';

const actors:HTMLElement[]=[];
const live=new Map<HTMLElement,Animation>();
for(const section of document.querySelectorAll<HTMLElement>('main>section:not(#top)')){
  const heading=section.querySelector<HTMLElement>('.section-title');
  const content=section.querySelector<HTMLElement>('.sd-stack,.of-slider,.team-grid,.works-fan,.visit-ticket,.about-stack,.gifts-layout,.reviews-board,.faq-list,.contact-layout');
  for(const [index,item] of [heading,content].entries())if(item){
    item.dataset.revealIndex=String(index);
    item.dataset.revealMode=item===heading&&section.id!=='about'?'move':'fade';
    if(item.dataset.revealMode==='move')item.classList.add('reveal-move');
    actors.push(item);
  }
}
function reveal(item:HTMLElement,animate:boolean){
  if(item.dataset.revealed)return;
  item.dataset.revealed='true';delete item.dataset.revealPending;
  if(!animate||reducedMotion.matches)return;
  const move=item.dataset.revealMode==='move';
  const frames=move?[{opacity:.2,transform:`translate3d(calc(-1 * ${textToken('--reveal-distance')}),0,0)`},{opacity:1,transform:'translate3d(0,0,0)'}]:[{opacity:.2},{opacity:1}];
  const a=item.animate(frames,{duration:n('--motion-reveal'),delay:Number(item.dataset.revealIndex)*n('--reveal-stagger'),easing:textToken('--ease-out'),fill:'backwards'});
  live.set(item,a);void a.finished.catch(()=>{}).finally(()=>live.delete(item));
}
if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{
    for(const entry of entries)if(entry.isIntersecting||entry.boundingClientRect.bottom<0){reveal(entry.target as HTMLElement,entry.boundingClientRect.bottom>0);observer.unobserve(entry.target);}
  },{rootMargin:`0px 0px -${textToken('--reveal-margin')} 0px`,threshold:0});
  for(const actor of actors){
    const r=actor.getBoundingClientRect();
    if(r.top<innerHeight&&r.bottom>0||r.bottom<=0)reveal(actor,false);
    else {actor.dataset.revealPending='true';observer.observe(actor);}
  }
  const revealTarget=(target:Element|null)=>{
    const section=target?.closest('main>section');
    for(const actor of actors)if(section?.contains(actor)){live.get(actor)?.cancel();reveal(actor,false);observer.unobserve(actor);}
  };
  document.addEventListener('focusin',event=>revealTarget(event.target instanceof Element?event.target:null));
  document.addEventListener('pointerdown',event=>revealTarget(event.target instanceof Element?event.target:null),{passive:true});
  const hash=()=>{try{revealTarget(document.getElementById(decodeURIComponent(location.hash.slice(1))))}catch{}};
  addEventListener('hashchange',hash);hash();
  reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)for(const actor of actors){live.get(actor)?.cancel();reveal(actor,false);observer.unobserve(actor);}});
}
const raySurfaces = document.querySelectorAll<HTMLElement>('.cashback-surface,.visit-surface');
const visibleRaySurfaces = new Set<Element>();
function updateRays() {
  for (const surface of raySurfaces)
    surface.querySelector('.soyuz-rays')?.classList.toggle('is-running',visibleRaySurfaces.has(surface) && !document.hidden);
}
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) visibleRaySurfaces.add(entry.target);
      else visibleRaySurfaces.delete(entry.target);
    }
    updateRays();
  });
  raySurfaces.forEach(surface => observer.observe(surface));
} else {
  raySurfaces.forEach(surface => visibleRaySurfaces.add(surface));
  updateRays();
}
document.addEventListener('visibilitychange',updateRays);

// Only the header follows scroll direction. The mobile navigation stays fixed.
const header = document.querySelector<HTMLElement>(".site-header")!;
const headerShape=header.querySelector<HTMLElement>('.header-shape')!;
let shapeAnimation:Animation|undefined;
function setHeaderHidden(hidden:boolean){
  if(header.classList.contains('is-hidden')===hidden)return;
  const from=new DOMMatrix(getComputedStyle(headerShape).transform);
  shapeAnimation?.cancel();
  header.classList.toggle('is-hidden',hidden);
  if(reducedMotion.matches||!header.offsetWidth)return;
  const damping=hidden?spring.popoverDamping:spring.windowDamping;
  const strength=n('--header-material-strain')*(hidden?-1:1);
  // Aspect weighting keeps the long capsule inside its gutters while it breathes.
  const weight=headerShape.offsetHeight/headerShape.offsetWidth/n('--golden-ratio');
  const frames=Array.from({length:spring.samples+1},(_,index)=>{
    const p=index/spring.samples,t=springProgress(p,damping),shape=springShape(p,strength,damping,weight);
    return {offset:p,transform:`scale(${(from.m11+(1-from.m11)*t)*shape.x},${(from.m22+(1-from.m22)*t)*shape.y})`};
  });
  shapeAnimation=headerShape.animate(frames,{duration:n(hidden?'--motion-header-exit':'--motion-header-enter'),easing:'linear'});
}
reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)shapeAnimation?.finish();});
let hideAfter = n("--header-hide-after"),
  hideTravel = n("--header-hide-travel"),
  showTravel = n("--header-show-travel"),
  noise = n("--header-scroll-noise");
const floatExit=n("--header-float-exit");
const floatEnter=n('--header-float-enter');
let shadowBackground='';
function updateHeaderShadow() {
  if (!header.offsetWidth || document.querySelector('dialog[open]')) return;
  const bounds=header.querySelector<HTMLElement>('.header-capsule')!.getBoundingClientRect();
  const behind=document.elementsFromPoint(bounds.left+bounds.width/2,bounds.top+bounds.height/2);
  for(const element of behind) {
    if(header.contains(element)) continue;
    const surface=element.closest<HTMLElement>('[data-selection-surface]');
    const tone=surface?.dataset.selectionSurface;
    const color=tone&&['red','blue','yellow','ink'].includes(tone)
      ? getComputedStyle(surface!).getPropertyValue(`--${tone}`).trim()
      : getComputedStyle(element).backgroundColor;
    if(color==='transparent'||color==='rgba(0, 0, 0, 0)') continue;
    if(color!==shadowBackground) {
      shadowBackground=color;
      header.querySelector<HTMLElement>('.header-capsule')!.style.setProperty('--shadow-tint',`color-mix(in srgb,${color} 28%,var(--shadow-base))`);
    }
    break;
  }
}
let previous = pageScrollY(),
  direction = 0,
  travel = 0,
  scheduled = false;
function updateChrome() {
  scheduled = false;
  const current = Math.max(0, pageScrollY()),
    delta = current - previous;
  if(!header.offsetWidth){previous=current;return;}
  const floating=header.classList.contains('is-floating');
  if(current<=floatExit&&floating) header.classList.remove('is-floating');
  else if(current>=floatEnter&&!floating) header.classList.add('is-floating');
  if (Math.abs(delta) > noise) {
    const next = Math.sign(delta);
    travel = next === direction ? travel + Math.abs(delta) : Math.abs(delta);
    direction = next;
  }
  const pinned =
    !!document.querySelector("dialog[open],.header-menu[open]") ||
    (header.contains(document.activeElement) && document.activeElement?.matches(':focus-visible'));
  if (
    pinned ||
    current <= floatExit ||
    (direction < 0 && travel >= showTravel)
  )
    setHeaderHidden(false);
  else if (current > hideAfter && direction > 0 && travel >= hideTravel)
    setHeaderHidden(true);
  previous = current;
  if(!header.classList.contains('is-hidden')) updateHeaderShadow();
}
function schedule() {
  if (!scheduled) {
    scheduled = true;
    requestAnimationFrame(updateChrome);
  }
}
window.addEventListener("scroll", schedule, { passive: true });
window.addEventListener("resize",()=>{hideAfter=n("--header-hide-after");hideTravel=n("--header-hide-travel");showTravel=n("--header-show-travel");noise=n("--header-scroll-noise");schedule();});
document.addEventListener("focusin", schedule);
new MutationObserver(schedule).observe(document.body, {
  subtree: true,
  attributes: true,
  attributeFilter: ["open"],
});
new MutationObserver(schedule).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
updateChrome();
