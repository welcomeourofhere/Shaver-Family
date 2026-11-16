"""Phone halves, the separate tablet ticket and preserved desktop geometry."""
from iteration33_browser_helpers import *

call.__globals__['CLI']=['node','node_modules/agent-browser/bin/agent-browser.js','--session','soyuz32','--json']
MEASURE=r'''(()=>{
 const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}};
 const ticket=rect('.visit-ticket'),art=rect('.visit-art'),copy=rect('.visit-copy'),print=rect('.visit-print');
 const buttons=[...document.querySelectorAll('.visit-actions .btn')].map(button=>{
  const r=button.getBoundingClientRect(),style=getComputedStyle(button),label=button.querySelector('.visit-book-short'),range=document.createRange();
  range.selectNodeContents(label);
  return {width:r.width,height:r.height,overflow:button.scrollWidth>button.clientWidth+1,lines:range.getClientRects().length,padding:parseFloat(style.paddingLeft)};
 });
 return {width:innerWidth,ticket,art,copy,print,layout:getComputedStyle(document.querySelector('.visit-copy')).gridRowStart,heading:rect('.visit-copy h3'),paragraph:rect('.visit-copy>p'),align:[...document.querySelectorAll('.visit-copy h3,.visit-copy>p')].map(e=>getComputedStyle(e).textAlign),buttons,mask:getComputedStyle(document.querySelector('.visit-surface')).maskImage};
})()'''

def mobile_case(width,zoom=1):
 call('set','viewport',str(width),'1000')
 js(f'document.documentElement.style.zoom={zoom}')
 center('.visit-ticket')
 row=js(MEASURE)
 midpoint=row['ticket']['y']+row['ticket']['h']/2
 if row['layout']=='1':
  assert abs(row['copy']['h']-row['ticket']['h'])<.2,row
  assert abs(row['print']['h']-row['ticket']['h'])<.2,row
  assert abs(row['art']['bottom']-row['ticket']['bottom'])<.2,row
  assert row['copy']['w']<=row['ticket']['w']*.51,row
 else:
  assert abs(row['art']['bottom']-midpoint)<.2,row
  assert abs(row['print']['bottom']-midpoint)<.2,row
  assert abs(row['copy']['y']-midpoint)<.2,row
  assert abs(row['copy']['h']-row['ticket']['h']/2)<.2,row
  assert row['heading']['y']>=midpoint and row['paragraph']['y']>=midpoint,row
 assert row['align']==['center','center'],row
 assert '50%' in row['mask'],row
 assert row['ticket']['x']>=0 and row['ticket']['x']+row['ticket']['w']<=width+.2,row
 for button in row['buttons']:
  assert not button['overflow'] and button['lines']==1 and button['padding']>=12,button
  assert button['height']>=44*zoom-.2,button
 return {'zoom':zoom,**row}

report={'mobile':[],'zoom':[],'desktop':[],'routes':[],'externalSubmission':False}
call('open','http://127.0.0.1:4321/?qa=35-regression');call('set','media','light','reduced-motion');settle()
for theme in ['light','dark']:
 call('select','.footer [data-theme-select]',theme)
 for width in [320,360,390,430,480,540,650,768,800,960]:
  report['mobile'].append({'theme':theme,**mobile_case(width)})
 print('PASS phone halves, tablet columns and centered text',theme,flush=True)
for width in [390,540,768]:
 for zoom in [.8,1.25,1.5,2]:
  report['zoom'].append(mobile_case(width,zoom))
print('PASS CSS zoom 80/125/150/200 percent',flush=True)
js('document.documentElement.style.removeProperty("zoom")')
call('select','.footer [data-theme-select]','light')
baseline=json.loads((ROOT/'tmp/planning/iteration35-before.json').read_text(encoding='utf-8'))
for width in [961,1024,1440,1920]:
 call('set','viewport',str(width),'1000');center('.visit-ticket');row=js(MEASURE)
 assert row['align']==['start','start'],row
 old=next((case for case in baseline if case['width']==width),None)
 if old:
  for key in ['art','copy','h3','paragraph']:
   current=row['heading'] if key=='h3' else row[key]
   for axis in ['w','h']:assert abs(current[axis]-old[key][axis])<.1,(width,key,axis,current,old[key])
   assert abs((current['x']-row['ticket']['x'])-(old[key]['x']-old['ticket']['x']))<.1,(width,key)
 report['desktop'].append(row)
print('PASS desktop alignment and saved component geometry',flush=True)
call('set','viewport','390','1000');center('.visit-actions')
for master,company in [('souz-sonya-kid','2266404'),('souz-svetlana','2440449')]:
 call('click',f'.visit-actions [data-master="{master}"]');settle()
 assert company in js('document.querySelector("[data-booking-frame]").getAttribute("src")')
 call('press','Escape');settle();report['routes'].append({'master':master,'company':company})
save('iteration35-first-visit',report)
print('PASS both personal booking destinations',flush=True)
