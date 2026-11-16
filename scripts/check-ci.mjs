import assert from 'node:assert/strict';
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {resolve,relative,sep,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import ts from 'typescript';

const root=fileURLToPath(new URL('../',import.meta.url)),tests=resolve(root,'tests');
const config=JSON.parse(readFileSync(resolve(tests,'ci-suites.json'),'utf8'));
const suite=process.argv[2]??'runtime',entryFile=entry=>typeof entry==='string'?entry:entry.file;
const runtime=config.runtime.map(entryFile),local=config.localProvenance.map(entryFile),classified=[...runtime,...local];
assert.equal(config.schemaVersion,1);
assert.equal(new Set(classified).size,classified.length,'A test must have exactly one CI owner');
assert.deepEqual([...classified].sort(),readdirSync(tests).filter(name=>name.endsWith('.test.mjs')).sort(),'Classify every new unit test explicitly');
assert.deepEqual([...config.packagePython].sort(),readdirSync(tests).filter(name=>name.endsWith('_test.py')).sort(),'Classify every Python test explicitly');
for(const entry of config.localProvenance)assert.ok(entry.reason?.length>20,entry.file);
function caseNames(file){
 const source=ts.createSourceFile(file,readFileSync(resolve(tests,file),'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),names=[];
 function visit(node){if(ts.isCallExpression(node)&&ts.isIdentifier(node.expression)&&node.expression.text==='test'){assert.ok(ts.isStringLiteralLike(node.arguments[0]),`Filtered suites need explicit case names: ${file}`);names.push(node.arguments[0].text)}ts.forEachChild(node,visit)}
 visit(source);return names;
}
for(const entry of config.runtime.filter(entry=>typeof entry!=='string'))for(const test of entry.localCases){
 assert.ok(test.reason?.length>20,test.name);
 assert.ok(caseNames(entry.file).includes(test.name),`Stale local-case name: ${entry.file}: ${test.name}`);
}
for(const name of [...classified,...config.release,...config.packagePython])assert.ok(/^[\w.-]+\.(?:mjs|py)$/.test(name)&&existsSync(resolve(tests,name)),name);

function run(command,args,expectedNames=[]){
 const result=spawnSync(command,args,{cwd:root,encoding:'utf8',maxBuffer:10*1024*1024});
 process.stdout.write(result.stdout??'');process.stderr.write(result.stderr??'');
 assert.equal(result.error,undefined,result.error?.message);
 assert.equal(result.status,0,`${command} ${args.join(' ')} failed`);
 if(command===process.execPath)assert.match(result.stdout,/^# pass [1-9]\d*$/m,'The selected suite must actually execute tests');
 for(const name of expectedNames)assert.ok(result.stdout.split(/\r?\n/).includes('# Subtest: '+name),'Selected runtime case did not execute: '+name);
}
const escape=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
if(suite==='check')console.log(`PASS CI ownership: ${runtime.length} runtime suites, ${local.length} local provenance suites, ${config.packagePython.length} Python suites`);
else if(suite==='source'){
 for(const path of config.productionForbiddenInputs)assert.ok(!existsSync(resolve(root,path)),`Production source excludes ${path}; keep this input in the local workspace only`);
 const lock=JSON.parse(readFileSync(resolve(root,'deploy/media-lock.json'),'utf8')),seen=new Set();
 for(const row of lock.files){
  const path=resolve(root,'public',row.sourcePath),rel=relative(resolve(root,'public'),path);
  assert.ok(rel&&!isAbsolute(rel)&&!rel.startsWith('..'+sep)&&rel!=='..'&&!rel.includes(':')&&!row.sourcePath.includes('\\')&&!seen.has(rel),row.sourcePath);seen.add(rel);
  assert.match(row.url,/^https:\/\/storage\.yandexcloud\.net\/shaver\/Soyuz\/releases\//);
  assert.equal(createHash('sha256').update(readFileSync(path)).digest('hex'),row.sourceSha256,row.sourcePath);
 }
 console.log(`PASS production source boundary and ${seen.size} restored public asset hashes`);
}else if(suite==='runtime'){
 run(process.execPath,['--test','--test-reporter=tap',...config.runtime.filter(entry=>typeof entry==='string').map(name=>'tests/'+name)]);
 for(const entry of config.runtime.filter(entry=>typeof entry!=='string')){
  const names=caseNames(entry.file).filter(name=>!entry.localCases.some(test=>test.name===name));assert.ok(names.length,'Filtered runtime suite cannot be empty: '+entry.file);
  const pattern='^(?:'+names.map(escape).join('|')+')$';
  console.log(`CI ${entry.file}: ${entry.localCases.length} explicitly named original-source cases remain local`);
  run(process.execPath,['--test','--test-reporter=tap','--test-name-pattern='+pattern,'tests/'+entry.file],names);
 }
}else if(suite==='release')run(process.execPath,['--test','--test-reporter=tap',...config.release.map(name=>'tests/'+name)]);
else if(suite==='package')for(const name of config.packagePython)run(process.env.PYTHON??'python',['-X','utf8','-m','unittest','discover','-s','tests','-p',name]);
else throw new Error('Unknown CI suite: '+suite);
