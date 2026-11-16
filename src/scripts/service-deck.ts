import { numberToken as n, textToken } from "./motion";
import { orderDeck } from "./deck-order";
import {enableHorizontalSwipe} from './horizontal-swipe';
import {setLoading} from './loading';
for (const deck of document.querySelectorAll<HTMLElement>(
  "[data-service-deck]",
)) {
  const tabs = [...deck.querySelectorAll<HTMLButtonElement>("[data-sd-tab]")];
  const panels = [...deck.querySelectorAll<HTMLElement>("[data-sd-panel]")];
  const colors = panels.map((panel) => panel.dataset.sdColor!);
  const stack = deck.querySelector<HTMLElement>(".sd-stack")!;
  const reduced = matchMedia("(prefers-reduced-motion:reduce)");
  const compact = matchMedia('(max-width:960px)');
  let dragged:HTMLElement|null=null,dragBase=new DOMMatrix();
  let interrupted=new Set<HTMLElement>();
  let current = 0,
    order = orderDeck(panels.map((_, i) => i), 0, colors),
    animations: Animation[] = [],
    revision = 0;
  for(const panel of panels){
    const stage=panel.querySelector<HTMLElement>('.sd-photo')!;
    let photoRevision=0;
    panel.addEventListener('click',event=>{
      const summary=(event.target as Element).closest('summary');
      // One open row keeps the disclosure affordance visible without growing the card.
      if(summary?.parentElement instanceof HTMLDetailsElement && summary.parentElement.open) event.preventDefault();
    });
    const syncPhoto=(row:HTMLDetailsElement)=>{
      const turn=++photoRevision;
      if(compact.matches){setLoading(stage,false);return;}
      const previous=stage.querySelector<HTMLImageElement>('[data-photo-current="true"]')!;
      if(previous.getAttribute('src')===row.dataset.photoSrc){setLoading(stage,false);return;}
      setLoading(stage,true);
      const image=new Image();image.className='photo-image';image.alt=row.dataset.photoAlt!;
      image.sizes=previous.sizes;image.srcset=row.dataset.photoSrcset!;image.src=row.dataset.photoSrc!;
      image.decoding='async';
      void image.decode().then(()=>{
        if(turn!==photoRevision)return;
        stage.append(image);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          if(turn!==photoRevision){image.remove();return;}
          for(const old of stage.querySelectorAll('img'))old.setAttribute('data-photo-current',String(old===image));
          window.setTimeout(()=>{for(const old of stage.querySelectorAll('img'))if(old!==image&&old.dataset.photoCurrent!=='true')old.remove();},n('--motion-photo'));
        }));
      }).catch(()=>{/* Keep the decoded photograph when a replacement is unavailable. */}).finally(()=>{if(turn===photoRevision)setLoading(stage,false);});
    };
    panel.addEventListener('toggle',event=>{if(event.target instanceof HTMLDetailsElement&&event.target.open)syncPhoto(event.target)},true);
    compact.addEventListener('change',()=>{const row=panel.querySelector<HTMLDetailsElement>('.sd-service[open]');if(row)syncPhoto(row)});
  }
  function settle() {
    animations.forEach((a) => a.cancel());
    animations = [];
    deck.dataset.deckMoving='false';
    panels.forEach((p) => p.classList.remove("is-leaving"));
    panels.forEach(panel=>{panel.style.removeProperty('transform');panel.style.removeProperty('opacity');panel.style.zIndex=String(panels.length-Number(panel.style.getPropertyValue('--card-level')));});
  }
  function select(requested: number, focus = false, throwX=0) {
    const next = (requested + tabs.length) % tabs.length;
    if (next === current) {
      if (focus) tabs[next].focus({ preventScroll: true });
      return;
    }
    const poses=panels.map(p=>{const s=getComputedStyle(p);return{transform:s.transform,opacity:s.opacity,leaving:p.classList.contains('is-leaving')||interrupted.has(p)}});
    const previous = current,
      turn = ++revision;
    settle();
    // A thrown compact card goes to the back, so repeated gestures visit the whole stack.
    order = throwX && compact.matches ? [...order.slice(1), order[0]] : orderDeck(order, next, colors);
    current = next;
    panels[next].querySelector<HTMLDetailsElement>('.sd-service')!.open=true;
    panels.forEach((panel, i) => {
      const level = order.indexOf(i);
      panel.style.setProperty("--card-level", String(level));
      panel.style.zIndex = String(panels.length - level);
      panel.querySelector<HTMLElement>(".sd-face")!.inert = i !== next;
      panel.setAttribute("aria-hidden", String(i !== next));
    });
  tabs.forEach((tab, i) => {
      tab.setAttribute("aria-selected", String(i === next));
      tab.tabIndex = i === next ? 0 : -1;
    });
    if (focus) tabs[next].focus({ preventScroll: true });
    const rail = tabs[next].parentElement!;
    const tabRect = tabs[next].getBoundingClientRect(),
      railRect = rail.getBoundingClientRect();
    if (tabRect.left < railRect.left)
      rail.scrollLeft -= railRect.left - tabRect.left;
    else if (tabRect.right > railRect.right)
      rail.scrollLeft += tabRect.right - railRect.right;
    if (focus || reduced.matches) return;
    deck.dataset.deckMoving='true';
    panels[previous].classList.add("is-leaving");
    if(throwX)panels[previous].style.zIndex=String(panels.length+1);
    animations = panels.map((panel, i) =>
      panel.animate(
        [
          { transform:poses[i].leaving&&i!==previous?getComputedStyle(panel).transform:poses[i].transform,opacity:poses[i].leaving&&i!==previous?0:Number(poses[i].opacity) },
          { transform:throwX&&i===previous?`translate3d(${Math.sign(throwX)*stack.clientWidth*1.3}px,${n('--size-24')}px,0) rotate(${Math.sign(throwX)*12}deg)`:getComputedStyle(panel).transform,opacity:throwX&&i===previous?0:1 },
        ],
        { duration: n("--motion-card"), easing: textToken("--ease-spring") },
      ),
    );
    interrupted.clear();
    void Promise.allSettled(animations.map((a) => a.finished)).then(() => {
      if (turn === revision) settle();
    });
  }
  function returnDeck(){
    const poses=panels.map(panel=>({transform:getComputedStyle(panel).transform,opacity:getComputedStyle(panel).opacity})),turn=++revision;settle();dragged=null;interrupted.clear();
    if(reduced.matches)return;
    deck.dataset.deckMoving='true';
    animations=panels.map((panel,i)=>panel.animate([{transform:poses[i].transform,opacity:poses[i].opacity},{transform:getComputedStyle(panel).transform,opacity:1}],{duration:n('--motion-card'),easing:textToken('--ease-spring')}));
    void Promise.allSettled(animations.map(animation=>animation.finished)).then(()=>{if(turn===revision)settle();});
  }
  enableHorizontalSwipe(stack,direction=>{select(compact.matches?order[1]:current+direction,false,-direction);dragged=null;},{enabled:()=>compact.matches,motion:{
    start(){const poses=panels.map(panel=>({transform:getComputedStyle(panel).transform,opacity:getComputedStyle(panel).opacity,leaving:panel.classList.contains('is-leaving')}));interrupted=new Set(panels.filter((_,i)=>poses[i].leaving));++revision;settle();deck.dataset.deckMoving='true';panels.forEach((panel,i)=>{if(poses[i].leaving&&i!==current){panel.style.opacity='0';return;}panel.style.transform=poses[i].transform;panel.style.opacity=poses[i].opacity;});dragged=panels[current];dragBase=new DOMMatrix(poses[current].transform);},
    move(dx){if(dragged)dragged.style.transform=dragBase.translate(dx,Math.abs(dx)*.035,0).rotate(0,0,dx/stack.clientWidth*12).toString();},
    cancel:returnDeck,
  }});
  panels.forEach((panel,i)=>panel.addEventListener("click",()=>{if(i!==current)select(i);}));
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(i));
    tab.addEventListener("keydown", (event) => {
      const next =
        event.key === "ArrowRight"
          ? current + 1
          : event.key === "ArrowLeft"
            ? current - 1
            : event.key === "Home"
              ? 0
              : event.key === "End"
                ? tabs.length - 1
                : null;
      if (next === null) return;
      event.preventDefault();
      select(next, true);
    });
  });
  reduced.addEventListener("change", () => {
    if (reduced.matches) {
      ++revision;
      settle();
    }
  });
}
