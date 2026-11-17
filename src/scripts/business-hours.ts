import site from '../../content/site.json';
import {businessStatus} from './business-clock';
const nodes=[...document.querySelectorAll<HTMLElement>('[data-business-hours-status]')];
const compact=matchMedia('(max-width:960px)');
function update(){if(document.hidden)return;const {state,heading,detail}=businessStatus(new Date(),site.hours);for(const node of nodes){node.dataset.state=state;node.textContent=compact.matches?detail:heading;const note=node.parentElement?.querySelector('[data-business-hours-detail]');if(note)note.textContent=compact.matches?'':detail;}}
update();const timer=setInterval(update,60000);
document.addEventListener('visibilitychange',update);
compact.addEventListener('change',update);
document.addEventListener('astro:before-swap',()=>{clearInterval(timer);document.removeEventListener('visibilitychange',update);compact.removeEventListener('change',update)},{once:true});
