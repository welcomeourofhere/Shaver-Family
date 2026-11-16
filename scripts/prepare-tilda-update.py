"""Prepare exact, source-owned Tilda changes after verifying the uploaded release graph.

This writes a local payload only. Read-back, remote preconditions and publication remain
separate actions; the published registry is never advanced by this command.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def prepare(root,require_uploaded=True):
 pointer=json.loads((root/'deploy/current.json').read_text(encoding='utf-8'))
 folder=(root/pointer['manifest']).resolve()
 if not folder.is_relative_to((root/'deploy/out').resolve()):raise ValueError('Manifest outside deployment output')
 data=folder.read_bytes();manifest=json.loads(data);folder=folder.parent
 registry=json.loads((root/'deploy/tilda-pages.json').read_text(encoding='utf-8'))
 config=json.loads((root/'deploy/production.json').read_text(encoding='utf-8'))
 if config['projectId']!=46815509 or manifest['projectId']!=config['projectId']or registry['projectId']!=manifest['projectId']or manifest['origin']!=config['origin']or config['origin']!='https://soyuz.hair'or manifest['build']!=pointer['build']:raise ValueError('Unexpected deployment target')
 if require_uploaded:
  report=json.loads((folder/'upload-report.json').read_text(encoding='utf-8'))
  expected={(r['key'],r['sha256'])for r in manifest['files']}
  actual={(r['key'],r.get('sha256'))for r in report['results']if r['status']in('verified','uploaded')}
  if len(expected)!=len(manifest['files'])or len(report['results'])!=len(expected)or not report.get('applied')or not report.get('complete')or not report.get('ok')or report.get('build')!=manifest['build']or report.get('total')!=len(expected)or actual!=expected:raise ValueError('Complete public asset verification required')
 sources={r['route']:r for r in manifest['pages']}
 sources.update({'/soyuz-'+kind:{**row,'sharedKind':kind}for kind,row in manifest['shared'].items()})
 expected_routes=set(config['pages'])|{'/soyuz-header','/soyuz-footer'}
 if set(manifest['shared'])!={'header','footer'}or set(sources)!=expected_routes or len(registry['pages'])!=len(expected_routes)or {r['route']for r in registry['pages']}!=expected_routes:raise ValueError('Configured content and shared targets required')
 if len({r['pageid']for r in registry['pages']})!=len(expected_routes)or len({r['recordid']for r in registry['pages']})!=len(expected_routes):raise ValueError('Duplicate native target')
 rows=[]
 for target in registry['pages']:
  source=sources[target['route']];row={k:target[k]for k in('route','pageid','recordid','alias')}
  if source['alias']!=target['alias']:raise ValueError('Native alias mismatch')
  row['expectedBefore']={k:target[k]for k in('headSha256','codeSha256')}
  for field,file_key,hash_key in [('head','headFile','headSha256'),('code','codeFile','codeSha256')]:
   path=(folder/source[file_key]).resolve()
   if not path.is_relative_to(folder):raise ValueError('Page outside package')
   body=path.read_bytes()
   if sha(body)!=source[hash_key]:raise ValueError('Page bytes differ from manifest')
   row[field]=body.decode('utf-8');row[hash_key]=source[hash_key]
  if 'sharedKind'in source:row['sharedKind']=source['sharedKind']
  rows.append(row)
 rows.sort(key=lambda r:(0 if r.get('sharedKind')=='header'else 1 if r.get('sharedKind')=='footer'else 2))
 return{'projectId':manifest['projectId'],'build':manifest['build'],'previousPublishedBuild':registry['build'],'manifestSha256':sha(data),'projectHeadSha256':sha((root/'deploy/project-head.html').read_bytes()),'assetsVerified':require_uploaded,'rows':rows}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'.local/release65/tilda-update.json');parser.add_argument('--allow-unuploaded',action='store_true');args=parser.parse_args()
 output=args.output.resolve()
 if not output.is_relative_to((ROOT/'.local').resolve()):raise ValueError('Keep local operation payload under .local')
 payload=prepare(ROOT,not args.allow_unuploaded);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print(json.dumps({k:payload[k]for k in('projectId','build','previousPublishedBuild','assetsVerified')}|{'pages':len(payload['rows']),'payloadSha256':sha(output.read_bytes()),'externalWrites':False}))
if __name__=='__main__':main()
