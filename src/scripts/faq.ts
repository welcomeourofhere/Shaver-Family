import {instantInteraction,numberToken,textToken} from './motion';
const button=document.querySelector<HTMLButtonElement>('[data-faq-more]');
if(button){
 const rest=[...document.querySelectorAll<HTMLDetailsElement>('[data-faq-rest]')];
 button.setAttribute('aria-controls',rest.map(item=>item.id).join(' '));
 button.addEventListener('click',()=>{
  const expanded=button.getAttribute('aria-expanded')!=='true';
  button.setAttribute('aria-expanded',String(expanded));button.textContent=expanded?'Скрыть вопросы':'Ещё вопросы';button.setAttribute('aria-label',expanded?'Скрыть дополнительные вопросы':'Показать остальные вопросы');
  for(const item of rest){item.hidden=!expanded;if(!expanded)item.open=false;}
  if(expanded&&!instantInteraction())rest.forEach((item,i)=>item.animate([{opacity:.7,transform:'translateY(6px)'},{opacity:1,transform:'none'}],{duration:numberToken('--motion-context'),delay:Math.min(i,3)*20,easing:textToken('--ease-out')}));
 });
}
