import {observeRail,connectRailControls,enableRailCardSelection} from './rail-selection.ts';
import {enableRailMouseDrag} from './native-rail-drag.ts';
import {updateReadingEdges} from './reading-edges.ts';
import {labelReadingButton} from './reading-preview.ts';
import {beginReadingTransition} from './reading-transition.ts';
import {pageScrollY} from './modal-scroll-lock.ts';

// Start at the centre when it fits; reserve the final step and readable bottom.
export const aboutStickyTop = (
  height: number,
  viewport: number,
  safeTop: number,
  safeBottom: number,
  lastStep = 0,
) => Math.min(
  Math.max(safeTop, (viewport - height) / 2),
  viewport - height - safeBottom - lastStep,
);

const stack =
  typeof document === "undefined"
    ? null
    : document.querySelector<HTMLElement>("[data-about-stack]");
if (stack) {
  const compact = matchMedia('(max-width:960px)');
  enableRailMouseDrag(stack,compact);
  enableRailCardSelection(stack,'.about-layer',()=>compact.matches,index=>choose(index));
  const cards = [...stack.querySelectorAll<HTMLElement>("[data-about-card]")];
  const layers = [...stack.querySelectorAll<HTMLElement>("[data-about-layer]")];
  const heading = document.querySelector<HTMLElement>("#about-title")!;
  const section = stack.closest<HTMLElement>(".about-section")!;
  const content = [...stack.querySelectorAll<HTMLElement>("[data-about-copy-inner]")];
  function reading(){
    cards.forEach(card=>{
      const expanded=compact.matches&&card.dataset.expanded==='true',prose=card.querySelector<HTMLElement>('.about-prose')!,photo=card.querySelector<HTMLElement>('.about-media')!,button=card.querySelector<HTMLButtonElement>('[data-about-more]')!;
      prose.querySelectorAll<HTMLElement>('[data-reading-rest]').forEach(p=>p.hidden=compact.matches&&!expanded);
      photo.inert=expanded;photo.setAttribute('aria-hidden',String(expanded));
      button.setAttribute('aria-expanded',String(expanded));labelReadingButton(button,expanded);
      prose.tabIndex=expanded&&prose.scrollHeight>prose.clientHeight?0:-1;updateReadingEdges(prose);
    });
  }
  const header = document.querySelector<HTMLElement>(".site-header");
  const mobileNavigation = document.querySelector<HTMLElement>(".mobile-nav");
  const mobileBooking = document.querySelector<HTMLElement>(".mobile-nav-book");
  let frame = 0;
  let depthFrame = 0, visible = false;
  let triggers: number[] = [], surfaceHeight = 1, depthStep = 0;
  const reduced = matchMedia('(prefers-reduced-motion:reduce)');
  const depth = cards.map(() => 1);
  const scheduleDepth = () => {
    if (!compact.matches && section.dataset.stackMode==='stack' && !depthFrame && visible && !document.hidden) depthFrame=requestAnimationFrame(paintDepth);
  };
  function paintDepth() {
    depthFrame=0;
    cards.forEach((card,index)=>{
      let levels=0;
      for(let next=index+1;next<cards.length;next++) levels+=Math.max(0,Math.min(1,(pageScrollY()-triggers[next]+surfaceHeight)/surfaceHeight));
      const value=reduced.matches?1:1-levels*depthStep;
      if(Math.abs(value-depth[index])<.00001)return;
      depth[index]=value;
      card.style.transform=reduced.matches?'none':`translate3d(0,0,0) scale(${value})`;
    });
  }

  const update = () => {
    frame = 0;
    reading();
    if(compact.matches) {
      delete stack.dataset.stackReady;
      delete section.dataset.stackMode;
      cards.forEach(card=>card.style.removeProperty('transform'));
      const heights=cards.map(card=>{
        const media=card.querySelector<HTMLElement>('.about-media')!,copy=card.querySelector<HTMLElement>('.about-copy')!,inner=card.querySelector<HTMLElement>('.about-copy-inner')!,style=getComputedStyle(copy),cardStyle=getComputedStyle(card);
        const mediaSize=parseFloat(getComputedStyle(media).width);card.style.setProperty('--about-preview-media-height',`${mediaSize}px`);
        return mediaSize+['h3','.about-prose p','[data-about-more]'].reduce((sum,selector)=>sum+parseFloat(getComputedStyle(card.querySelector<HTMLElement>(selector)!).height),0)+parseFloat(getComputedStyle(inner).gap)*2+parseFloat(style.paddingTop)+parseFloat(style.paddingBottom)+parseFloat(cardStyle.paddingTop)+parseFloat(cardStyle.paddingBottom);
      });
      const height=`${Math.max(...heights)}px`;if(stack.style.getPropertyValue('--about-compact-height')!==height)stack.style.setProperty('--about-compact-height',height);
      return;
    }
    const style = getComputedStyle(stack);
    const gap = parseFloat(style.getPropertyValue("--about-safe-gap"));
    const step = parseFloat(style.getPropertyValue("--about-stack-step"));
    const viewport = window.innerHeight;
    const headerTop =
      header && header.offsetHeight
        ? header.offsetHeight + parseFloat(getComputedStyle(header).top)
        : 0;
    const navigationTop = Math.min(
      ...[mobileNavigation, mobileBooking]
        .filter((element): element is HTMLElement => !!element?.offsetHeight)
        .map((element) => element.getBoundingClientRect().top),
      viewport,
    );
    const bottom = viewport - navigationTop + gap;
    const copyHeight = Math.max(...content.map((element) => {
      const padding = getComputedStyle(element.parentElement!);
      return parseFloat(getComputedStyle(element).height)
        + parseFloat(padding.paddingTop) + parseFloat(padding.paddingBottom);
    }));
    const heightValue = `${copyHeight}px`;
    if (stack.style.getPropertyValue("--about-copy-height") !== heightValue)
      stack.style.setProperty("--about-copy-height", heightValue);
    const height = Math.max(...cards.map((card) => parseFloat(getComputedStyle(card).height)));
    const lastStep = step * (cards.length - 1);
    stack.style.setProperty("--about-card-height", `${height}px`);
    stack.style.setProperty("--about-card-count", String(cards.length));
    const titleTop = headerTop + gap;
    const headingHeight = heading.getBoundingClientRect().height;
    // A tall card needs normal flow; pinning it above the title hides readable text.
    const canStack=!reduced.matches&&titleTop+headingHeight+gap+height+bottom+lastStep<=viewport;
    section.dataset.stackMode=canStack?'stack':'flow';
    if(!canStack)cards.forEach((card,index)=>{depth[index]=1;card.style.removeProperty('transform');});
    const baseTop = aboutStickyTop(height, viewport, titleTop + headingHeight + gap, bottom, lastStep);
    layers.forEach((layer, index) => {
      layer.style.setProperty("--about-sticky-top", `${baseTop + step * index}px`);
    });
    stack.dataset.stackReady = "true";
    section.style.setProperty("--about-heading-height", `${headingHeight}px`);
    section.style.setProperty("--about-heading-top", `${titleTop}px`);
    // The native sticky heading and final card leave their containers together.
    section.style.setProperty("--about-heading-tail", `${Math.max(0, height + baseTop + lastStep - titleTop - headingHeight)}px`);
    section.dataset.headingReady = "true";
    surfaceHeight=height;
    depthStep=parseFloat(getComputedStyle(stack).getPropertyValue('--about-depth-scale-step'));
    const origin=stack.getBoundingClientRect().top+pageScrollY()+parseFloat(getComputedStyle(stack).paddingTop);
    const rowGap=parseFloat(getComputedStyle(stack).rowGap);
    triggers=layers.map((_,index)=>origin+index*(height+rowGap)-baseTop-step*index);
    scheduleDepth();
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };
  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(schedule);
    // Intrinsic content sizes stay independent of the shared minimum height.
    [...content,...stack.querySelectorAll<HTMLElement>('.about-prose p:first-child,.about-copy h3,[data-about-more]'), heading, header, mobileNavigation, mobileBooking].forEach(
      (element) => {
        if (element) observer.observe(element);
      },
    );
  }
  window.addEventListener("resize", schedule);
  compact.addEventListener('change',schedule);
  window.addEventListener('scroll',scheduleDepth,{passive:true});
  new IntersectionObserver(([entry])=>{
    visible=entry.isIntersecting;
    if(visible)scheduleDepth();
    else {cancelAnimationFrame(depthFrame);depthFrame=0;}
  }).observe(stack);
  reduced.addEventListener('change',()=>{
    if(reduced.matches)cards.forEach((card,index)=>{depth[index]=1;card.style.transform='none';});
    schedule();scheduleDepth();
  });
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){cancelAnimationFrame(depthFrame);depthFrame=0;}
    else scheduleDepth();
  });
  window.visualViewport?.addEventListener("resize", schedule);
  void document.fonts.ready.then(schedule);
  schedule();
  const controls=connectRailControls(stack);
  const choose=observeRail(stack,':scope>.about-layer',index=>controls(index));
  const more=[...stack.querySelectorAll<HTMLButtonElement>('[data-about-more]')];
  for(const button of more)button.addEventListener('click',()=>{
    const card=button.closest<HTMLElement>('.about-card')!,prose=card.querySelector<HTMLElement>('.about-prose')!;
    beginReadingTransition(card,prose,reading);card.dataset.expanded=String(card.dataset.expanded!=='true');prose.scrollTop=0;schedule();
  });
  cards.forEach(card=>{const prose=card.querySelector<HTMLElement>('.about-prose')!;prose.addEventListener('scroll',()=>updateReadingEdges(prose),{passive:true});});

}
