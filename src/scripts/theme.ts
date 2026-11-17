import config from '../config/design.json' with {type:'json'};
import {syncBrowserTheme} from './browser-theme.ts';
export const themeKey=config.theme.storageKey;
export function resolveTheme(choice:string|null,darkSystem:boolean){
  return choice==='dark'||choice==='light'?choice:darkSystem?'dark':'light';
}
if(typeof document!=='undefined'){
  const system=matchMedia('(prefers-color-scheme:dark)');
  let choice='auto';try{choice=localStorage.getItem(themeKey)||'auto';}catch{}
  const controls=[...document.querySelectorAll<HTMLSelectElement>('[data-theme-select]')];
  function apply(){
    document.documentElement.dataset.theme=resolveTheme(choice,system.matches);
    syncBrowserTheme();
    for(const control of controls){control.value=['light','dark'].includes(choice)?choice:'auto';control.dispatchEvent(new Event('choice:sync'));}
    for(const button of document.querySelectorAll<HTMLButtonElement>('[data-theme-toggle]')){button.setAttribute('aria-label',`Включить ${document.documentElement.dataset.theme==='dark'?'светлую':'тёмную'} тему`);button.setAttribute('aria-pressed',String(document.documentElement.dataset.theme==='dark'));}
  }
  for(const control of controls)control.addEventListener('change',()=>{
    choice=control.value;try{localStorage.setItem(themeKey,choice);}catch{}apply();
  });
  document.addEventListener('click',event=>{if(event.defaultPrevented||!(event.target instanceof Element)||!event.target.closest('[data-theme-toggle]'))return;choice=document.documentElement.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem(themeKey,choice);}catch{}apply();});
  system.addEventListener('change',apply);
  addEventListener('storage',event=>{if(event.key===themeKey||event.key===null){choice=event.newValue||'auto';apply();}});
  apply();
}
