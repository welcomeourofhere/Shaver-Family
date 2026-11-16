"""Both faces load and the rays' convergence remains covered by opaque artwork."""
from PIL import Image
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
image=Image.open(ROOT/'public/media/fair-price-poster-soviet-v3.webp').convert('RGBA')
report=[]
for width in [390,650,699,700,768,834,960]:
 for scale in [1,2]:
  call('open','http://127.0.0.1:4321/');call('set','viewport',str(width),'1000');call('set','media','light','reduced-motion');settle()
  if scale==2:js('''(()=>{for(const e of document.querySelectorAll('.visit-copy *'))if([...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))e.style.fontSize=`${parseFloat(getComputedStyle(e).fontSize)*2}px`})()''')
  center('.visit-ticket');js('document.querySelector(".visit-art img").decode().then(()=>true)')
  sample=js('''(()=>{const img=document.querySelector('.visit-art img'),r=img.getBoundingClientRect(),print=document.querySelector('.visit-print').getBoundingClientRect(),ticket=document.querySelector('.visit-ticket'),style=getComputedStyle(img),tablet=getComputedStyle(document.querySelector('.visit-copy')).gridRowStart==='1';const scale=(style.objectFit==='cover'?Math.max:Math.min)(r.width/img.naturalWidth,r.height/img.naturalHeight),w=img.naturalWidth*scale,h=img.naturalHeight*scale,x=print.left+print.width*(tablet?.75:.5),y=print.top+print.height*.82;return{loaded:img.complete&&img.naturalWidth>0,tablet,x:(x-(r.left+(r.width-w)/2))/scale,y:(y-(r.bottom-h))/scale}})()''')
  assert sample['loaded'],sample
  x,y=round(sample['x']),round(sample['y']);assert 0<=x<image.width and 0<=y<image.height,(width,scale,sample)
  sample['alpha']=image.getpixel((x,y))[3];assert sample['alpha']>=250,(width,scale,sample)
  report.append({'width':width,'textScale':scale,**sample})
save('iteration38-artwork',report)
print('PASS loaded portraits and opaque rays origin in 14 phone/tablet/text cases',flush=True)
