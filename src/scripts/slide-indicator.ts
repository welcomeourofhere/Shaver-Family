export function selectSlideIndicator(group:HTMLElement,index:number){group.querySelectorAll<HTMLButtonElement>('[data-slide-index]').forEach((button,i)=>button.setAttribute('aria-current',String(i===index)));}
export function bindSlideIndicator(group:HTMLElement,choose:(index:number,event:Event)=>void,signal?:AbortSignal){
 const buttons=[...group.querySelectorAll<HTMLButtonElement>('[data-slide-index]')];
 group.addEventListener('click',event=>{
  const target=event.target instanceof Element?event.target.closest<HTMLButtonElement>('[data-slide-index]'):null;
  const index=event.detail===0&&target?buttons.indexOf(target):buttons.reduce((best,button,i)=>{const a=button.getBoundingClientRect(),b=buttons[best].getBoundingClientRect();return Math.abs(a.left+a.width/2-event.clientX)<Math.abs(b.left+b.width/2-event.clientX)?i:best},0);
  choose(index,event);
 },{signal});
 group.addEventListener('keydown',event=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  event.preventDefault();event.stopPropagation();
  const current=Math.max(0,buttons.findIndex(button=>button.getAttribute('aria-current')==='true'));
  const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(current+(event.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;
  choose(next,event);buttons[next].focus({preventScroll:true});
 },{signal});
}
