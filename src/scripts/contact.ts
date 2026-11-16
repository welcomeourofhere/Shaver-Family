import {closeBooking} from './booking';
import {openDialog,closeDialog} from './motion';

/** All contact entry points share one dialog and replace any previous context. */
export function openContact(context=''){
 const contact=document.querySelector<HTMLDialogElement>('.contact-dialog');
 if(!contact)return;
 for(const dialog of document.querySelectorAll<HTMLDialogElement>('dialog[open]')){
  if(dialog===contact)continue;
  if(dialog.matches('[data-booking-drawer]'))void closeBooking(true);
  else void closeDialog(dialog,true);
 }
 const description=contact.querySelector<HTMLElement>('[data-contact-context]');
 if(description){description.textContent=context;description.hidden=!context;}
 openDialog(contact);
}
