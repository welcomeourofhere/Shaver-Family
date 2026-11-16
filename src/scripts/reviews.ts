import {planReviewBatches,planReviewCarousel,type ReviewTile} from './review-layout';
import {createReviewGallery} from './review-gallery';
import {observeRail,connectRailControls,enableRailCardSelection,nativeRail} from './rail-selection';
import {enableRailMouseDrag} from './native-rail-drag';
import {numberToken} from './motion';
import {enableReadingScroll,updateReadingEdges} from './reading-scroll';
import {labelReadingButton} from './reading-preview';
import {beginReadingTransition} from './reading-transition';

const board=document.querySelector<HTMLElement>('[data-review-bento]');
if(board){
 const bento=board,lifetime=new AbortController(),{signal}=lifetime,phone=matchMedia('(max-width:960px)');
 const seed=crypto.getRandomValues(new Uint32Array(1))[0];
 const cards=[...bento.querySelectorAll<HTMLElement>('[data-review-card]')],extras=[...bento.querySelectorAll<HTMLElement>('[data-review-extra]')],all=[...cards,...extras];
 const rules={verticalIds:cards.filter(c=>c.dataset.reviewShort==='true').map(c=>c.id),featureIds:cards.filter(c=>c.dataset.reviewFeature==='true').map(c=>c.id),videoIds:cards.filter(c=>c.dataset.reviewVideo==='true').map(c=>c.id)};
 const byId=new Map(all.map(card=>[card.id,card])),galleries=new Map(cards.map(card=>[card,createReviewGallery(card.querySelector<HTMLElement>('[data-review-gallery]')!,signal)]));
 const more=document.querySelector<HTMLButtonElement>('[data-review-more]');
 let tiles:ReviewTile[]=[],key='',frame=0,readingFrame=0,selectedId='',fontsReady=false,expanded=false;
 bento.setAttribute('aria-busy','true');
 const measurements=new WeakMap<HTMLElement,{key:string;height:number}>();
 const visibleCards=()=>[...bento.querySelectorAll<HTMLElement>(':scope>[data-review-tile]')].filter(item=>!item.hidden);
 function measuredCopy(card:HTMLElement,quote:HTMLElement,width:number){
  const style=getComputedStyle(quote),key=[width,style.font,style.letterSpacing,quote.textContent].join('|'),previous=measurements.get(card);
  if(previous?.key===key)return previous.height;
  // Measure intrinsic text at the candidate full width, outside both grid tracks and transforms.
  const sample=quote.cloneNode(true) as HTMLElement;
  sample.querySelectorAll<HTMLElement>('[hidden]').forEach(p=>p.hidden=false);
  sample.setAttribute('aria-hidden','true');sample.inert=true;sample.style.cssText=`position:fixed;visibility:hidden;pointer-events:none;inset:0 auto auto 0;width:${width}px;max-width:none;height:auto;`;
  quote.parentElement!.append(sample);const height=sample.scrollHeight+numberToken('--size-2');sample.remove();measurements.set(card,{key,height});return height;
 }
 function reading(){
  readingFrame=0;
  for(const card of cards){
   const prose=card.querySelector<HTMLElement>('.review-prose')!,button=card.querySelector<HTMLButtonElement>('[data-review-read]')!,gallery=card.querySelector<HTMLElement>('[data-review-gallery]')!;
   if(card.hidden){gallery.inert=true;galleries.get(card)!.playback();continue;}
   const expanded=phone.matches&&card.dataset.reading==='true',copy=card.querySelector<HTMLElement>('.review-copy')!,quote=prose.querySelector<HTMLElement>('blockquote')!;
   const padding=numberToken('--review-copy-padding')*2,tolerance=numberToken('--reading-scroll-tolerance');
   const style=getComputedStyle(copy);
   const proseStyle=getComputedStyle(prose),width=phone.matches?prose.clientWidth-parseFloat(proseStyle.paddingRight):card.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)-parseFloat(proseStyle.paddingRight);
   const intrinsic=measuredCopy(card,quote,width),height=card.clientHeight,cap=height*numberToken(phone.matches?'--review-phone-copy-share':'--review-copy-share');
   const [w,h]=(card.dataset.reviewShape||'1x2').split('x').map(Number);
   const side=!phone.matches&&card.dataset.reviewShort!=='true'&&w>1&&(h===1||intrinsic>height*numberToken('--review-side-copy-share'));
   card.dataset.reviewComposition=side?'side':'top';
   const needed=phone.matches&&(expanded||intrinsic>cap-padding+tolerance);
   button.hidden=!needed;button.setAttribute('aria-expanded',String(expanded));
   quote.querySelectorAll<HTMLElement>('[data-reading-rest]').forEach(p=>p.hidden=needed&&!expanded);
   const opening=needed&&!expanded?quote.scrollHeight:intrinsic,controlsHeight=needed?button.offsetHeight+parseFloat(style.gap):0;
   const natural=opening+padding+controlsHeight,copyHeight=`${needed&&!expanded?Math.min(height-numberToken('--size-160'),natural):natural<=cap+tolerance?natural:cap}px`;
   if(card.style.getPropertyValue('--review-copy-height')!==copyHeight)card.style.setProperty('--review-copy-height',copyHeight);
   labelReadingButton(button,expanded);
   gallery.inert=expanded;gallery.setAttribute('aria-hidden',String(expanded));
   const previousTrim=parseFloat(copy.style.getPropertyValue('--review-copy-trim'))||0,missing=quote.scrollHeight-(prose.clientHeight-previousTrim),trim=missing>0&&missing<=tolerance?Math.ceil(missing):0;
   const trimValue=`${trim}px`;if(copy.style.getPropertyValue('--review-copy-trim')!==trimValue)copy.style.setProperty('--review-copy-trim',trimValue);
   const scrollable=prose.scrollHeight>prose.clientHeight+tolerance;
   prose.tabIndex=scrollable?0:-1;card.dataset.reviewScrollable=String(scrollable);
   const edge=`${side?gallery.offsetWidth:gallery.offsetHeight}px`;
   if(card.style.getPropertyValue('--review-media-edge')!==edge)card.style.setProperty('--review-media-edge',edge);
   readingProgress(card,prose);
   galleries.get(card)!.playback();
  }
  if(fontsReady){bento.dataset.bentoReady='true';bento.setAttribute('aria-busy','false');}
 }
 const scheduleReading=()=>{if(!readingFrame)readingFrame=requestAnimationFrame(reading)};
 function readingProgress(card:HTMLElement,prose:HTMLElement){const range=prose.scrollHeight-prose.clientHeight;card.style.setProperty('--review-scroll-progress',String(range>0?prose.scrollTop/range:0));updateReadingEdges(prose);}
 for(const card of cards){
  const prose=card.querySelector<HTMLElement>('.review-prose')!;
  prose.addEventListener('scroll',()=>readingProgress(card,prose),{signal,passive:true});
  enableReadingScroll(prose,()=>true,signal,{edgeChain:'buffered'});
  card.querySelector<HTMLButtonElement>('[data-review-read]')!.addEventListener('click',()=>{
   beginReadingTransition(card,prose,scheduleReading);card.dataset.reading=String(card.dataset.reading!=='true');prose.scrollTop=0;scheduleReading();
  },{signal});
 }
 const controls=connectRailControls(bento);
 const choose=observeRail(bento,':scope>[data-review-tile]',index=>{if(phone.matches){selectedId=visibleCards()[index]?.id??'';controls(index);}});
 enableRailMouseDrag(bento,phone);
 enableRailCardSelection(bento,'.review-card',()=>phone.matches,index=>choose(index),signal);
 function layout(){
  frame=0;const columns=bento.clientWidth>=numberToken('--review-quad-min')?4:bento.clientWidth>=numberToken('--review-triple-min')?3:2,nextKey=(phone.matches?'phone':String(columns))+':'+expanded;
  if(nextKey===key){scheduleReading();return;}key=nextKey;
  const plan=phone.matches?{columns:1,rows:1,initialRows:1,initialIds:all.map(c=>c.id),tiles:planReviewCarousel(all.map(c=>c.id),seed,rules)}:planReviewBatches(cards.map(c=>c.id),extras.map(c=>c.id),columns,seed,rules);
  const ordered=[...plan.tiles].sort((a,b)=>a.y-b.y||a.x-b.x);
  tiles=ordered.filter(tile=>phone.matches||expanded||plan.initialIds.includes(tile.id));
  const shown=new Set(tiles.map(t=>t.id));
  all.forEach(card=>{card.hidden=!shown.has(card.id);card.inert=card.hidden;});
  if(more)more.hidden=phone.matches;
  tiles.forEach((tile,index)=>{
   const card=byId.get(tile.id)!;
   card.dataset.reviewShape=`${tile.w}x${tile.h}`;
   for(const [name,value]of Object.entries({'--tile-x':tile.x+1,'--tile-y':tile.y+1,'--tile-w':tile.w,'--tile-h':tile.h}))card.style.setProperty(name,String(value));
   if(bento.children[index]!==card)bento.insertBefore(card,bento.children[index]??null);
  });
  bento.style.setProperty('--review-columns',String(plan.columns));bento.style.setProperty('--review-rows',String(expanded?plan.rows:plan.initialRows));bento.style.setProperty('--rail-count',String(tiles.length));
  bento.dataset.reviewLayout=phone.matches?'phone':String(columns);bento.dataset.reviewExpanded=String(expanded);
  bento.dataset.reviewFormat=phone.matches?'phone':'module';
  tiles.forEach(tile=>{const card=byId.get(tile.id)!;card.dataset.reviewTone=tile.tone;card.dataset.selectionSurface=tile.tone;});
  if(phone.matches){
   nativeRail(bento).interrupt();nativeRail(bento).measure();
   const index=Math.max(0,visibleCards().findIndex(card=>card.id===selectedId));
   choose(index);controls(index);const card=visibleCards()[index];
   if(card)bento.scrollTo({left:card.offsetLeft-bento.offsetLeft,behavior:'instant'});
  }else bento.scrollLeft=0;
  scheduleReading();
 }
 const schedule=()=>{if(!frame)frame=requestAnimationFrame(layout)};
 more?.addEventListener('click',()=>{
  expanded=!expanded;more.setAttribute('aria-expanded',String(expanded));more.textContent=expanded?'Скрыть отзывы':'Показать ещё';schedule();
 },{signal});
 const size=new ResizeObserver(schedule);size.observe(bento);
 const copySizes=new ResizeObserver(scheduleReading);cards.forEach(card=>{copySizes.observe(card.querySelector('.review-prose')!);copySizes.observe(card.querySelector('blockquote')!);});
 phone.addEventListener('change',schedule,{signal});
 void document.fonts.ready.then(()=>{fontsReady=true;cards.forEach(card=>measurements.delete(card));scheduleReading();});layout();
 document.addEventListener('astro:before-swap',()=>{lifetime.abort();size.disconnect();copySizes.disconnect();cancelAnimationFrame(frame);cancelAnimationFrame(readingFrame);},{once:true});
}
