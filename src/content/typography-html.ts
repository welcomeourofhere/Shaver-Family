import {parseFragment,type DefaultTreeAdapterMap} from 'parse5';
import {bindRuns,typographyBlocks as blocks,typographyExcludedTags as excluded} from '../scripts/typography-rules.ts';

type Element=DefaultTreeAdapterMap['element'];
type Text=DefaultTreeAdapterMap['textNode'];
const escape=(text:string)=>text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');

/** Bind the initial HTML with the same rules as live content, before its first layout. */
export function typographyHTML(html:string){
 const root=parseFragment(html,{sourceCodeLocationInfo:true}),edits:{start:number;end:number;text:string}[]=[];
 let run:Text[]=[],heading=false;
 const flush=()=>{const values=bindRuns(run.map(node=>node.value),heading);run.forEach((node,i)=>{const loc=node.sourceCodeLocation;if(loc&&values[i]!==node.value)edits.push({start:loc.startOffset,end:loc.endOffset,text:escape(values[i])})});run=[]};
 function visit(element:DefaultTreeAdapterMap['parentNode'],inHeading=false){
  for(const node of element.childNodes){
   if(node.nodeName==='#text'){heading=inHeading;run.push(node as Text);continue;}
   if(!('tagName' in node))continue;
   const child=node as Element,tag=child.tagName;
   const skip=excluded.has(tag)||child.attrs.some(a=>a.name==='data-typography'&&a.value==='off'||a.name==='contenteditable'&&a.value!=='false');
   if(skip||tag==='br'){flush();continue;}
   if(blocks.has(tag)){flush();visit(child,inHeading||/^h[1-6]$/.test(tag));flush();}else visit(child,inHeading);
  }
 }
 visit(root);flush();
 for(const edit of edits.sort((a,b)=>b.start-a.start))html=html.slice(0,edit.start)+edit.text+html.slice(edit.end);
 return html;
}
