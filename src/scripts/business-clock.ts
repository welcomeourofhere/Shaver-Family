export function businessStatus(date:Date,hours:string){
 const [opening,closing]=hours.split(/[–—-]/).map(time=>{const [h,m]=time.trim().split(':').map(Number);return h*60+m;});
 const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Moscow',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date);
 const clock=Object.fromEntries(parts.map(p=>[p.type,p.value])),now=Number(clock.hour)%24*60+Number(clock.minute),open=now>=opening&&now<closing;
 const remaining=open?closing-now:now<opening?opening-now:1440-now+opening;
 const h=Math.floor(remaining/60),m=remaining%60,delay=[h?`${h} ч`:'',m?`${m} мин`:''].filter(Boolean).join(' ');
 return {state:open?remaining<=120?'closing':'open':'closed',heading:open?'Сейчас открыто':'Сейчас закрыто',detail:open?`До закрытия ${delay}`:`Откроемся через ${delay}`,text:open?remaining<=120?`До закрытия ${delay}`:'Открыто сейчас':`Закрыто · откроемся через ${delay}`};
}
