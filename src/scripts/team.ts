import {observeRail,connectRailControls,enableRailCardSelection,nativeRail} from './rail-selection';
import {enableRailMouseDrag} from './native-rail-drag.ts';
import './personal-booking-label';
import { closeBooking } from "./booking";
import { closeDialog, openDialog } from "./motion";
import {requestFeedback} from './feedback';

for (const button of document.querySelectorAll<HTMLButtonElement>(
  "[data-team-open]",
)) {
  button.addEventListener("click", () => {
    const dialog = document.getElementById(
      `team-dialog-${button.dataset.teamOpen}`,
    );
    if (!(dialog instanceof HTMLDialogElement)) return;
    for (const other of document.querySelectorAll<HTMLDialogElement>(
      "dialog[open]",
    ))
      if (other !== dialog)
        void (other.matches("[data-booking-drawer]")
          ? closeBooking(true)
          : closeDialog(other, true));
    openDialog(dialog);
  });
}

const rail=document.querySelector<HTMLElement>('.team-grid');
if(rail) {
  const compact=matchMedia('(max-width:960px)'),cards=[...rail.querySelectorAll<HTMLElement>('.team-card')];
  enableRailMouseDrag(rail,compact);
  enableRailCardSelection(rail,'.team-card',()=>compact.matches,index=>choose(index));
  let selected=0;
  const controls=connectRailControls(rail);
  const choose=observeRail(rail,'.team-card',index=>{selected=index;cards.forEach((card,i)=>card.dataset.mobileCurrent=String(i===index));controls(index)});
  rail.addEventListener('keydown',event=>{
    if(!compact.matches||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?cards.length-1:Math.max(0,Math.min(cards.length-1,selected+(event.key==='ArrowRight'?1:-1)));
    if(next!==selected)requestFeedback('select',event);
    nativeRail(rail).goTo(next,true);
    cards[next].querySelector<HTMLAnchorElement>('.team-book')?.focus({preventScroll:true});
  });
}
