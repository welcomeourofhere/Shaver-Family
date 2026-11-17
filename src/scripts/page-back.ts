import {requestFeedback} from './feedback.ts';

export function hasSitePreviousPage(referrer:string,origin:string,historyLength:number){
 if(historyLength<=1||!referrer)return false;
 try{return new URL(referrer).origin===origin;}catch{return false;}
}
if(typeof document!=='undefined')for(const link of document.querySelectorAll<HTMLAnchorElement>('[data-page-back]')){
 link.addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  if(hasSitePreviousPage(document.referrer,location.origin,history.length)){event.preventDefault();history.back();}
  requestFeedback('close',event);
 });
}
