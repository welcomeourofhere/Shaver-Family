import defaults from '../../deploy/analytics.json' with {type:'json'};
type Metrika=((...args:unknown[])=>void)&{a?:IArguments[];l?:number};
type CounterWindow=Window&{soyuzAnalytics?:{ga4?:string;metrika?:string};dataLayer?:IArguments[];gtag?:(...args:unknown[])=>void;ym?:Metrika};
export const analyticsConsentKey='soyuz.analytics.v2';
export const analyticsNoticeVersion='2026-11-16';
const consentLifetime=180*24*60*60*1000;
export type AnalyticsConsent={version:2;notice:string;updatedAt:number;expiresAt:number;metrika:boolean;ga4:boolean};
export function readAnalyticsConsent(raw:string|null,now=Date.now()):AnalyticsConsent|null{
 try{const value=JSON.parse(raw??'null');
  return value?.version===2&&value.notice===analyticsNoticeVersion&&typeof value.metrika==='boolean'&&typeof value.ga4==='boolean'&&Number.isFinite(value.updatedAt)&&Number.isFinite(value.expiresAt)&&value.updatedAt<=now&&value.expiresAt>now&&value.expiresAt-value.updatedAt===consentLifetime?value:null;
 }catch{return null;}
}
export function makeAnalyticsConsent(metrika:boolean,ga4:boolean,now=Date.now()):AnalyticsConsent{return{version:2,notice:analyticsNoticeVersion,updatedAt:now,expiresAt:now+consentLifetime,metrika,ga4};}
export function publicAnalyticsHost(host:string){return host==='soyuz.hair'||host==='www.soyuz.hair';}
export function contactChannel(address:string){
 try{const url=new URL(address);if(url.protocol==='tel:')return'phone';if(['vk.com','vk.ru','vk.me'].includes(url.hostname))return'vk';if(url.hostname==='t.me')return'telegram';if(url.hostname==='max.ru')return'max';}catch{}
 return undefined;
}
if(typeof window!=='undefined'){
 const w=window as CounterWindow,live=publicAnalyticsHost(location.hostname),config=w.soyuzAnalytics??defaults;
 const prompt=document.querySelector<HTMLElement>('[data-analytics-prompt]');
 const dialog=document.querySelector<HTMLDialogElement>('#cookie-settings');
 const inputs=[...document.querySelectorAll<HTMLInputElement>('[data-cookie-service]')];
 const state=document.querySelector<HTMLElement>('[data-cookie-state]');
 let consent:AnalyticsConsent|null=null,settingsTrigger:HTMLElement|null=null,pendingMetrika:Metrika|undefined;
 let gaStarted=false,metrikaStarted=false,gaQueued=false,gaScriptReady=false,choiceSaved=true,expiryTimer=0;
 const gaValid=!!config.ga4&&/^G-[A-Z0-9]+$/.test(config.ga4),ymValid=!!config.metrika&&/^\d+$/.test(config.metrika);
 function loadChoice(){
  choiceSaved=true;
  try{const raw=localStorage.getItem(analyticsConsentKey);consent=readAnalyticsConsent(raw);
   // A previous refusal stays a refusal; the expanded notice needs a fresh grant.
   if(raw===null&&localStorage.getItem('soyuz.analytics.v1')==='denied'){consent=makeAnalyticsConsent(false,false);localStorage.setItem(analyticsConsentKey,JSON.stringify(consent));localStorage.removeItem('soyuz.analytics.v1');}
  }catch{consent=null;choiceSaved=false;}
 }
 function script(id:string,src:string,ready:()=>void,failed:()=>void){
  if(document.getElementById(id))return;
  const node=document.createElement('script');node.id=id;node.async=true;node.src=src;
  node.addEventListener('load',ready,{once:true});node.addEventListener('error',()=>{node.remove();failed();},{once:true});document.head.append(node);
 }
 function clearCookies(vendor:'ga4'|'metrika'){
  for(const cookie of document.cookie.split(';')){
   const name=cookie.split('=')[0].trim();if(!(vendor==='ga4'?/^(_ga(?:_|$)|_gid$|_gat)/:/^_ym_/).test(name))continue;
   for(const domain of ['',location.hostname,'.soyuz.hair'])document.cookie=`${name}=;Max-Age=0;Path=/${domain?`;Domain=${domain}`:''};SameSite=Lax;Secure`;
  }
  if(vendor==='metrika')try{for(const key of Object.keys(localStorage))if(/^_ym/.test(key))localStorage.removeItem(key);}catch{}
 }
 function apply(){
  clearTimeout(expiryTimer);
  if(consent){if(consent.expiresAt<=Date.now())consent=null;else expiryTimer=window.setTimeout(()=>apply(),Math.min(consent.expiresAt-Date.now(),2147483647));}
  const gaAllowed=live&&consent?.ga4===true,metrikaAllowed=live&&consent?.metrika===true;
  if(gaValid)(w as unknown as Record<string,unknown>)[`ga-disable-${config.ga4}`]=!gaAllowed;
  if(gaValid&&gaAllowed&&!gaStarted){
   gaStarted=true;
   try{
    w.dataLayer??=[];w.gtag??=function(){w.dataLayer!.push(arguments);};gaQueued=!gaScriptReady;
    w.gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
    w.gtag('consent','update',{analytics_storage:'granted'});w.gtag('js',new Date());
    w.gtag('config',config.ga4,{allow_google_signals:false,allow_ad_personalization_signals:false,page_location:location.origin+location.pathname,page_referrer:safeReferrer()});
    script('soyuz-ga4',`https://www.googletagmanager.com/gtag/js?id=${config.ga4}`,()=>{gaScriptReady=true;gaQueued=false;},()=>{gaStarted=false;if(gaQueued)w.dataLayer?.splice(0);gaQueued=false;});
   }catch{gaStarted=false;}
  }else if(!gaAllowed){
   const wasStarted=gaStarted;gaStarted=false;
   // Remove delayed config/events before an SDK still in transit can replay them.
   if(gaQueued&&w.dataLayer){w.dataLayer.splice(0);gaQueued=false;}
   if(wasStarted)try{w.gtag?.('consent','update',{analytics_storage:'denied'});}catch{}
   clearCookies('ga4');
  }
  if(ymValid&&metrikaAllowed&&!metrikaStarted){
   metrikaStarted=true;
   try{
    if(!w.ym){const queue:Metrika=function(){(queue.a??=[]).push(arguments);};queue.l=Date.now();w.ym=queue;pendingMetrika=queue;}
    w.ym(Number(config.metrika),'init',{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true,url:location.origin+location.pathname,referrer:safeReferrer()});
    script('soyuz-metrika','https://mc.yandex.ru/metrika/tag.js',()=>{},()=>{metrikaStarted=false;if(pendingMetrika&&w.ym===pendingMetrika)pendingMetrika.a=[];});
   }catch{metrikaStarted=false;}
  }else if(!metrikaAllowed){
   const wasStarted=metrikaStarted;metrikaStarted=false;
   try{if(pendingMetrika&&w.ym===pendingMetrika)pendingMetrika.a=[];else if(wasStarted)w.ym?.(Number(config.metrika),'destruct');}catch{}
   clearCookies('metrika');
  }
  if(prompt)prompt.hidden=!live||consent!==null;
 }
 function safeReferrer(){try{const url=new URL(document.referrer);return url.origin+url.pathname;}catch{return'';}}
 function syncControls(){
  for(const input of inputs)input.checked=consent?.[input.dataset.cookieService as 'ga4'|'metrika']===true;
  if(state)state.textContent=consent?`Сейчас: ${[consent.metrika?'Яндекс Метрика':'',consent.ga4?'Google Analytics':''].filter(Boolean).join(' и ')||'без аналитики'}. Выбор от ${new Date(consent.updatedAt).toLocaleDateString('ru-RU')}.`:'Аналитика выключена. Выбор ещё не сохранён.';
  if(state&&!choiceSaved)state.textContent+=' Выбор действует только в этой вкладке: браузер запретил сохранение настроек.';
 }
 async function choose(metrika:boolean,ga4:boolean){
  consent=makeAnalyticsConsent(metrika,ga4);
  choiceSaved=true;
  try{localStorage.setItem(analyticsConsentKey,JSON.stringify(consent));localStorage.removeItem('soyuz.analytics.v1');}catch{choiceSaved=false;}
  apply();syncControls();
  if(dialog?.open){const{closeDialog}=await import('./motion');await closeDialog(dialog);}
 }
 dialog?.addEventListener('close',()=>{
  const target=[settingsTrigger,document.querySelector<HTMLButtonElement>('[data-site-settings]'),document.querySelector<HTMLButtonElement>('[data-open-menu]')].find(button=>button?.isConnected&&button.getClientRects().length&&!button.closest('[hidden],[inert]'));
  target?.focus({preventScroll:true});settingsTrigger=null;
 });
 document.addEventListener('click',event=>{
  if(event.defaultPrevented||!(event.target instanceof Element))return;
  const selection=event.target.closest<HTMLElement>('[data-analytics-choice]')?.dataset.analyticsChoice;
  if(selection==='granted'||selection==='denied'){void choose(selection==='granted',selection==='granted');return;}
  if(event.target.closest('[data-analytics-save]')){void choose(inputs.some(input=>input.dataset.cookieService==='metrika'&&input.checked),inputs.some(input=>input.dataset.cookieService==='ga4'&&input.checked));return;}
  if(event.target.closest('[data-analytics-withdraw]')){void choose(false,false);return;}
  const trigger=event.target.closest<HTMLElement>('[data-analytics-settings]');
  if(trigger&&dialog){settingsTrigger=trigger;syncControls();void import('./motion').then(({openDialog})=>{openDialog(dialog);dialog.querySelector<HTMLButtonElement>('[data-dismiss]')?.focus({preventScroll:true});});}
 });
 addEventListener('storage',event=>{if(event.key===analyticsConsentKey||event.key==='soyuz.analytics.v1'||event.key===null){loadChoice();apply();if(!dialog?.open)syncControls();}});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&consent&&consent.expiresAt<=Date.now()){consent=null;apply();syncControls();}});
 loadChoice();apply();
 const send=(name:string,params:Record<string,string>={})=>{
  if(!live)return;
  if(consent&&consent.expiresAt<=Date.now()){consent=null;apply();return;}
  try{if(consent?.ga4&&gaValid&&typeof w.gtag==='function')w.gtag('event',name,{...params,send_to:config.ga4});}catch{}
  try{if(consent?.metrika&&ymValid&&typeof w.ym==='function')w.ym(Number(config.metrika),'reachGoal',name,params);}catch{}
 };
 document.addEventListener('soyuz:booking-open',event=>{
  const detail=(event as CustomEvent).detail??{},params:Record<string,string>={};
  for(const key of ['master_id','service_id'])if(typeof detail[key]==='string'&&/^[\w-]{1,80}$/.test(detail[key]))params[key]=detail[key];
  send('booking_open',params);
 });
 document.addEventListener('soyuz:certificate-open',()=>send('certificate_open'));
 document.addEventListener('click',event=>{
  if(!event.isTrusted||event.defaultPrevented||!(event.target instanceof Element))return;
  const link=event.target.closest<HTMLAnchorElement>('a[href]');if(!link)return;
  if(link.matches('.certificate-buy')){send('certificate_open');return;}
  const channel=contactChannel(link.href);if(channel)send('contact_click',{channel});
 });
}
