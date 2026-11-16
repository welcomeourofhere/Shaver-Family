import{test}from'node:test';import assert from'node:assert/strict';import{readFileSync,readdirSync,existsSync,statSync}from'node:fs';import{resolve,dirname}from'node:path';
const root=resolve('dist'),pages=[];
function crawl(folder){for(const item of readdirSync(folder,{withFileTypes:true})){const path=resolve(folder,item.name);if(item.isDirectory())crawl(path);else if(item.name.endsWith('.html'))pages.push(path)}}crawl(root);
function attributes(html){return[...html.matchAll(/<[a-z][^>]*>/gi)].map(([tag])=>Object.fromEntries([...tag.matchAll(/([\w:-]+)="([^"]*)"/g)].map(([,name,value])=>[name,value.replaceAll('&amp;','&')])))}
const documents=new Map(pages.map(page=>[page,attributes(readFileSync(page,'utf8'))]));
test('built pages keep unique accessible IDs and resolve every internal reference and local asset',()=>{
 const errors=[];
 for(const[page,nodes]of documents){
  const ids=new Set();for(const node of nodes)if(node.id){if(ids.has(node.id))errors.push({page,id:node.id,error:'Duplicate ID'});ids.add(node.id)}
  for(const node of nodes){
   for(const role of['aria-labelledby','aria-describedby','aria-controls'])for(const id of(node[role]||'').split(/\s+/).filter(Boolean))if(!ids.has(id))errors.push({page,role,id,error:'Missing accessible target'});
   const urls=[node.href,node.src,node.poster,...(node.srcset||'').split(',').map(value=>value.trim().split(/\s+/)[0])].filter(Boolean);
   for(const raw of urls){if(/^(?:https?:|mailto:|tel:|data:|blob:)/.test(raw)||raw==='/'||raw==='#')continue;
    const url=new URL(raw,'https://local.invalid/'+page.slice(root.length+1).replaceAll('\\','/')),path=resolve(root,decodeURIComponent(url.pathname).replace(/^\//,''));
    const file=existsSync(path)&&statSync(path).isDirectory()?resolve(path,'index.html'):path;
    if(!existsSync(file))errors.push({page,url:raw,error:'Missing local destination'});
    else if(url.hash&&file.endsWith('.html')){const target=decodeURIComponent(url.hash.slice(1)),targetNodes=documents.get(file)||[];if(!targetNodes.some(node=>node.id===target))errors.push({page,url:raw,error:'Missing fragment destination'})}
   }
  }
 }
 assert.ok(pages.length>=5);assert.deepEqual(errors,[]);
});
