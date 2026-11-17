interface LoadingState {busy:boolean;manual:boolean;media:boolean;layer:HTMLElement|null;showTimer?:ReturnType<typeof setTimeout>;timeout?:ReturnType<typeof setTimeout>;}
const states=new Map<HTMLElement,LoadingState>();
const watched=new Map<HTMLElement,()=>void>();
const visible=new Set<HTMLElement>();
const indicators=new Set<HTMLElement>(),mediaVisible=new WeakSet<HTMLElement>(),refreshers=new WeakMap<HTMLElement,()=>void>();
const mediaObserver=new IntersectionObserver(entries=>{for(const entry of entries){const host=entry.target as HTMLElement;if(entry.isIntersecting){mediaVisible.add(host);refreshers.get(host)?.()}else mediaVisible.delete(host);}});
const template=()=>document.querySelector<HTMLTemplateElement>('[data-loading-template]');
const token=(name:string)=>Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue(name));
const motionObserver=new IntersectionObserver(entries=>{for(const entry of entries){const indicator=entry.target as HTMLElement;if(entry.isIntersecting)visible.add(indicator);else visible.delete(indicator);indicator.dataset.loadingPaused=String(!entry.isIntersecting||document.hidden);}});
function observeIndicators(root:ParentNode){const nodes=[...root.querySelectorAll<HTMLElement>('[data-loading-indicator]')];if(root instanceof HTMLElement&&root.matches('[data-loading-indicator]'))nodes.unshift(root);for(const indicator of nodes)if(!indicators.has(indicator)){indicators.add(indicator);motionObserver.observe(indicator);}}
function stateFor(host:HTMLElement){let state=states.get(host);if(!state){state={busy:false,manual:false,media:false,layer:null};states.set(host,state)}return state;}

/** One visual owner for pending components; existing components retain success/error semantics. */
export function setLoading(host:HTMLElement,busy:boolean){stateFor(host).manual=busy;renderLoading(host);}
function renderLoading(host:HTMLElement){
 const state=stateFor(host),busy=state.manual||state.media;host.setAttribute('aria-busy',String(busy));if(state.busy===busy)return;
 state.busy=busy;clearTimeout(state.showTimer);
 if(!busy){clearTimeout(state.timeout);state.timeout=undefined;if(state.layer)state.layer.hidden=true;return;}
 state.showTimer=setTimeout(()=>{
  if(!state.busy||!host.isConnected)return;
  if(!state.layer){const source=template();if(!source)return;const layer=document.createElement('span');layer.className='loading-layer';layer.setAttribute('aria-hidden','true');layer.append(source.content.cloneNode(true));host.append(layer);state.layer=layer;observeIndicators(layer);}
  state.layer.hidden=false;
 },token('--loading-show-delay'));
}

function watchMedia(host:HTMLElement){
 if(watched.has(host))return;
 const loadedFrames=new WeakMap<HTMLIFrameElement,string>(),failedFrames=new WeakMap<HTMLIFrameElement|HTMLVideoElement,string>();
 let frameSources='';
 const refresh=()=>{
  let pending=false;const waiting:(HTMLIFrameElement|HTMLVideoElement)[]=[];
  for(const image of host.querySelectorAll<HTMLImageElement>('img'))if((image.getAttribute('src')||image.getAttribute('srcset'))&&!image.complete)pending=true;
  for(const frame of host.querySelectorAll<HTMLIFrameElement>('iframe')){const source=frame.getAttribute('src');if(source&&loadedFrames.get(frame)!==source&&failedFrames.get(frame)!==source){pending=true;waiting.push(frame);}}
  for(const video of host.querySelectorAll<HTMLVideoElement>('video')){const source=video.getAttribute('src');if(source&&video.readyState<2&&!video.error&&failedFrames.get(video)!==source){pending=true;waiting.push(video);}}
  const state=stateFor(host);
  const sources=[...host.querySelectorAll('iframe,video')].map(frame=>frame.getAttribute('src')).join('|');
  if(sources!==frameSources){clearTimeout(state.timeout);state.timeout=undefined;frameSources=sources;}
  state.media=pending;renderLoading(host);
  if(waiting.length&&!state.timeout&&mediaVisible.has(host))state.timeout=setTimeout(()=>{for(const frame of waiting)failedFrames.set(frame,frame.getAttribute('src')||'');state.timeout=undefined;refresh();},token('--loading-timeout'));
 };
 const finished=(event:Event)=>{const target=event.target;if(target instanceof HTMLIFrameElement)(event.type==='load'?loadedFrames:failedFrames).set(target,target.getAttribute('src')||'');refresh();};
 host.addEventListener('load',finished,true);host.addEventListener('error',finished,true);host.addEventListener('loadeddata',finished,true);
 watched.set(host,()=>{host.removeEventListener('load',finished,true);host.removeEventListener('error',finished,true);host.removeEventListener('loadeddata',finished,true)});
 // Source changes and new images share the same owner, including decoded service replacements.
 const observer=new MutationObserver(refresh);observer.observe(host,{childList:true,subtree:true,attributes:true,attributeFilter:['src','srcset']});
 const cleanup=watched.get(host)!;watched.set(host,()=>{cleanup();observer.disconnect();mediaObserver.unobserve(host)});refreshers.set(host,refresh);mediaObserver.observe(host);refresh();
}

function scan(root:ParentNode){
 if(root instanceof HTMLElement&&root.matches('[data-loading-media]'))watchMedia(root);
 for(const host of root.querySelectorAll<HTMLElement>('[data-loading-media]'))watchMedia(host);
 observeIndicators(root);
}
scan(document);
new MutationObserver(records=>{
 for(const record of records)for(const node of record.addedNodes)if(node instanceof HTMLElement)scan(node);
 for(const [host,state] of states)if(!host.isConnected){clearTimeout(state.showTimer);clearTimeout(state.timeout);watched.get(host)?.();watched.delete(host);states.delete(host);}
 for(const indicator of indicators)if(!indicator.isConnected){visible.delete(indicator);indicators.delete(indicator);motionObserver.unobserve(indicator);}
}).observe(document.body,{childList:true,subtree:true});
document.addEventListener('visibilitychange',()=>{for(const indicator of visible)indicator.dataset.loadingPaused=String(document.hidden)});
