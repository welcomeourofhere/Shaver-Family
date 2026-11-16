import {numberToken as n,reducedMotion,textToken,registerDialogMotion,instantInteraction} from './motion';
import {enableSheetDismiss} from './sheet-gesture';
import {spring,springProgress} from '../config/spring';
import {closePopoversWithin} from './popover';

export type DockItem={action:string;label:string;accessible:string;controls?:string;icon?:'left'|'right';disabled?:boolean;primary?:boolean};
type ButtonPose={rect:DOMRect;opacity:number};
export function createDockSurface(dock:HTMLElement,menu:HTMLDialogElement,perform:(item:DockItem,button:HTMLButtonElement,event:MouseEvent)=>void){
  const compact=matchMedia('(max-width:960px)'),toolbar=dock.querySelector<HTMLElement>('.dock-toolbar')!,shell=dock.querySelector<HTMLElement>('.dock-shell')!,trigger=dock.querySelector<HTMLButtonElement>('[data-open-menu]')!;
  const slots=[...dock.querySelectorAll<HTMLButtonElement>('[data-dock-slot]')],content=menu.querySelector<HTMLElement>(':scope>.surface-viewport')!;
  const home=document.createComment('mobile dock');dock.before(home);content.classList.add('dock-content');content.hidden=true;dock.prepend(content);menu.dataset.dockOwned='true';
  let expanded=false,initialized=false,context:DockItem[]=[],shown:DockItem[]=[],effects:Animation[]=[],revision=0,fitFrame=0,presentKey='';
  const rect=()=>shell.getBoundingClientRect();
  const buttonPoses=()=>new Map<HTMLElement,ButtonPose>([trigger,...slots.filter(button=>!button.hidden)].map(button=>[button,{rect:button.getBoundingClientRect(),opacity:Number(getComputedStyle(button).opacity)}]));
  const cancel=()=>{effects.forEach(effect=>effect.cancel());effects=[];};
  function fit(){
    fitFrame=0;if(!compact.matches){document.documentElement.style.removeProperty('--mobile-nav-space');document.documentElement.style.removeProperty('--dock-live-height');return;}
    const available=toolbar.clientWidth,bottom=n('--dock-bottom'),space=n('--size-12');
    const visible=[...toolbar.querySelectorAll<HTMLButtonElement>('[data-dock-slot]:not([hidden])')],gap=n('--size-8'),side=n('--size-44');
    const widths=visible.map(button=>{const style=getComputedStyle(button);return button.dataset.icon?n('--size-44'):Math.max(n('--size-64'),button.querySelector('span')!.scrollWidth+parseFloat(style.paddingLeft)+parseFloat(style.paddingRight))});
    const preferred=side+gap*visible.length+widths.reduce((sum,width)=>sum+width,0),stacked=preferred>available+.5;
    dock.dataset.stacked=String(stacked);
    toolbar.style.gridTemplateColumns=stacked?`${side}px minmax(0,1fr)`:`${side}px ${widths.map((width,index)=>visible[index].dataset.icon?`${width}px`:`minmax(${width}px,1fr)`).join(' ')}`;
    trigger.style.gridRow=stacked?`1 / span ${visible.length}`:'';
    visible.forEach((button,index)=>{button.style.gridColumn=stacked?'2':'';button.style.gridRow=stacked?String(index+1):'';});
    const style=getComputedStyle(dock),height=toolbar.offsetHeight+parseFloat(style.paddingTop)+parseFloat(style.paddingBottom);
    const rootStyle=document.documentElement.style,heightValue=`${height}px`,spaceValue=`${height+bottom+space}px`;
    if(rootStyle.getPropertyValue('--dock-live-height')!==heightValue)rootStyle.setProperty('--dock-live-height',heightValue);
    if(rootStyle.getPropertyValue('--mobile-nav-space')!==spaceValue)rootStyle.setProperty('--mobile-nav-space',spaceValue);
  }
  const schedule=()=>{if(!fitFrame)fitFrame=requestAnimationFrame(fit)};
  function morph(before:DOMRect,oldButtons:Map<HTMLElement,ButtonPose>,immediate=false,duration=n('--motion-context')){
    const turn=++revision;cancel();
    if(immediate||instantInteraction()||!compact.matches)return;
    const after=rect();
    const sx=before.width/after.width,sy=before.height/after.height,radius=n('--radius-card');
    const dockStyle=getComputedStyle(dock),minimum=(toolbar.offsetHeight+parseFloat(dockStyle.paddingTop)+parseFloat(dockStyle.paddingBottom))/after.height;
    const shape=Array.from({length:spring.samples+1},(_,i)=>{
      const p=springProgress(i/spring.samples,spring.windowDamping),x=sx+(1-sx)*p,y=Math.max(minimum,sy+(1-sy)*p);
      return {transformOrigin:'bottom left',transform:`translate(${(before.left-after.left)*(1-p)}px,${(before.bottom-after.bottom)*(1-p)}px) scale(${x},${y})`,borderRadius:`${radius/x}px / ${radius/y}px`};
    });
    effects.push(shell.animate(shape,{duration,easing:'linear'}));
    for(const button of [trigger,...slots.filter(button=>!button.hidden)]){
      const pose=oldButtons.get(button),previous=pose?.rect,next=button.getBoundingClientRect(),targetOpacity=Number(getComputedStyle(button).opacity);
      if(previous){
        const frames=Array.from({length:spring.samples+1},(_,i)=>{
          const p=Math.max(0,Math.min(1,springProgress(i/spring.samples,spring.windowDamping)));
          return {transformOrigin:'top left',transform:`translate(${(previous.left-next.left)*(1-p)}px,${(previous.top-next.top)*(1-p)}px) scale(${1+(previous.width/next.width-1)*(1-p)},${1+(previous.height/next.height-1)*(1-p)})`,opacity:pose!.opacity+(targetOpacity-pose!.opacity)*p};
        });
        effects.push(button.animate(frames,{duration,easing:'linear'}));
      }
      else effects.push(button.animate([{opacity:0,transform:`translateY(${n('--size-8')}px)`},{opacity:targetOpacity,transform:'none'}],{duration,easing:'linear'}));
    }
    void Promise.allSettled(effects.map(effect=>effect.finished)).then(()=>{if(turn===revision)effects=effects.filter(effect=>effect.playState==='running');});
  }
  function present(items:DockItem[],immediate=false){
    const key=items.map(item=>[item.action,item.label,item.accessible,item.controls,item.icon,item.disabled,item.primary].join('|')).join(';')+expanded;
    if(key===presentKey)return;presentKey=key;
    const focused=dock.contains(document.activeElement)?document.activeElement as HTMLElement:null;
    const focusedAction=focused instanceof HTMLButtonElement&&slots.includes(focused)?focused.dataset.action:undefined;
    const animated=!immediate&&!instantInteraction()&&compact.matches;
    const before=animated?rect():undefined,old=animated?buttonPoses():new Map<HTMLElement,ButtonPose>();
    const free=new Set(slots),ordered:HTMLButtonElement[]=[];
    items.forEach(item=>{const same=slots.find(button=>free.has(button)&&button.dataset.action===item.action)||slots.find(button=>free.has(button)&&/booking$/.test(item.action)&&/booking$/.test(button.dataset.action||''));if(same){ordered.push(same);free.delete(same);}else ordered.push(null as unknown as HTMLButtonElement)});
    items.forEach((_,index)=>{if(!ordered[index]){const button=free.values().next().value!;ordered[index]=button;free.delete(button);}});
    slots.forEach(button=>{button.hidden=true;button.removeAttribute('data-dock-primary');button.removeAttribute('data-dock-secondary');button.classList.remove('mobile-nav-book','dock-secondary');});
    shown=items;
    const primaryIndex=items.findIndex(item=>item.primary),entrances:HTMLElement[]=[];
    ordered.forEach((button,index)=>{
      const item=items[index],span=button.querySelector('span')!,changed=button.dataset.action!==item.action||button.dataset.icon!==item.icon||span.textContent!==item.label;button.hidden=false;button.dataset.action=item.action;button.dataset.displayIndex=String(index);button.dataset.uiKind=item.controls?'filled':'selection';
      button.disabled=item.disabled??false;
      if(item.icon)button.dataset.icon=item.icon;else delete button.dataset.icon;
      if(span.textContent!==item.label)span.textContent=item.label;
      if(changed)entrances.push(item.icon?button.querySelector<HTMLElement>(`.dock-arrow-${item.icon}`)!:span);
      button.setAttribute('aria-label',item.accessible);if(item.controls){button.setAttribute('aria-controls',item.controls);button.setAttribute('aria-haspopup','dialog')}else{button.removeAttribute('aria-controls');button.removeAttribute('aria-haspopup')}
      const primary=index===(primaryIndex<0?items.length-1:primaryIndex);button.classList.toggle('mobile-nav-book',primary);button.classList.toggle('dock-secondary',!primary);button.toggleAttribute(primary?'data-dock-primary':'data-dock-secondary',true);
    });
    [trigger,...ordered,...free].forEach((button,index)=>{if(toolbar.children[index]!==button)toolbar.insertBefore(button,toolbar.children[index]??null)});
    if(focusedAction){
      const target=ordered.find(button=>button.dataset.action===focusedAction&&!button.disabled)
        ||(/booking$/.test(focusedAction)?ordered.find(button=>/booking$/.test(button.dataset.action||'')&&!button.disabled):undefined)
        ||trigger;
      if(target!==document.activeElement)target.focus({preventScroll:true});
    }else if(focused&&!focused.hidden&&focused!==document.activeElement)focused.focus({preventScroll:true});
    dock.dataset.actionCount=String(items.length);fit();
    if(animated)morph(before!,old);else{++revision;cancel();}
    if(!immediate&&!instantInteraction())for(const visual of entrances){
      visual.getAnimations().forEach(animation=>animation.cancel());
      const frames=Array.from({length:spring.samples+1},(_,i)=>{const p=Math.max(0,Math.min(1,springProgress(i/spring.samples,spring.windowDamping)));return{opacity:p,transform:`scale(${.88+.12*p})`};});
      effects.push(visual.animate(frames,{duration:n('--motion-context'),easing:'linear'}));
    }
  }
  async function close(immediate=false){
    if(!expanded&&!menu.open)return;
    const before=rect(),old=buttonPoses();
    const panelWidth=content.getBoundingClientRect().width,opacity=getComputedStyle(content).opacity,toolbarHeight=toolbar.offsetHeight,gap=n('--size-8'),duration=n('--motion-dock-exit');
    closePopoversWithin(content);
    expanded=false;dock.dataset.expanded='false';trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-label','Разделы сайта');
    content.inert=true;content.style.cssText=`position:absolute;bottom:${toolbarHeight+gap}px;left:${gap}px;width:${panelWidth}px;pointer-events:none`;
    // The target is neutral; FLIP carries the released sheet offset into the shrinking material.
    home.after(dock);dock.style.removeProperty('translate');menu.close();presentKey='';present(context,true);morph(before,old,immediate,duration);
    if(!immediate&&!instantInteraction()){const fade=content.animate([{opacity},{opacity:0}],{duration:n('--motion-ui'),easing:textToken('--ease-out')});effects.push(fade);try{await fade.finished}catch{}}
    if(!expanded){content.hidden=true;content.inert=false;content.style.cssText='';dock.style.removeProperty('translate');}
    if(compact.matches&&!document.querySelector('dialog:modal'))trigger.focus({preventScroll:true});
  }
  function open(){
    if(expanded||!compact.matches)return;
    const before=rect(),old=buttonPoses(),duration=n('--motion-dock');
    expanded=true;dock.dataset.expanded='true';content.hidden=false;content.inert=false;content.style.cssText='';menu.append(dock);menu.showModal();
    trigger.setAttribute('aria-expanded','true');trigger.setAttribute('aria-label','Закрыть меню');presentKey='';present([{action:'booking',label:'Записаться',accessible:'Записаться онлайн',controls:'booking-drawer'}],true);morph(before,old,false,duration);
    if(!instantInteraction())effects.push(content.animate([{opacity:0,translate:`0 ${n('--size-8')}px`},{opacity:1,translate:'0 0'}],{duration,easing:textToken('--ease-out')}));
    content.querySelector<HTMLElement>('#menu-title')?.focus({preventScroll:true});
  }
  registerDialogMotion(menu,{open,close});enableSheetDismiss(dock,()=>close());
  menu.addEventListener('cancel',event=>{event.preventDefault();void close()});menu.addEventListener('click',event=>{if(event.target===menu)void close()});
  slots.forEach(button=>button.addEventListener('click',event=>{const item=shown[Number(button.dataset.displayIndex)];if(item)perform(item,button,event);}));
  const sizes=new ResizeObserver(schedule);sizes.observe(dock);sizes.observe(toolbar);slots.forEach(button=>sizes.observe(button.querySelector('span')!));
  addEventListener('resize',schedule);compact.addEventListener('change',()=>{if(!compact.matches)void close(true);fit()});
  void document.fonts.ready.then(schedule);
  reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)cancel()});
  return {setActions(items:DockItem[]){context=items;if(!expanded)present(items,!initialized);initialized=true;},isOpen:()=>expanded,fit:schedule};
}
