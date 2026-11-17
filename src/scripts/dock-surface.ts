import {numberToken as n,reducedMotion,registerDialogMotion,instantInteraction} from './motion';
import {enableSheetDismiss} from './sheet-gesture';
import {spring,boundedSpringProgress,boundedMaterialShape} from '../config/spring';
import {closePopoversWithin} from './popover';
import {modalDialogs} from './modal-scroll-lock';
import {floatingActionTone,type FloatingTone} from './floating-tone';

export type DockItem={action:string;label:string;accessible:string;controls?:string;popup?:boolean;href?:string;icon?:'left'|'right';disabled?:boolean;primary?:boolean;short?:string};
type DockControl=HTMLButtonElement|HTMLAnchorElement;
type MaterialScale={x:number;y:number};
type ButtonPose={rect:DOMRect;opacity:number;skin:MaterialScale};
type DockPose={rect:DOMRect;background:string;radius:number;shadow:string};
export function createDockSurface(dock:HTMLElement,menu:HTMLDialogElement,perform:(item:DockItem,button:HTMLButtonElement,event:MouseEvent)=>void){
  const compact=matchMedia('(max-width:960px)'),toolbar=dock.querySelector<HTMLElement>('.dock-toolbar')!,shell=dock.querySelector<HTMLElement>('.dock-shell')!,trigger=dock.querySelector<HTMLButtonElement>('[data-open-menu]')!;
  const slots=[...dock.querySelectorAll<DockControl>('[data-dock-slot]')],content=menu.querySelector<HTMLElement>(':scope>.surface-viewport')!;
  const notice=dock.querySelector<HTMLElement>('[data-analytics-prompt]');
  const anchor=dock.closest<HTMLElement>('[data-mobile-nav-anchor]')??dock;
  const home=document.createComment('mobile dock');anchor.before(home);content.classList.add('dock-content');content.hidden=true;dock.prepend(content);menu.dataset.dockOwned='true';
  let expanded=false,initialized=false,context:DockItem[]=[],contextSection=dock.dataset.section||'top',contextTone=(dock.dataset.floatingTone||'red')as FloatingTone,shown:DockItem[]=[],effects:Animation[]=[],revision=0,fitFrame=0,presentKey='',noticeRevision=0;
  const pose=():DockPose=>{const rect=shell.getBoundingClientRect(),style=getComputedStyle(shell),radii=style.borderTopLeftRadius.match(/[\d.]+/g)?.map(Number)??[0];return{rect,background:style.backgroundColor,shadow:style.boxShadow,radius:Math.min(rect.width/2,rect.height/2,radii[0]*rect.width/Math.max(1,shell.offsetWidth),(radii[1]??radii[0])*rect.height/Math.max(1,shell.offsetHeight))}};
  const noticeVisible=()=>document.documentElement.dataset.cookiePrompt==='true';
  const noticeMoving=()=>!!notice&&(notice.hasAttribute('data-cookie-exiting')||toolbar.hasAttribute('data-cookie-exiting'));
  const materialPose=(button:HTMLElement):MaterialScale=>{const skin=button.querySelector('.dock-skin'),transform=skin?getComputedStyle(skin).transform:'none',matrix=transform==='none'?new DOMMatrix():new DOMMatrix(transform);return{x:matrix.a,y:matrix.d};};
  const buttonPoses=()=>new Map<HTMLElement,ButtonPose>([trigger,...slots.filter(button=>!button.hidden)].filter(button=>button.getClientRects().length).map(button=>[button,{rect:button.getBoundingClientRect(),opacity:Number(getComputedStyle(button).opacity),skin:materialPose(button)}]));
  const cancel=()=>{if(noticeMoving())for(const element of [notice!,toolbar])element.style.opacity=getComputedStyle(element).opacity;effects.forEach(effect=>effect.cancel());effects=[];};
  function fit(){
    fitFrame=0;if(!compact.matches){document.documentElement.style.removeProperty('--mobile-nav-space');document.documentElement.style.removeProperty('--dock-live-height');return;}
    const bottom=n('--dock-bottom'),space=n('--size-12');
    const visible=[...toolbar.querySelectorAll<DockControl>('[data-dock-slot]:not([hidden])')],gap=n('--size-8'),side=Math.max(n('--size-44'),parseFloat(getComputedStyle(trigger).minHeight));
    const maxWidth=Math.min(n('--content-max')+n('--size-16'),document.documentElement.getBoundingClientRect().width-n('--size-8'));
    const basePad=expanded||!dock.dataset.condensed||dock.dataset.condensed==='false'?n('--size-8'):n('--size-6');
    const inset=(pad:number)=>Math.max(pad,n('--safe-left')-n('--size-4')+pad)+Math.max(pad,n('--safe-right')-n('--size-4')+pad);
    const measure=()=>visible.map(button=>{const style=getComputedStyle(button);return button.dataset.icon?n('--size-44'):Math.max(n('--size-64'),button.querySelector('span')!.scrollWidth+parseFloat(style.paddingLeft)+parseFloat(style.paddingRight))});
    visible.forEach(button=>{const label=button.querySelector('span')!,full=button.dataset.dockLabel;if(full&&label.textContent!==full)label.textContent=full;});
    let widths=measure(),preferred=side+gap*visible.length+widths.reduce((sum,width)=>sum+width,0);
    const targetWidth=expanded||dock.dataset.condensed!=='true'?maxWidth:maxWidth*n('--dock-condensed-ratio');
    if(preferred+inset(basePad)>targetWidth+.5){visible.forEach(button=>{const label=button.querySelector('span')!,short=button.dataset.dockShort;if(short&&label.textContent!==short)label.textContent=short;});widths=measure();preferred=side+gap*visible.length+widths.reduce((sum,width)=>sum+width,0);}
    const stacked=preferred+inset(basePad)>maxWidth+.5,vertical=stacked&&Math.max(...widths,side)+side+gap+inset(n('--size-12'))>maxWidth+.5;
    dock.dataset.stacked=String(stacked);
    const minimum=(stacked?Math.max(...widths,side)+(vertical?0:side+gap):preferred)+inset(stacked?n('--size-12'):basePad);
    dock.style.setProperty('--dock-min-width',`${minimum}px`);
    toolbar.style.gridTemplateColumns=vertical?'minmax(0,1fr)':stacked?`${side}px minmax(0,1fr)`:`${side}px ${widths.map((width,index)=>visible[index].dataset.icon?`${width}px`:`minmax(${width}px,1fr)`).join(' ')}`;
    trigger.style.gridColumn=vertical?'1':'';trigger.style.justifySelf=vertical?'center':'';trigger.style.width=`${side}px`;trigger.style.gridRow=vertical?'1':stacked?`1 / span ${visible.length}`:'';
    visible.forEach((button,index)=>{button.style.gridColumn=vertical?'1':stacked?'2':'';button.style.gridRow=vertical?String(index+2):stacked?String(index+1):'';});
    const style=getComputedStyle(dock),height=(noticeVisible()?notice?.offsetHeight??0:toolbar.offsetHeight)+parseFloat(style.paddingTop)+parseFloat(style.paddingBottom);
    const rootStyle=document.documentElement.style,heightValue=`${height}px`,spaceValue=`${height+bottom+space}px`;
    if(rootStyle.getPropertyValue('--dock-live-height')!==heightValue)rootStyle.setProperty('--dock-live-height',heightValue);
    if(rootStyle.getPropertyValue('--mobile-nav-space')!==spaceValue)rootStyle.setProperty('--mobile-nav-space',spaceValue);
  }
  const schedule=()=>{if(!fitFrame)fitFrame=requestAnimationFrame(fit)};
  function settleNotice(){
    for(const element of [notice,toolbar])if(element){element.removeAttribute('data-cookie-exiting');element.style.removeProperty('position');element.style.removeProperty('left');element.style.removeProperty('bottom');element.style.removeProperty('width');element.style.removeProperty('pointer-events');element.style.removeProperty('opacity');element.inert=false;}
    if(notice)notice.hidden=!noticeVisible();
  }
  function setNotice(visible:boolean,immediate=false){
    if(!notice)return;
    if(visible===noticeVisible()){if(!notice.hasAttribute('data-cookie-exiting'))notice.hidden=!visible;return;}
    ++noticeRevision;const before=pose(),duration=n('--motion-context');
    if(visible&&expanded)void close(true);
    const outgoing=visible?toolbar:notice,incoming=visible?notice:toolbar,from=outgoing.getBoundingClientRect(),opacity=getComputedStyle(outgoing).opacity;
    const incomingOpacity=incoming.getClientRects().length?Number(getComputedStyle(incoming).opacity):0;
    cancel();settleNotice();
    document.documentElement.dataset.cookiePrompt=String(visible);notice.hidden=!visible;
    if(!compact.matches||immediate||instantInteraction()){fit();return;}
    // Keep the released content in its visible pose while this one shell changes shape.
    notice.hidden=false;outgoing.setAttribute('data-cookie-exiting','');outgoing.inert=true;
    const dockRect=dock.getBoundingClientRect();
    outgoing.style.cssText=`position:absolute;left:${from.left-dockRect.left}px;bottom:${dockRect.bottom-from.bottom}px;width:${from.width}px;pointer-events:none;opacity:${opacity}`;
    incoming.style.opacity=String(incomingOpacity);
    fit();morph(before,null,false,duration);
  }
  document.addEventListener('soyuz:analytics-prompt',event=>{event.preventDefault();setNotice((event as CustomEvent<{visible:boolean}>).detail.visible);});
  if(notice)notice.hidden=!noticeVisible();
  function morph(start:DockPose,oldButtons:Map<HTMLElement,ButtonPose>|null,immediate=false,duration=n('--motion-dock-context')){
    const turn=++revision,outgoing=noticeMoving()?(notice!.hasAttribute('data-cookie-exiting')?notice!:toolbar):null,incoming=outgoing?(outgoing===notice?toolbar:notice!):null;
    const outgoingOpacity=outgoing?Number(getComputedStyle(outgoing).opacity):0,incomingOpacity=incoming?Number(getComputedStyle(incoming).opacity):0;
    const controls=[trigger,...slots.filter(button=>!button.hidden)];
    const noticeTurn=outgoing?++noticeRevision:noticeRevision;cancel();
    if(immediate||instantInteraction()||!compact.matches){if(outgoing)settleNotice();return;}
    const before=start.rect,after=shell.getBoundingClientRect();
    const end=pose(),colors=[start.background,end.background].map(value=>{const channels=value.match(/[\d.]+/g)!.map(Number);return[...channels.slice(0,3),channels[3]??1]});
    if(colors[0][3]===0)colors[0].splice(0,3,...colors[1].slice(0,3));if(colors[1][3]===0)colors[1].splice(0,3,...colors[0].slice(0,3));
    const sx=before.width/after.width,sy=before.height/after.height,strength=n('--dock-material-strain'),resized=Math.abs(before.width-after.width)>.5||Math.abs(before.height-after.height)>.5;
    const shape=Array.from({length:spring.samples+1},(_,i)=>{
      const p=boundedSpringProgress(i/spring.samples),x=sx+(1-sx)*p,y=sy+(1-sy)*p;
      const channels=colors[0].map((value,index)=>value+(colors[1][index]-value)*p),radius=start.radius+(end.radius-start.radius)*p;
      return {...(resized?{transformOrigin:'bottom left',transform:`translate(${(before.left-after.left)*(1-p)}px,${(before.bottom-after.bottom)*(1-p)}px) scale(${x},${y})`,borderRadius:`${radius/x}px / ${radius/y}px`}:{}),backgroundColor:`rgba(${channels.join(',')})`,...(i===0?{boxShadow:start.shadow}:i===spring.samples?{boxShadow:end.shadow}:{})};
    });
    effects.push(shell.animate(shape,{duration,easing:'linear'}));
    if(outgoing&&incoming){
      const frames=Array.from({length:spring.samples+1},(_,i)=>boundedSpringProgress(i/spring.samples));
      const fade=outgoing.animate(frames.map(p=>({opacity:outgoingOpacity*(1-p)})),{duration,easing:'linear',fill:'forwards'});
      const reveal=incoming.animate(frames.map(p=>({opacity:incomingOpacity+(1-incomingOpacity)*p})),{duration,easing:'linear',fill:'forwards'});
      effects.push(fade,reveal);
      void fade.finished.then(()=>{if(noticeTurn===noticeRevision){settleNotice();fade.cancel();reveal.cancel();}},()=>{});
    }
    for(const button of controls){
      const pose=oldButtons?.get(button);if(!pose)continue;
      const previous=pose.rect,next=button.getBoundingClientRect(),targetOpacity=Number(getComputedStyle(button).opacity),startSkin=pose.skin;
      if(Math.abs(previous.width-next.width)<=.5&&Math.abs(previous.height-next.height)<=.5)continue;
      {
        const frames=Array.from({length:spring.samples+1},(_,i)=>{
          const p=boundedSpringProgress(i/spring.samples);
          return {transformOrigin:'top left',transform:`translate(${(previous.left-next.left)*(1-p)}px,${(previous.top-next.top)*(1-p)}px) scale(${1+(previous.width/next.width-1)*(1-p)},${1+(previous.height/next.height-1)*(1-p)})`,opacity:pose!.opacity+(targetOpacity-pose!.opacity)*p};
        });
        effects.push(button.animate(frames,{duration,easing:'linear'}));
      }
      for(const visual of button.querySelectorAll<HTMLElement>(':scope>span')){
        const skin=visual.classList.contains('dock-skin');
        const frames=Array.from({length:spring.samples+1},(_,i)=>{
          const progress=i/spring.samples,p=boundedSpringProgress(progress),material=boundedMaterialShape(progress,strength),x=material.x+(startSkin.x-1)*(1-p),y=material.y+(startSkin.y-1)*(1-p);
          const outerX=previous?1+(previous.width/next.width-1)*(1-p):1,outerY=previous?1+(previous.height/next.height-1)*(1-p):1;
          return{transformOrigin:'center',transform:`scale(${skin?x:x/outerX},${skin?y:y/outerY})`};
        });
        effects.push(visual.animate(frames,{duration,easing:'linear'}));
      }
    }
    void Promise.allSettled(effects.map(effect=>effect.finished)).then(()=>{if(turn===revision)effects=effects.filter(effect=>effect.playState==='running');});
  }
  function present(items:DockItem[],immediate=false,section=dock.dataset.section,condensed=dock.dataset.condensed==='true',tone=contextTone){
    const key=items.map(item=>[item.action,item.label,item.accessible,item.controls,item.popup,item.href,item.icon,item.disabled,item.primary,item.short].join('|')).join(';')+expanded+section+condensed+tone;
    if(key===presentKey)return;presentKey=key;
    const focused=dock.contains(document.activeElement)?document.activeElement as HTMLElement:null;
    const focusedAction=(focused instanceof HTMLButtonElement||focused instanceof HTMLAnchorElement)&&slots.includes(focused)?focused.dataset.action:undefined;
    const animated=!immediate&&!instantInteraction()&&compact.matches&&(!noticeVisible()||noticeMoving());
    const before=animated?pose():undefined,old=animated?buttonPoses():new Map<HTMLElement,ButtonPose>();
    if(section)dock.dataset.section=section;dock.dataset.condensed=String(condensed);dock.dataset.floatingTone=tone;dock.dataset.selectionSurface=tone;
    const actionTone=floatingActionTone(tone,expanded);toolbar.dataset.selectionSurface=actionTone;
    for(const role of ['primary','secondary','primary-active','secondary-active'])for(const channel of ['bg','fg'])toolbar.style.setProperty(`--dock-${role}-${channel}`,`var(--dock-${actionTone}-${expanded?'menu':'panel'}-${role}-${channel})`);
    const free=new Set(slots),ordered:DockControl[]=[];
    const compatible=(button:DockControl,item:DockItem)=>item.href?button instanceof HTMLAnchorElement:button instanceof HTMLButtonElement;
    items.forEach(item=>{const same=slots.find(button=>free.has(button)&&compatible(button,item)&&button.dataset.action===item.action)||slots.find(button=>free.has(button)&&compatible(button,item)&&/booking$/.test(item.action)&&/booking$/.test(button.dataset.action||''));if(same){ordered.push(same);free.delete(same);}else ordered.push(null as unknown as DockControl)});
    items.forEach((item,index)=>{if(!ordered[index]){const button=[...free].find(candidate=>compatible(candidate,item))!;ordered[index]=button;free.delete(button);}});
    slots.forEach(button=>{button.hidden=true;button.removeAttribute('data-dock-primary');button.removeAttribute('data-dock-secondary');button.classList.remove('mobile-nav-book','dock-secondary');});
    shown=items;
    const primaryIndex=items.findIndex(item=>item.primary);
    ordered.forEach((button,index)=>{
      const item=items[index],span=button.querySelector('span')!;button.hidden=false;button.dataset.action=item.action;button.dataset.displayIndex=String(index);button.dataset.uiKind=item.href?'text':item.controls&&item.popup!==false?'filled':'selection';
      if(button instanceof HTMLButtonElement)button.disabled=item.disabled??false;else{button.href=item.href!;if(item.disabled)button.setAttribute('aria-disabled','true');else button.removeAttribute('aria-disabled');}
      if(item.icon)button.dataset.icon=item.icon;else delete button.dataset.icon;
      if(span.textContent!==item.label)span.textContent=item.label;
      button.dataset.dockLabel=item.label;if(item.short)button.dataset.dockShort=item.short;else delete button.dataset.dockShort;
      button.setAttribute('aria-label',item.accessible);if(item.controls)button.setAttribute('aria-controls',item.controls);else button.removeAttribute('aria-controls');if(item.controls&&item.popup!==false)button.setAttribute('aria-haspopup','dialog');else button.removeAttribute('aria-haspopup');
      const primary=index===(primaryIndex<0?items.length-1:primaryIndex);button.classList.toggle('mobile-nav-book',primary);button.classList.toggle('dock-secondary',!primary);button.toggleAttribute(primary?'data-dock-primary':'data-dock-secondary',true);
    });
    [trigger,...ordered,...free].forEach((button,index)=>{if(toolbar.children[index]!==button)toolbar.insertBefore(button,toolbar.children[index]??null)});
    if(focusedAction){
      const target=ordered.find(button=>button.dataset.action===focusedAction&&!(button instanceof HTMLButtonElement&&button.disabled))
        ||(/booking$/.test(focusedAction)?ordered.find(button=>/booking$/.test(button.dataset.action||'')&&!(button instanceof HTMLButtonElement&&button.disabled)):undefined)
        ||trigger;
      if(target!==document.activeElement)target.focus({preventScroll:true});
    }else if(focused&&!focused.hidden&&focused!==document.activeElement)focused.focus({preventScroll:true});
    dock.dataset.actionCount=String(items.length);fit();
    if(animated)morph(before!,old);else{++revision;cancel();if(noticeMoving()&&(instantInteraction()||!compact.matches)){++noticeRevision;settleNotice();}}
  }
  async function close(immediate=false){
    if(!expanded&&!menu.open)return;
    const before=pose(),old=buttonPoses();
    const panelWidth=content.getBoundingClientRect().width,opacity=getComputedStyle(content).opacity,toolbarHeight=toolbar.offsetHeight,gap=n('--size-8'),duration=n('--motion-dock-exit');
    closePopoversWithin(content);
    expanded=false;dock.dataset.expanded='false';trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-label','Разделы сайта');
    content.inert=true;content.style.cssText=`position:absolute;bottom:${toolbarHeight+gap}px;left:${gap}px;width:${panelWidth}px;pointer-events:none`;
    // The target is neutral; FLIP carries the released sheet offset into the shrinking material.
    home.after(anchor);dock.style.removeProperty('translate');menu.close();presentKey='';present(context,true,contextSection);morph(before,old,immediate,duration);
    if(!immediate&&!instantInteraction()){const fade=content.animate(Array.from({length:spring.samples+1},(_,i)=>({opacity:Number(opacity)*(1-boundedSpringProgress(i/spring.samples))})),{duration:n('--motion-ui'),easing:'linear',fill:'forwards'});effects.push(fade);try{await fade.finished}catch{}if(!expanded)content.hidden=true;fade.cancel();}
    if(!expanded){content.hidden=true;content.inert=false;content.style.cssText='';dock.style.removeProperty('translate');}
    if(compact.matches&&!modalDialogs().length)trigger.focus({preventScroll:true});
  }
  function open(){
    if(expanded||!compact.matches||noticeVisible())return;
    const before=pose(),old=buttonPoses(),duration=n('--motion-dock');
    expanded=true;dock.dataset.expanded='true';content.hidden=false;content.inert=false;content.style.cssText='';menu.append(anchor);menu.showModal();
    trigger.setAttribute('aria-expanded','true');trigger.setAttribute('aria-label','Закрыть меню');presentKey='';present([{action:'booking',label:'Записаться',accessible:'Записаться онлайн',controls:'booking-drawer'}],true);morph(before,old,false,duration);
    if(!instantInteraction())effects.push(content.animate(Array.from({length:spring.samples+1},(_,i)=>{const p=boundedSpringProgress(i/spring.samples);return{opacity:p,translate:`0 ${n('--size-8')*(1-p)}px`};}),{duration,easing:'linear'}));
    content.querySelector<HTMLElement>('#menu-title')?.focus({preventScroll:true});
  }
  registerDialogMotion(menu,{open,close});enableSheetDismiss(dock,()=>close());
  menu.addEventListener('cancel',event=>{event.preventDefault();void close()});menu.addEventListener('click',event=>{if(event.target===menu)void close()});
  slots.forEach(button=>button.addEventListener('click',event=>{const item=shown[Number(button.dataset.displayIndex)];if(item?.disabled){event.preventDefault();return;}if(item&&button instanceof HTMLButtonElement)perform(item,button,event as MouseEvent);}));
  const sizes=new ResizeObserver(schedule);sizes.observe(dock);sizes.observe(toolbar);slots.forEach(button=>sizes.observe(button.querySelector('span')!));
  addEventListener('resize',schedule);compact.addEventListener('change',()=>{++noticeRevision;cancel();settleNotice();if(!compact.matches)void close(true);fit()});
  void document.fonts.ready.then(schedule);
  reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches){++noticeRevision;cancel();settleNotice();}});
  return {setActions(items:DockItem[],section=dock.dataset.section,condensed=dock.dataset.condensed==='true',tone=contextTone){context=items;contextSection=section||'top';contextTone=tone;if(!expanded)present(items,!initialized,section,condensed,tone);else dock.dataset.condensed=String(condensed);initialized=true;},setCondensed(condensed:boolean){if(String(condensed)===dock.dataset.condensed)return;if(expanded){dock.dataset.condensed=String(condensed);fit();}else present(context,!initialized,contextSection,condensed);},isOpen:()=>expanded,fit:schedule};
}
