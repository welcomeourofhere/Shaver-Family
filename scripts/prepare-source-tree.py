"""Prepare an explicit SOYUZ-only Git tree and an optional empty CI rehearsal folder."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES=('src','content','scripts','tests','deploy','docs','integrations','tilda-import')
ROOT_FILES=('AGENTS.md','README.md','.gitignore','.gitattributes','package.json','pnpm-lock.yaml','pnpm-workspace.yaml','astro.config.mjs','tsconfig.json','dev.cmd','build.cmd')
SUFFIXES={'.astro','.ts','.mjs','.js','.css','.json','.md','.py','.txt','.yaml','.yml','.svg','.cmd'}
SOURCE_EXCEPTIONS={'content/third-party/lucide/LICENSE','public/brand/lucide-LICENSE.txt','deploy/project-head.html'}

def excluded(path,prefixes):
 return any(path==prefix.rstrip('/')or path.startswith(prefix.rstrip('/')+'/')for prefix in prefixes)or any(part in ('__pycache__','.git')for part in Path(path).parts)

def source_files(root):
 config=json.loads((root/'tests/ci-suites.json').read_text(encoding='utf-8'));paths=set(ROOT_FILES)|SOURCE_EXCEPTIONS
 for directory in DIRECTORIES:
  paths.update(p.relative_to(root).as_posix()for p in (root/directory).rglob('*')if p.is_file()and p.suffix in SUFFIXES and(directory!='docs'or p.suffix=='.md'))
 paths.add('.github/workflows/soyuz-website.yml')
 # These are authored glyphs, not copies of binary delivery resources.
 lock=json.loads((root/'deploy/media-lock.json').read_text(encoding='utf-8'))
 paths.update('public/'+r['sourcePath']for r in lock['files']if Path(r['sourcePath']).suffix=='.svg')
 selected=sorted(path for path in paths if not excluded(path,config['productionSourceExcludes']))
 for path in selected:
  file=(root/path).resolve()
  if not file.is_relative_to(root.resolve())or not file.is_file():raise ValueError('Invalid source path: '+path)
  if file.suffix not in SUFFIXES and path not in ROOT_FILES and path not in SOURCE_EXCEPTIONS:raise ValueError('Unapproved source type: '+path)
 return selected

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'.local/release65/github-tree.json');parser.add_argument('--materialize',type=Path);args=parser.parse_args()
 output=args.output.resolve()
 if not output.is_relative_to((ROOT/'.local').resolve()):raise ValueError('Payload must stay in workspace/.local')
 destination=args.materialize.resolve()if args.materialize else None
 if destination and(not destination.is_relative_to((ROOT/'.local').resolve())or destination.exists()):raise ValueError('Use a new empty path under workspace/.local')
 entries=[]
 for path in source_files(ROOT):
  content=(ROOT/path).read_bytes().decode('utf-8');entries.append({'path':path,'mode':'100644','type':'blob','content':content})
  if destination:
   target=destination/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8',newline='')
 output.parent.mkdir(parents=True,exist_ok=True);body=json.dumps(entries,ensure_ascii=False,separators=(',',':'));output.write_text(body,encoding='utf-8')
 summary={'files':len(entries),'characters':sum(len(r['content'])for r in entries),'sha256':hashlib.sha256(body.encode()).hexdigest(),'productionOnly':True}
 output.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
