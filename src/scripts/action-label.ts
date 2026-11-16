// Fit a deliberate short label without shrinking padding, wrapping text or losing its accessible name.
const context=document.createElement('canvas').getContext('2d');
if(context){
 const controls=[...document.querySelectorAll<HTMLElement>('[data-action-short],[data-personal-booking-short]')];
 const update=(control:HTMLElement)=>{
  if(!control.clientWidth)return;
  const label=control.querySelector<HTMLElement>('[data-action-label]')??control,full=control.dataset.actionFull??control.getAttribute('aria-label')!,style=getComputedStyle(control),labelStyle=getComputedStyle(label),parent=control.parentElement!,parentStyle=getComputedStyle(parent);
  context.font=`${labelStyle.fontStyle} ${labelStyle.fontWeight} ${labelStyle.fontSize} ${labelStyle.fontFamily}`;
  const parentWidth=parent.clientWidth-parseFloat(parentStyle.paddingLeft)-parseFloat(parentStyle.paddingRight),columns=Number(control.dataset.actionColumns)||1;
  const width=control.hasAttribute('data-action-short')?(parentWidth-(columns-1)*(parseFloat(parentStyle.columnGap)||0))/columns:control.clientWidth;
  const siblings=label===control?[]:[...control.children].filter(child=>child!==label);
  const icons=siblings.reduce((sum,child)=>sum+child.getBoundingClientRect().width,0)+siblings.length*(parseFloat(style.columnGap)||0);
  // Plain contact links extend their touch padding into existing visual gutters.
  const bleed=control.hasAttribute('data-action-bleed')?Math.min(0,parseFloat(style.marginLeft)||0)+Math.min(0,parseFloat(style.marginRight)||0):0;
  const available=width-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)-icons-bleed;
  const next=context.measureText(full).width>available+.5?(control.dataset.actionShort??control.dataset.personalBookingShort!):full;
  if(label.textContent!==next)label.textContent=next;
 };
 let frame=0;const pending=new Set<HTMLElement>();
 const schedule=(control:HTMLElement)=>{pending.add(control);if(!frame)frame=requestAnimationFrame(()=>{frame=0;for(const item of pending)update(item);pending.clear();});};
 const observer=new ResizeObserver(entries=>{for(const entry of entries)for(const control of controls)if(control.contains(entry.target)||entry.target===control.parentElement)schedule(control);});
 controls.forEach(control=>{observer.observe(control);const label=control.querySelector<HTMLElement>('[data-action-label]');if(label)observer.observe(label);if(control.parentElement)observer.observe(control.parentElement);update(control);});
 void document.fonts.ready.then(()=>controls.forEach(schedule));
 document.addEventListener('astro:before-swap',()=>{observer.disconnect();cancelAnimationFrame(frame);pending.clear();},{once:true});
}
