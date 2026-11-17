import { spring, springProgress, springShape } from '../config/spring';
export {pageScrollY,modalScrollLocked} from './modal-scroll-lock.ts';
import {numberToken,textToken} from './design-tokens';
export {numberToken,textToken};
export {isKeyboardActivation} from './interaction-intent';
export const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
let keyboardInput=false;
function setInput(keyboard:boolean){const modality=keyboard?'keyboard':'pointer';if(keyboardInput===keyboard&&document.documentElement.dataset.inputModality===modality)return;keyboardInput=keyboard;document.documentElement.dataset.inputModality=modality;}
addEventListener('keydown',event=>{if(!['Shift','Control','Alt','Meta'].includes(event.key))setInput(true);},{capture:true});
addEventListener('pointerdown',()=>setInput(false),{capture:true,passive:true});
export const instantInteraction=()=>reducedMotion.matches||keyboardInput;
const surfaceShapes=new WeakMap<HTMLElement,Animation>();
export function surfacePose(element:HTMLElement){
  const style=getComputedStyle(element),shell=element.querySelector<HTMLElement>(':scope > .surface-shell');
  return{opacity:style.opacity,transform:style.transform,shapeTransform:shell?getComputedStyle(shell).transform:undefined};
}
export function animateSurface(element: HTMLElement, opening: boolean, current?:ReturnType<typeof surfacePose>, role:"window"|"popover"="window") {
  surfaceShapes.get(element)?.cancel();surfaceShapes.delete(element);
  if (instantInteraction()) return undefined;
  const scale=numberToken(`--${role}-scale`),distance=numberToken(`--${role}-distance`);
  const hidden=new DOMMatrix().translate(0,distance),visible=new DOMMatrix();
  const start=current?new DOMMatrix(current.transform):(opening?hidden:visible),end=opening?visible:hidden;
  const shapeStart=current?.shapeTransform?new DOMMatrix(current.shapeTransform):new DOMMatrix().scale(opening?scale:1);
  const shapeEnd=opening?1:scale;
  const fromOpacity=current?Number(current.opacity):(opening?0:1),toOpacity=opening?1:0;
  const damping=role==='popover'?spring.popoverDamping:spring.windowDamping;
  const strength=numberToken(`--${role}-material-strain`)*(opening?1:-1);
  const mix=(a:number,b:number,p:number)=>a+(b-a)*p;
  const materialFrames:Keyframe[]=[];
  const frames=Array.from({length:spring.samples+1},(_,index)=>{
    const p=index/spring.samples,t=springProgress(p,damping),shape=springShape(p,strength,damping);
    materialFrames.push({offset:p,transform:`scale(${mix(shapeStart.m11,shapeEnd,t)*shape.x},${mix(shapeStart.m22,shapeEnd,t)*shape.y})`});
    return {offset:p,opacity:Math.max(0,Math.min(1,mix(fromOpacity,toOpacity,t))),
      transform:`translate3d(${mix(start.m41,end.m41,t)}px,${mix(start.m42,end.m42,t)}px,0)`};
  });
  const options:KeyframeAnimationOptions={
    duration: numberToken(opening?`--motion-${role}`:'--motion-exit'),
    easing: 'linear',
    fill: opening ? "none" : "forwards",
  };
  const shell=element.querySelector<HTMLElement>(':scope > .surface-shell');
  const material=shell?.animate(materialFrames,options);
  if(material)surfaceShapes.set(element,material);
  const animation=element.animate(frames,options);
  void animation.finished.catch(()=>{}).finally(()=>{
    if(material&&surfaceShapes.get(element)===material){material.cancel();surfaceShapes.delete(element);}
  });
  return animation;
}
const windows = new Map<HTMLDialogElement, Animation>();
const dialogOwners=new WeakMap<HTMLDialogElement,{open:()=>void;close:(immediate:boolean)=>Promise<void>}>();
export function registerDialogMotion(dialog:HTMLDialogElement,owner:{open:()=>void;close:(immediate:boolean)=>Promise<void>}){dialogOwners.set(dialog,owner);}
export function openDialog(dialog: HTMLDialogElement) {
  const owner=dialogOwners.get(dialog);if(owner){owner.open();return;}
  const current=windows.has(dialog)?surfacePose(dialog):undefined;
  windows.get(dialog)?.cancel();
  windows.delete(dialog);
  if (!dialog.open) dialog.showModal();
  const animation = animateSurface(dialog, true,current);
  if (!animation) return;
  windows.set(dialog, animation);
  void animation.finished
    .catch(() => {})
    .finally(() => {
      if (windows.get(dialog) === animation) windows.delete(dialog);
    });
}
export async function closeDialog(
  dialog: HTMLDialogElement,
  immediate = false,
) {
  const owner=dialogOwners.get(dialog);if(owner){await owner.close(immediate);return;}
  const current=windows.has(dialog)?surfacePose(dialog):undefined;
  windows.get(dialog)?.cancel();
  windows.delete(dialog);
  if (!dialog.open) return;
  if (immediate || instantInteraction()) {
    dialog.close();
    return;
  }
  const animation = animateSurface(dialog, false,current)!;
  windows.set(dialog, animation);
  try {
    await animation.finished;
    if (windows.get(dialog) === animation) dialog.close();
  } catch {
    /* A newer action owns this window. */
  } finally {
    if (windows.get(dialog) === animation) windows.delete(dialog);
    animation.cancel();
  }
}
reducedMotion.addEventListener("change", () => {
  if (reducedMotion.matches)
    for (const animation of windows.values()) animation.finish();
});
