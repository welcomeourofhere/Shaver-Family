import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

// agent-browser has no web touch gesture command; CDP supplies real browser input.
export async function touchBrowser() {
  const cli=['node_modules/agent-browser/bin/agent-browser.js','--session',process.env.QA_BROWSER_SESSION||'soyuz37-touch','--json'];
  const options={encoding:'utf8',timeout:15000,env:{...process.env,AGENT_BROWSER_SOCKET_DIR:resolve(process.env.QA_BROWSER_SOCKET_DIR||'.local/browser-qa')}};
  execFileSync(process.execPath,[...cli,'open','about:blank'],{...options,stdio:'ignore'});
  const output=execFileSync(process.execPath,[...cli,'get','cdp-url'],options);
  const endpoint=JSON.parse(output).data.cdpUrl;
  const socket=new WebSocket(endpoint),pending=new Map(),events=new Map();let sequence=0,pageSession='';
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  socket.addEventListener('message',event=>{
    const message=JSON.parse(event.data);
    if(message.method&&message.sessionId===pageSession){for(const listener of events.get(message.method)||[])listener(message.params);return;}
    const request=pending.get(message.id);
    if(!request)return;pending.delete(message.id);clearTimeout(request.timer);
    if(message.error)request.reject(new Error(JSON.stringify(message.error)));else request.resolve(message.result);
  });
  function command(method,params={},sessionId) {
    return new Promise((resolve,reject)=>{
      const id=++sequence,timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method));},15000);
      pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params,sessionId}));
    });
  }
  const {targetId}=await command('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await command('Target.attachToTarget',{targetId,flatten:true});
  pageSession=sessionId;
  const send=(method,params={})=>command(method,params,sessionId);
  await send('Page.enable');await send('Runtime.enable');
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__touchErrors=[];window.__touchTrace=[];addEventListener('error',e=>__touchErrors.push(e.message));addEventListener('unhandledrejection',e=>__touchErrors.push(String(e.reason)));for(const type of ['pointerdown','pointercancel','pointerup','click'])addEventListener(type,e=>__touchTrace.push({type,pointer:e.pointerType,trusted:e.isTrusted,target:e.target.className}),true);`});
  async function evaluate(expression) {
    const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(result.exceptionDetails)throw new Error(result.exceptionDetails.text+': '+result.exceptionDetails.exception?.description);
    return result.result.value;
  }
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  async function until(expression) {
    for(let i=0;i<100;i++){if(await evaluate(expression))return;await pause(100);}throw new Error('Condition timeout: '+expression);
  }
  async function settle() {
    await evaluate(`document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))`);
    await evaluate(`Promise.allSettled(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getTiming().iterations)&&a.animationName!=='hero-photo-zoom').map(a=>a.finished))`);
  }
  async function viewport(width,height,reduced=false) {
    await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:true});
    await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5});
    await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:reduced?'reduce':'no-preference'}]});
  }
  async function open(url) {await send('Page.navigate',{url});await until(`document.readyState==='complete'&&!!document.querySelector('.of-rail[data-loop-ready]')`);await settle();}
  async function center(selector) {await evaluate(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'center',inline:'center',behavior:'instant'})`);await settle();}
  async function point(selector,x=.5,y=.5) {
    return evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect(),top=Math.max(r.height>150?100:10,r.top),bottom=Math.min(innerHeight-120,r.bottom);return{x:r.left+r.width*${x},y:Math.max(top+1,Math.min(bottom-1,r.top+r.height*${y}))}})()`);
  }
  async function swipe(start,dx,dy=0,cancel=false) {
    const touches=(x,y)=>[{x,y,id:1,radiusX:5,radiusY:5,force:1}];
    await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:touches(start.x,start.y)});
    for(let step=1;step<=12;step++){
      await send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:touches(start.x+dx*step/12,start.y+dy*step/12)});await pause(16);
    }
    await send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]});await pause(550);await settle();
  }
  async function tap(p) {await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...p,id:1}]});await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await settle();}
  const on=(method,listener)=>{if(!events.has(method))events.set(method,new Set());events.get(method).add(listener);return()=>events.get(method)?.delete(listener)};
  return {send,on,evaluate,pause,until,settle,viewport,open,center,point,swipe,tap,close:async()=>{try{await command('Target.closeTarget',{targetId});}finally{socket.close();}}};
}
