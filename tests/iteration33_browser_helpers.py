from iteration18_browser_helpers import *
AUDIT=r'''(()=>{
 const bad=[],range=document.createRange();
 for(const b of document.querySelectorAll('button,.btn,.text-btn,.mobile-menu nav a,.contact-channel,.footer-groups a')){
  const r=b.getBoundingClientRect(),s=getComputedStyle(b);
  if(!r.width||!r.height||s.visibility==='hidden'||b.closest('dialog:not([open]),[hidden],[inert]'))continue;
  if(r.height<43.9)bad.push('hit:'+b.className);
  if(b.matches('.hero-edge,.hero-dot,.icon-btn,.certificate-object,.gift-visual,.dock-menu')||b.querySelector('img')||!b.textContent.trim())continue;
  if(b.scrollWidth>b.clientWidth+1||parseFloat(s.paddingLeft)<12||parseFloat(s.paddingRight)<12)bad.push('label:'+b.textContent.trim());
  const nodes=document.createTreeWalker(b,NodeFilter.SHOW_TEXT);while(nodes.nextNode()){
   if(!nodes.currentNode.textContent.trim())continue;range.selectNodeContents(nodes.currentNode);if(range.getClientRects().length>1)bad.push('wrap:'+nodes.currentNode.textContent);
  }
 }
 for(const dialog of document.querySelectorAll('dialog[open]:not(.booking-drawer)')){const r=dialog.getBoundingClientRect(),v=dialog.querySelector('.surface-viewport')?.getBoundingClientRect();if(r.left<7.9||r.right>innerWidth-7.9||r.top<7.9||r.bottom>innerHeight-7.9||v&&(v.left<r.left-.1||v.right>r.right+.1||v.top<r.top-.1||v.bottom>r.bottom+.1))bad.push('window bounds:'+dialog.className);}
 const dock=document.querySelector('[data-mobile-nav]'),d=dock.getBoundingClientRect();
 return{width:innerWidth,height:innerHeight,theme:document.documentElement.dataset.theme,overflow:document.documentElement.scrollWidth>innerWidth+1,bad,context:dock.dataset.section,dock:{top:d.top,bottom:d.bottom,width:d.width,left:d.left,right:d.right,suppressed:dock.dataset.suppressed,inert:dock.inert},errors:window.__qaErrors||[]};
})()'''
