import{test}from'node:test';import assert from'node:assert/strict';import{readFileSync,readdirSync}from'node:fs';import postcss from'postcss';
test('a component has one declaration owner per selector and breakpoint',()=>{
 const conflicts=[];
 for(const file of readdirSync(new URL('../src/styles/',import.meta.url)).filter(name=>name.endsWith('.css'))){
  const rules=new Map();postcss.parse(readFileSync(new URL('../src/styles/'+file,import.meta.url),'utf8')).walkRules(rule=>{
   const conditions=[];for(let parent=rule.parent;parent&&parent.type!=='root';parent=parent.parent)if(parent.type==='atrule')conditions.unshift('@'+parent.name+parent.params.replace(/\s+/g,''));
   const key=conditions.join('|')+'|'+rule.selector.replace(/\s+/g,' ').trim(),previous=rules.get(key)||new Map();
   for(const node of rule.nodes.filter(node=>node.type==='decl')){if(previous.has(node.prop))conflicts.push({file,selector:rule.selector,conditions,property:node.prop,previous:previous.get(node.prop),next:node.value});previous.set(node.prop,node.value)}
   rules.set(key,previous);
  });
 }
 assert.deepEqual(conflicts,[]);
});

test('root scrolling has one modal owner and no competing overflow lock',()=>{
 const fixed=[];
 for(const file of readdirSync(new URL('../src/styles/',import.meta.url)).filter(name=>name.endsWith('.css'))){
  postcss.parse(readFileSync(new URL('../src/styles/'+file,import.meta.url),'utf8')).walkRules(rule=>{
   const rootSubject=rule.selectors.some(selector=>/^(?:html|body|:root)(?=[.#[:]|$)/.test(selector.replace(/:(?:has|is|where|not)\([^)]*\)/g,'').trim().split(/\s+|[>+~]/).at(-1)));
   if(!rootSubject)return;
   for(const decl of rule.nodes.filter(node=>node.type==='decl')){
    if(/^overflow(?:-[xy])?$/.test(decl.prop)&&/\bhidden\b/.test(decl.value))assert.deepEqual([file,rule.selector,decl.prop,decl.value],['system.css','body[data-modal-scroll-locked]','overflow','hidden'],'Only the shared fixed body may own the modal scrollport');
    if(decl.prop==='position'&&decl.value==='fixed')fixed.push([file,rule.selector]);
   }
  });
 }
 assert.deepEqual(fixed,[['system.css','body[data-modal-scroll-locked]']]);
 const system=readFileSync(new URL('../src/styles/system.css',import.meta.url),'utf8');
 assert.match(system,/:root\s*\{[^}]*overflow-y:\s*scroll\s*;/,'Root gutter stays present throughout modal ownership');
 for(const file of readdirSync(new URL('../src/scripts/',import.meta.url)).filter(name=>name.endsWith('.ts'))){
  const source=readFileSync(new URL('../src/scripts/'+file,import.meta.url),'utf8'),aliases=['document\\.body','document\\.documentElement'];
  for(const match of source.matchAll(/(?:const|let)\s+([\w$]+)\s*=\s*document\.(?:body|documentElement)\b/g))aliases.push(match[1]);
  for(const alias of aliases)assert.doesNotMatch(source,new RegExp('\\b'+alias+'\\.style\\s*(?:\\.overflow(?:X|Y)?\\s*=|\\.setProperty\\(\\s*["\u0027]overflow(?:-[xy])?["\u0027])'),file+' must use the shared modal owner');
  if(/\.dataset\.modalScrollLocked\s*=/.test(source))assert.equal(file,'modal-scroll-lock.ts');
 }
});
