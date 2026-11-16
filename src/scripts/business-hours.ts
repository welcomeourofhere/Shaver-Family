import site from '../../content/site.json';
import {businessStatus} from './business-clock';
const nodes=[...document.querySelectorAll<HTMLElement>('[data-business-hours-status]')];
function update(){if(document.hidden)return;const {state,heading,detail}=businessStatus(new Date(),site.hours);for(const node of nodes){node.dataset.state=state;node.textContent=heading;const note=node.parentElement?.querySelector('[data-business-hours-detail]');if(note)note.textContent=detail;}}
update();const timer=setInterval(update,60000);
document.addEventListener('visibilitychange',update);
document.addEventListener('astro:before-swap',()=>{clearInterval(timer);document.removeEventListener('visibilitychange',update)},{once:true});
