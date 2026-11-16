import { animateSurface, surfacePose, reducedMotion, numberToken } from './motion';
import {requestFeedback} from './feedback';
import {isMousePointer} from './interaction-intent';

const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
const closers = new Map<HTMLDetailsElement, () => void>();
for (const menu of document.querySelectorAll<HTMLDetailsElement>('.header-menu')) {
  const trigger = menu.querySelector<HTMLElement>('summary')!;
  const panel = menu.querySelector<HTMLElement>('.header-menu-panel')!;
  const capsule = menu.closest<HTMLElement>('.header-capsule')!;
  let wanted = menu.open, revision = 0, animation: Animation | undefined;
  let closeTimer: ReturnType<typeof setTimeout> | undefined;
  let restoringFocus = false;
  let pointerType = 'mouse';
  const cancelClose = () => clearTimeout(closeTimer);
  function placePanel() {
    const button=trigger.getBoundingClientRect(),shell=capsule.getBoundingClientRect();
    const scale=shell.width/capsule.offsetWidth,edge=numberToken('--size-8');
    const start=(button.left-shell.left)/scale,end=(button.right-shell.left)/scale;
    const preferred=menu.classList.contains('header-contact')?end-panel.offsetWidth:start;
    const left=Math.max(edge,Math.min(capsule.offsetWidth-panel.offsetWidth-edge,preferred));
    panel.style.setProperty('--material-max-height',`max(${numberToken('--control-hit')}px, calc((100dvh - ${shell.bottom+numberToken('--size-16')}px) / ${scale} - ${edge}px))`);
    panel.style.left=`${left}px`;panel.style.right='auto';
    panel.style.transformOrigin=`${Math.max(0,Math.min(panel.offsetWidth,(start+end)/2-left))}px 0px`;
  }
  async function setOpen(open: boolean) {
    cancelClose();
    if (open === wanted) return;
    wanted = open;
    const current = ++revision;
    const pose = animation ? surfacePose(panel) : undefined;
    animation?.cancel();
    if (open) {
      menu.open = true;
      placePanel();
    }
    animation = animateSurface(panel, open, pose, 'popover');
    try { await animation?.finished; } catch { return; }
    if (current === revision) {
      if (!open) menu.open = false;
      animation?.cancel();
      animation = undefined;
    }
  }
  const open = () => {
    for (const [other, close] of closers) if (other !== menu) close();
    void setOpen(true);
  };
  const closeLater = () => {
    cancelClose();
    closeTimer = setTimeout(() => {
      const keyboardFocus = menu.contains(document.activeElement) && document.activeElement?.matches(':focus-visible');
      if (!menu.matches(':hover') && !capsule.matches(':hover') && !keyboardFocus) void setOpen(false);
    }, numberToken('--header-menu-close-delay'));
  };
  closers.set(menu, () => { void setOpen(false); });
  menu.addEventListener('pointerenter', event => {
    if (isMousePointer(event) && finePointer.matches) open();
  });
  menu.addEventListener('pointerleave', event => {
    if (isMousePointer(event)) closeLater();
  });
  capsule.addEventListener('pointerleave',event=>{
    if(isMousePointer(event))closeLater();
  });
  menu.addEventListener('focusin', event => {
    if (!restoringFocus && (event.target as Element).matches(':focus-visible')) {
      open();
    }
  });
  menu.addEventListener('focusout', () => {
    queueMicrotask(() => { if (!menu.contains(document.activeElement)) closeLater(); });
  });
  trigger.addEventListener('pointerdown', event => { pointerType = isMousePointer(event)?'mouse':event.pointerType; });
  trigger.addEventListener('keydown',event=>{
    if(event.key!=='ArrowDown'||!panel.querySelector('a[href],button:not(:disabled)'))return;
    event.preventDefault();
    const previous=wanted;
    open();
    [...panel.querySelectorAll<HTMLElement>('a[href],button:not(:disabled)')].find(item=>item.getClientRects().length)?.focus({preventScroll:true});
    if(!previous)requestFeedback('open',event);
  });
  trigger.addEventListener('click', event => {
    if (event.defaultPrevented) return;
    event.preventDefault();
    const previous=wanted;
    if (finePointer.matches && event.detail > 0 && pointerType === 'mouse') open();
    else if (wanted) void setOpen(false);
    else open();
    if(previous!==wanted)requestFeedback(wanted?'open':'close',event);
  });
  panel.addEventListener('click', event => {
    if ((event.target as Element).closest('a')) void setOpen(false);
  });
  document.addEventListener('click', event => {
    if (!menu.contains(event.target as Node)) void setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || !wanted) return;
    void setOpen(false);
    requestFeedback('close',event);
    restoringFocus = true;
    trigger.focus({ preventScroll: true });
    restoringFocus = false;
  });
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) animation?.finish();
  });
  const sizes=new ResizeObserver(() => {
    if (!trigger.getClientRects().length) void setOpen(false);
    else if(wanted)placePanel();
  });
  sizes.observe(trigger);sizes.observe(capsule);sizes.observe(panel);
}
