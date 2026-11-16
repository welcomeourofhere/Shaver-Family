import {execFile} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

// The local preview has the same last-successful-snapshot contract as the scheduled static delivery.
export function vkNewsPreview(){
 const root=fileURLToPath(new URL('../',import.meta.url)),feed=new URL('../public/data/news.json',import.meta.url);
 let pending=null,lastAttempt=0;
 const refresh=()=>{
  if(pending||Date.now()-lastAttempt<300000)return;lastAttempt=Date.now();
  pending=new Promise(resolve=>execFile('python',['-X','utf8',fileURLToPath(new URL('./sync-vk-news-snapshot.py',import.meta.url)),'--public-only'],{cwd:root,windowsHide:true,timeout:180000},error=>{
   if(error)process.stderr.write('VK refresh unavailable; last successful snapshot retained.\n');
   pending=null;resolve();
  }));
 };
 return {name:'soyuz-public-vk-preview',configureServer(server){
  server.middlewares.use((request,response,next)=>{
   if(request.method!=='GET'||request.url?.split('?')[0]!=='/data/news.json'){next();return;}
   refresh();
   void readFile(feed).then(body=>{response.setHeader('Content-Type','application/json; charset=utf-8');response.setHeader('Cache-Control','no-cache');response.end(body)}).catch(()=>next());
  });
 }};
}
