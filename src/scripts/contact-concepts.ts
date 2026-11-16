import {isKeyboardActivation} from './interaction-intent';
import {contactConcepts} from '../content/contact-concepts';
import {numberToken,textToken,reducedMotion} from './motion';
import {closeBooking} from './booking';

const stage=document.querySelector<HTMLElement>('[data-concept-stage]');
if(stage){
 const tabs=[...document.querySelectorAll<HTMLButtonElement>('[data-contact-choice]')],panels=[...stage.querySelectorAll<HTMLElement>('[data-contact-concept]')];
 const output=document.querySelector<HTMLOutputElement>('[data-concept-count]')!,name=document.querySelector<HTMLElement>('[data-concept-name]')!,description=document.querySelector<HTMLElement>('[data-concept-description]')!;
 const canvas=stage.parentElement!,range=document.querySelector<HTMLInputElement>('[data-concept-range]')!,widthOutput=document.querySelector<HTMLOutputElement>('[data-concept-width]')!,sizeButtons=[...document.querySelectorAll<HTMLButtonElement>('[data-concept-size]')];
 let current=-1,mode='auto',animation:Animation|undefined,sizeFrame=0;
 const lifetime=new AbortController(),{signal}=lifetime;
 function size(){
  sizeFrame=0;const box=getComputedStyle(canvas),width=mode==='auto'?canvas.clientWidth-parseFloat(box.paddingLeft)-parseFloat(box.paddingRight):Math.max(280,Math.min(1160,Number(mode)));
  const value=`${width}px`;if(stage!.style.width!==value)stage!.style.width=value;
  widthOutput.textContent=`${Math.round(width)} px`;range.value=String(Math.round(width));sizeButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.conceptSize===mode)));
 }
 const scheduleSize=()=>{if(!sizeFrame)sizeFrame=requestAnimationFrame(size)};
 function select(index:number,event?:Event){
  index=(index+panels.length)%panels.length;if(index===current)return;
  animation?.cancel();void closeBooking(true);
  if(current>=0)panels[current].querySelector('iframe')?.remove();
  current=index;const panel=panels[index],concept=contactConcepts[index];
  panels.forEach((item,i)=>{item.hidden=i!==index;item.inert=i!==index;});
  tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===index));tab.tabIndex=i===index?0:-1;});
  const map=panel.querySelector<HTMLElement>('[data-concept-map]')!,template=map.querySelector<HTMLTemplateElement>('[data-map-template]')!,fragment=template.content.cloneNode(true) as DocumentFragment,frame=fragment.querySelector<HTMLIFrameElement>('iframe')!;
  frame.src=frame.dataset.mapSrc!;map.dataset.interactive='false';const toggle=map.querySelector<HTMLButtonElement>('[data-map-toggle]')!;toggle.setAttribute('aria-pressed','false');toggle.setAttribute('aria-label','Включить перемещение карты');toggle.textContent='Двигать карту';map.append(fragment);
  output.textContent=`${concept.id} / 10`;output.setAttribute('aria-label',`Вариант ${index+1} из 10`);name.textContent=concept.title;description.textContent=concept.description;
  history.replaceState(null,'',`#contact-${concept.id}`);
  if(event&&!reducedMotion.matches&&!isKeyboardActivation(event))animation=panel.animate([{opacity:0,transform:`translateY(${numberToken('--size-8')}px)`},{opacity:1,transform:'translateY(0)'}],{duration:numberToken('--motion-context'),easing:textToken('--ease-out')});
  const rail=tabs[index].parentElement!;
  if(rail.scrollWidth>rail.clientWidth){const tab=tabs[index].getBoundingClientRect(),bounds=rail.getBoundingClientRect();if(tab.left<bounds.left||tab.right>bounds.right)rail.scrollTo({left:rail.scrollLeft+tab.left-bounds.left-(bounds.width-tab.width)/2,behavior:'instant'});}
 }
 function fromHash(){const index=panels.findIndex(panel=>`#${panel.id}`===location.hash);select(index<0?0:index);}
 tabs.forEach((tab,index)=>{
  tab.addEventListener('click',event=>select(index,event),{signal});
  tab.addEventListener('keydown',event=>{const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:event.key==='ArrowRight'?(index+1)%tabs.length:event.key==='ArrowLeft'?(index+tabs.length-1)%tabs.length:null;if(next===null)return;event.preventDefault();select(next,event);tabs[next].focus({preventScroll:true});},{signal});
 });
 document.querySelectorAll<HTMLButtonElement>('[data-concept-step]').forEach(button=>button.addEventListener('click',event=>select(current+Number(button.dataset.conceptStep),event),{signal}));
 sizeButtons.forEach(button=>button.addEventListener('click',()=>{mode=button.dataset.conceptSize!;size();},{signal}));
 range.addEventListener('input',()=>{mode=range.value;size();},{signal});
 for(const map of stage.querySelectorAll<HTMLElement>('[data-concept-map]'))map.querySelector<HTMLButtonElement>('[data-map-toggle]')!.addEventListener('click',()=>{
  const enabled=map.dataset.interactive!=='true',button=map.querySelector<HTMLButtonElement>('[data-map-toggle]')!,frame=map.querySelector<HTMLIFrameElement>('iframe');map.dataset.interactive=String(enabled);button.setAttribute('aria-pressed',String(enabled));button.setAttribute('aria-label',enabled?'Остановить перемещение карты':'Включить перемещение карты');button.textContent=enabled?'Готово':'Двигать карту';if(frame)frame.tabIndex=enabled?0:-1;
 },{signal});
 for(const group of stage.querySelectorAll<HTMLElement>('[data-switch-group]')){
  const buttons=[...group.querySelectorAll<HTMLButtonElement>('[data-contact-switch]')],parts=[...group.querySelectorAll<HTMLElement>('[data-contact-pane]')];
  function choose(index:number){buttons.forEach((button,i)=>{button.setAttribute('aria-selected',String(i===index));button.tabIndex=i===index?0:-1;});parts.forEach(part=>{part.hidden=part.dataset.contactPane!==buttons[index].dataset.contactSwitch;part.inert=part.hidden;});}
  buttons.forEach((button,index)=>{button.addEventListener('click',()=>choose(index),{signal});button.addEventListener('keydown',event=>{const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:event.key==='ArrowRight'?(index+1)%buttons.length:event.key==='ArrowLeft'?(index+buttons.length-1)%buttons.length:null;if(next===null)return;event.preventDefault();choose(next);buttons[next].focus({preventScroll:true});},{signal});});
 }
 const observer=new ResizeObserver(scheduleSize);observer.observe(canvas);size();fromHash();window.addEventListener('hashchange',fromHash,{signal});
 document.addEventListener('astro:before-swap',()=>{lifetime.abort();observer.disconnect();animation?.cancel();cancelAnimationFrame(sizeFrame);},{once:true});
}
