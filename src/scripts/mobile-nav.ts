import {isKeyboardActivation} from './interaction-intent';
import {openBooking,bookingActionFrom} from './booking';
import {openDialog,closeDialog,reducedMotion} from './motion';
import {dockActions,type DockAction} from './dock-actions';
import {navigation} from '../config/navigation';
import {openContact} from './contact';
import {enableSheetDismiss} from './sheet-gesture';
import {createDockSurface,type DockItem} from './dock-surface';

const dock=document.querySelector<HTMLElement>('[data-mobile-nav]');
if(dock) {
  const compact=matchMedia('(max-width:960px)');
  const menu=document.querySelector<HTMLDialogElement>('#mobile-menu')!;
  const categories=document.querySelector<HTMLDialogElement>('.category-dialog');
  if(categories)enableSheetDismiss(categories);
  const surface=createDockSurface(dock,menu,(item,button,event)=>void perform(item,button,event));
  const menuContent=dock.querySelector<HTMLElement>('.dock-content')!;
  const article=!!document.querySelector('.story-page');
  const status=dock.querySelector<HTMLElement>('[data-dock-status]')!;
  let section=article?'article':'top',actions=dockActions(section),scheduled=0;
  let returnToDock:HTMLElement|null=null;
  const candidates=new Set<HTMLElement>();
  const sections=[...document.querySelectorAll<HTMLElement>('main>section,.hero-asides,#certificates,#welcome-offer,#cashback,footer')];
  let observer:IntersectionObserver|undefined;
  function render() {
    actions=dockActions(section);dock!.dataset.section=section;
    const selected=document.querySelector<HTMLElement>('.team-card[data-mobile-current="true"]');
    const bookingName=selected?.dataset.bookingName;
    const items:DockItem[]=[];
    for(const item of actions) {
      const action=item.action;
      const personalBooking=action==='master-booking'&&bookingName;
      const controls=dialogForAction(action);
      let accessibleName=item.label;
      if(personalBooking)accessibleName=`Записаться к ${bookingName}`;
      if(action==='master-story')accessibleName=`Знакомство: ${selected?.querySelector('.team-name')?.textContent||''}`;
      if(action==='visit-sonya')accessibleName='Записаться к Соне по акции «Честная цена»';
      if(action==='visit-sveta')accessibleName='Записаться к Свете по акции «Честная цена»';
      if(action==='review-write')accessibleName='Оставить отзыв';
      const icon:DockItem['icon']=action==='offer-prev'?'left':action==='offer-next'?'right':undefined;
      if(icon)accessibleName=icon==='left'?'Предыдущая акция':'Следующая акция';
      const disabled=icon?document.querySelector<HTMLButtonElement>(icon==='left'?'[data-of-prev]':'[data-of-next]')?.disabled:false;
      items.push({action,label:personalBooking?`К ${bookingName}`:item.label,accessible:accessibleName,controls:controls||undefined,icon,disabled,primary:item.primary});
    }
    surface.setActions(items);
    const current=navigation.find(item=>item.id===section)?.label||({'welcome-offer':'Первый визит',cashback:'Кешбэк','first-visit':'Честная цена'} as Record<string,string>)[section];
    status.textContent=current?`Раздел: ${current}`:article?'Интервью мастера':'Барбершоп СОЮЗ';
    const activeLink=({'welcome-offer':'offers',promotions:'offers',cashback:'offers','first-visit':'offers',footer:'contacts',article:'masters'} as Record<string,string>)[section]||section;
    for(const link of menuContent.querySelectorAll<HTMLAnchorElement>('nav a')) {
      if(link.hash===`#${activeLink}`)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');
    }
  }
  function dialogForAction(action:string) {
    if(action.includes('booking')||action.startsWith('visit-'))return 'booking-drawer';
    switch(action) {
      case 'categories': return 'service-categories';
      case 'promo': return 'promo-dialog';
      case 'master-story': return document.querySelector('.team-card[data-mobile-current="true"] .team-portrait[data-team-open]')?.getAttribute('aria-controls');
      case 'review-write': return 'review-dialog';
      case 'contact': return 'contact-dialog';
      case 'offer-action': {
        const trigger=document.querySelector('.of-card[data-offer-active="true"] .of-action');
        if(trigger?.hasAttribute('data-booking'))return 'booking-drawer';
        if(trigger?.hasAttribute('data-contact'))return 'contact-dialog';
        return trigger?.getAttribute('aria-controls');
      }
    }
  }
  const navigate=(id:string)=>{
    const link=[...menuContent.querySelectorAll<HTMLAnchorElement>('nav a')].find(item=>item.hash===`#${id}`);
    if(link)link.click();
    else if(id==='top')document.querySelector<HTMLAnchorElement>('.footer-logo')?.click();
  };
  const click=(selector:string)=>document.querySelector<HTMLElement>(selector)?.click();
  async function perform(item:DockAction,source:HTMLButtonElement,event:MouseEvent) {
    switch(item.action) {
      case 'services':case 'masters':case 'certificates':case 'top':navigate(item.action);break;
      case 'categories':
        if(categories) {
          const selectedTab=document.querySelector<HTMLElement>('[data-sd-tab][aria-selected="true"]')?.dataset.sdTab;
          for(const button of categories.querySelectorAll<HTMLButtonElement>('[data-dock-category]'))
            button.setAttribute('aria-pressed',String(button.dataset.dockCategory===selectedTab));
          openDialog(categories);
        }
        break;
      case 'promo':{const promo=document.querySelector<HTMLDialogElement>('dialog.promo-dialog');if(promo)openDialog(promo);break;}
      case 'cashback-info':click('.hero .cashback-link');break;
      case 'offer-next':case 'offer-prev':{
        const target=document.querySelector<HTMLButtonElement>(item.action==='offer-next'?'[data-of-next]':'[data-of-prev]');
        if(target&&!target.disabled)target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:event.detail}));break;
      }
      case 'offer-action':click('.of-card[data-offer-active="true"] .of-action');break;
      case 'master-story':click('.team-card[data-mobile-current="true"] .team-portrait[data-team-open]');break;
      case 'certificate-next':{
        const cards=[...document.querySelectorAll<HTMLElement>('[data-certificate]')];
        cards[(cards.findIndex(card=>card.getAttribute('aria-pressed')==='true')+1)%cards.length]?.click();break;
      }
      case 'certificate-buy':click('.certificate-buy');document.dispatchEvent(new Event('soyuz:certificate-open'));break;
      case 'visit-sonya':case 'visit-sveta':{
        const target=document.querySelector<HTMLElement>(`.visit-actions [data-master="souz-${item.action==='visit-sonya'?'sonya-kid':'svetlana'}"]`);
        if(target)await openBooking(bookingActionFrom(target),source,isKeyboardActivation(event));break;
      }
      case 'review-write':{const review=document.querySelector<HTMLDialogElement>('#review-dialog');if(review)openDialog(review);break;}
      case 'contact':openContact();break;
      default:{
        const target=document.querySelector<HTMLElement>(item.action==='master-booking'?'.team-card[data-mobile-current="true"] .team-book':item.action==='welcome-booking'?'.first-actions [data-booking]':item.action==='article-booking'||article?'.story-actions [data-booking]':'.header-book');
        const selection=item.action==='service-booking'?document.querySelector<HTMLElement>('.sd-card[aria-hidden="false"] details[open] .sd-service-name')?.textContent:undefined;
        await openBooking(selection?{service:selection,context:`Услуга: ${selection}`} : target?bookingActionFrom(target):{},source,isKeyboardActivation(event));
      }
    }
  }
  for(const button of document.querySelectorAll<HTMLButtonElement>('[data-dock-category]'))button.addEventListener('click',async()=>{
    click(`[data-sd-tab="${button.dataset.dockCategory}"]`);if(categories)await closeDialog(categories);
    document.querySelector('.sd-tabs')?.scrollIntoView({block:'start',behavior:reducedMotion.matches?'instant':'smooth'});
    dock.querySelector<HTMLElement>('[data-dock-secondary]')?.focus({preventScroll:true});
  });
  function update() {
    scheduled=0;
    const blockingModal=[...document.querySelectorAll('dialog:modal')].some(dialog=>dialog!==menu);
    const visible=compact.matches&&!blockingModal&&!(window.visualViewport&&window.visualViewport.height<innerHeight*.65);
    const suppressed=String(!visible);
    if(dock!.dataset.suppressed!==suppressed) {
      dock!.inert=!visible;
      dock!.dataset.suppressed=suppressed;
    }
    if(!compact.matches||!visible)return;
    let next=article?'article':section;
    const point=innerHeight*.4;
    const present=sections.filter(element=>{
      if(!candidates.has(element))return false;
      const r=element.getBoundingClientRect();
      return r.top<=point&&r.bottom>point&&(!element.matches('#welcome-offer,#cashback')||r.width>innerWidth*.7);
    });
    if(!article&&present.length)next=present.at(-1)!.id;
    if(next!==section){section=next;render();}
  }
  const schedule=()=>{if(!scheduled)scheduled=requestAnimationFrame(update)};
  function observe() {
    observer?.disconnect();candidates.clear();
    observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting)candidates.add(entry.target as HTMLElement);else candidates.delete(entry.target as HTMLElement)}schedule();},{rootMargin:`-${Math.round(innerHeight*.25)}px 0px -${Math.round(innerHeight*.45)}px 0px`,threshold:0});
    sections.forEach(element=>observer!.observe(element));schedule();
  }
  // Each context delegates to the existing control; there is no second booking or carousel state.
  const selectionObserver=new MutationObserver(()=>{if(compact.matches&&(section==='masters'||section==='offers'))render()});
  for(const element of document.querySelectorAll('.of-rail,.team-grid'))selectionObserver.observe(element,{subtree:true,attributes:true,attributeFilter:['data-offer-active','data-mobile-current']});
  new MutationObserver(schedule).observe(document.body,{subtree:true,attributes:true,attributeFilter:['open']});
  compact.addEventListener('change',()=>{observe();render()});
  addEventListener('resize',observe);window.visualViewport?.addEventListener('resize',schedule);addEventListener('scroll',schedule,{passive:true});
  dock.addEventListener('click',event=>{const source=(event.target as Element).closest<HTMLElement>('button');queueMicrotask(()=>{if(source&&document.querySelector('dialog:modal'))returnToDock=source})});
  document.addEventListener('close',()=>{update();if(returnToDock&&!document.querySelector('dialog:modal')){
    const source=returnToDock;returnToDock=null;const active=document.activeElement;
    // A navigation continuation can focus its heading before the native close event arrives.
    if(active instanceof HTMLElement&&active!==document.body&&active!==document.documentElement&&active.isConnected&&active.getClientRects().length&&!active.closest('[hidden],[inert]'))return;
    [source,dock.querySelector<HTMLElement>('[data-open-menu]'),document.querySelector<HTMLElement>('.site-header .more-menu>summary')].find(target=>target?.isConnected&&target.getClientRects().length&&!target.closest('[hidden],[inert]'))?.focus({preventScroll:true});
  }},true);
  render();observe();
}
