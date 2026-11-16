// Keep the native root gutter stable while a top-layer dialog owns scrolling.
let locked=false;
export const pageScrollY=()=>locked?document.body.scrollTop:scrollY;
export const modalScrollLocked=()=>locked;
if(typeof document!=='undefined'){
const body=document.body;
function restorePageScroll(){
 const {scrollLeft:left,scrollTop:top}=body;
 body.scrollTo({left:0,top:0,behavior:'instant'});
 delete body.dataset.modalScrollLocked;
 scrollTo({left,top,behavior:'instant'});
 locked=false;
}
function syncModalScroll(){
 const modal=document.querySelector('dialog:modal');
 if(modal&&!locked){
  const left=scrollX,top=scrollY;
  locked=true;
  body.dataset.modalScrollLocked='true';
  // Keep sticky descendants in a real scrollport, at the page's saved position.
  body.scrollTo({left,top,behavior:'instant'});
 }else if(!modal&&locked)restorePageScroll();
}
function containRootScroll(event:Event){
 // The root's technical zero and the locked body must not reset page owners.
 if(locked&&(event.target===document||event.target===window||event.target===document.documentElement||event.target===body))event.stopImmediatePropagation();
}
addEventListener('scroll',containRootScroll,{capture:true});
const observer=new MutationObserver(syncModalScroll);
observer.observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['open']});
syncModalScroll();
document.addEventListener('astro:before-swap',()=>{
 observer.disconnect();
 if(locked)restorePageScroll();
 removeEventListener('scroll',containRootScroll,{capture:true});
},{once:true});
}
