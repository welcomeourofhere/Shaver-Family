type Popup={anchor:HTMLElement;isOpen:()=>boolean;open:()=>void;close:()=>void};
const popups=new Map<HTMLElement,Popup>();
const inherited=['--action-bg','--action-fg','--selection-bg','--selection-fg','--focus-ring','--shadow-tint'];

/** Native top layer when available; the same component portals into its dialog otherwise. */
export function popover(panel:HTMLElement,anchor:HTMLElement):Popup{
 const existing=popups.get(panel);if(existing)return existing;
 const native=typeof panel.showPopover==='function',home=native?null:document.createComment('popup home');
 if(home)panel.before(home);
 const saved=new Map<string,string>();
 const isOpen=()=>native?panel.matches(':popover-open'):panel.hasAttribute('data-popover-open');
 const automatic=panel.getAttribute('popover')!=='manual';
 const outside=(event:PointerEvent)=>{if(event.target instanceof Node&&!anchor.contains(event.target)&&!panel.contains(event.target))close()};
 function close(){
  if(!isOpen())return;
  if(native){panel.hidePopover();return;}
  panel.removeAttribute('data-popover-open');home!.after(panel);
  for(const [key,value]of saved){if(value)panel.style.setProperty(key,value);else panel.style.removeProperty(key)}saved.clear();
  document.removeEventListener('pointerdown',outside,true);panel.dispatchEvent(new Event('toggle'));
 }
 function open(){
  if(isOpen())return;
  if(automatic)for(const [other,owner]of popups)if(other!==panel&&other.getAttribute('popover')!=='manual')owner.close();
  if(native){panel.showPopover();return;}
  const style=getComputedStyle(panel),colors=inherited.map(key=>[key,style.getPropertyValue(key).trim()]);
  for(const [key,value]of colors)if(value){saved.set(key,panel.style.getPropertyValue(key));panel.style.setProperty(key,value)}
  const dialogs=document.querySelectorAll('dialog[open]');
  const dialog=anchor.closest('dialog[open]')??dialogs[dialogs.length-1];
  (dialog??document.body).append(panel);panel.setAttribute('data-popover-open','');
  if(automatic)document.addEventListener('pointerdown',outside,true);
  panel.dispatchEvent(new Event('toggle'));
 }
 const owner={anchor,isOpen,open,close};popups.set(panel,owner);return owner;
}

export function closePopoversWithin(root:HTMLElement){
 const dialog=root.closest('dialog');
 for(const [panel,owner]of popups)if(root.contains(owner.anchor)||root.contains(panel)||dialog?.contains(panel))owner.close();
}
if(typeof document!=='undefined')document.addEventListener('astro:before-swap',()=>{for(const owner of popups.values())owner.close();popups.clear()},{once:true});
