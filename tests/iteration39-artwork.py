"""The convergence is behind opaque artwork in all three ticket compositions."""
import os
from PIL import Image
from iteration33_browser_helpers import *
call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
image=Image.open(ROOT/'public/media/fair-price-poster-soviet-v3.webp').convert('RGBA');report=[]
for width in [320,390,540,560,620,650,699,768,834,960]:
 for scale in [1,2]:
  call('open',os.environ.get('QA_URL','http://127.0.0.1:4321/'));call('set','viewport',str(width),'1000');call('set','media','light','reduced-motion');settle()
  if scale==2:js('''(()=>{const runs=[...document.querySelectorAll('.visit-copy *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const [e,size] of runs)e.style.fontSize=2*size+'px'})()''')
  center('.visit-ticket');js('document.querySelector(".visit-art img").decode().then(()=>true)')
  sample=js('''(()=>{const img=document.querySelector('.visit-art img'),r=img.getBoundingClientRect(),rays=document.querySelector('.visit-rays').getBoundingClientRect(),style=getComputedStyle(img);const scale=(style.objectFit==='cover'?Math.max:Math.min)(r.width/img.naturalWidth,r.height/img.naturalHeight),w=img.naturalWidth*scale,h=img.naturalHeight*scale,x=rays.left+rays.width/2,y=rays.top+rays.height/2;return{loaded:img.complete&&img.naturalWidth>0,x:(x-(r.left+(r.width-w)/2))/scale,y:(y-(r.bottom-h))/scale}})()''')
  assert sample['loaded'];x,y=round(sample['x']),round(sample['y']);assert 0<=x<image.width and 0<=y<image.height,(width,scale,sample)
  sample['alpha']=image.getpixel((x,y))[3];assert sample['alpha']>=250,(width,scale,sample)
  report.append({'width':width,'textScale':scale,**sample})
save('iteration39-artwork',report);print('PASS opaque ray origin and loaded portraits in 20 compositions/text cases',flush=True)
