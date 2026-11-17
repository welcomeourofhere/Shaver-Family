import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import postcss from 'postcss';
const read=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
const css=read('src/styles/works.css'),rules=postcss.parse(css);
function properties(width){
 const values={};
 rules.walkRules(rule=>{if(rule.selector!=='.works')return;for(let parent=rule.parent;parent.type!=='root';parent=parent.parent){if(parent.type==='atrule'&&parent.name==='media'){const max=parent.params.match(/max-width:\s*(\d+)px/);if(max&&width>Number(max[1]))return;}}for(const decl of rule.nodes.filter(node=>node.type==='decl'))values[decl.prop]=decl.value;});
 return values;
}

test('mobile fan projects both neighbours to the shell edges without widening the centre',()=>{
 for(const width of[320,360,361,390,420,421,540,600]){
  const p=properties(width),shell=width-2*Math.max(10,Math.min(20,width*.016667));
  const [,minimum,percent,maximum]=p['--works-card-width'].match(/clamp\(var\(--size-(\d+)\),(\d+)cqi,var\(--size-(\d+)\)\)/);
  const card=Math.max(Number(minimum),Math.min(Number(maximum),shell*Number(percent)/100));
  const scale=Number(p['--works-neighbor-scale']),angle=width<=360?2:width<=420?3:4;
  const projected=card*scale*(Math.cos(angle*Math.PI/180)+4/3*Math.sin(angle*Math.PI/180));
  const step=(shell-card*scale*Number(p['--works-neighbor-width-factor']))/2;
  assert.ok(Math.abs(shell/2-step-projected/2)<.001,{width,shell,card,projected,step});
  assert.ok(Math.abs(shell/2+step+projected/2-shell)<.001,{width,shell,card,projected,step});
  assert.ok(card<=shell&&step>0&&projected<shell);
 }
 assert.match(css,/--works-step:calc\(\(100cqi - var\(--works-card-width\) \* var\(--works-neighbor-scale\) \* var\(--works-neighbor-width-factor\)\) \/ 2\)/);
});

test('smaller phones use smaller and less tilted neighbours while 1/2/3/4 depth remains intact',()=>{
 assert.deepEqual([320,390,540].map(width=>Number(properties(width)['--works-neighbor-scale'])),[.78,.82,.86]);
 assert.deepEqual([320,600,601,800,801,1100,1101,1440].map(width=>Number(properties(width)['--works-neighbor-limit'])),[1,1,2,2,3,3,4,4]);
 assert.match(css,/@media\(max-width:600px\)[\s\S]*?\.work-card \{[^}]*rotateZ\([^}]*var\(--works-neighbor-angle\)/);
 assert.match(css,/touch-action:pan-y pinch-zoom/);
});

test('mobile caption rhythm keeps intrinsic text reserve and a stable unscaled current hit area',()=>{
 assert.match(css,/\.works-fan \{ block-size:calc\(var\(--works-card-width\) \* 4 \/ 3 \+ var\(--size-48\)\); \}/);
 assert.match(css,/\.works-caption \{ min-block-size:var\(--size-64\); \}/);
 assert.match(css,/\.works-controls \{ margin-block-start:var\(--size-8\); \}/);
 assert.match(css,/scale\(calc\(1 - min\(var\(--work-distance\),1\) \* \(1 - var\(--works-neighbor-scale\)\)\)\)/);
 assert.match(css,/\.works-caption-current,\.works-caption-reserve/);
});

const masters=read('src/components/Masters.astro'),source=masters.match(/<script is:inline>([\s\S]*?)<\/script>/)[1];
function entry(random){
 class HTMLElement{constructor(id){this.id=id;this.children=[];}append(...cards){this.children=cards;}}
 const rail=new HTMLElement('masters-rail'),cards=Array.from({length:6},(_,index)=>({id:index,booking:`company-${index}`,story:`story-${index}`,color:`color-${index}`}));rail.children=[...cards];
 runInNewContext(source,{document:{currentScript:{previousElementSibling:rail}},HTMLElement,Math:Object.assign(Object.create(Math),{random})});
 return {rail,cards};
}

test('entry shuffle moves each existing master once without changing identity, booking, story or colour',()=>{
 for(const random of[()=>0,()=>.25,()=>.5,()=>.999]){
  const {rail,cards}=entry(random);
  assert.equal(rail.children.length,6);assert.equal(new Set(rail.children).size,6);
  assert.deepEqual(rail.children.map(card=>card.id).sort(),[0,1,2,3,4,5]);
  for(const card of rail.children){assert.equal(card,cards[card.id]);assert.equal(card.booking,`company-${card.id}`);assert.equal(card.story,`story-${card.id}`);assert.equal(card.color,`color-${card.id}`);}
 }
 assert.notDeepEqual(entry(()=>0).rail.children.map(card=>card.id),entry(()=>.999).rail.children.map(card=>card.id));
});

test('entry shuffle is parser-time between the complete SSR rail and its controls',()=>{
 assert.match(masters,/<\/div>\s*<script is:inline>[\s\S]*?<\/script>\s*<RailControls id="masters-rail"/);
 assert.match(source,/document\.currentScript\.previousElementSibling/);
 assert.ok(!/localStorage|sessionStorage|data-booking|cloneNode|style\s*=/.test(source));
 assert.match(read('src/scripts/team.ts'),/cards=\[\.\.\.rail\.querySelectorAll<HTMLElement>\('\.team-card'\)\]/);
});
