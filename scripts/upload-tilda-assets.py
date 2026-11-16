"""Upload and publicly verify the exact SOYUZ release manifest using an existing profile."""
import argparse,concurrent.futures,hashlib,json,subprocess,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()

class ImmutableConflict(ValueError):pass

def save_report(report,payload):
    temporary=report.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    for attempt in range(5):
        try:temporary.replace(report);return
        except PermissionError:
            if attempt==4:raise
            time.sleep(.15*(attempt+1))
def public_read(row):
    with urlopen(Request(row['url'],headers={'Accept-Encoding':'identity'}),timeout=45)as response:
        body=response.read();headers=response.headers
    if sha(body)!=row['sha256']:raise ImmutableConflict('Existing immutable object has different bytes: '+row['key'])
    return headers.get('Content-Type','').split(';')[0]==row['contentType']and headers.get('Content-Encoding')==row['contentEncoding']and'immutable'in headers.get('Cache-Control','')
def upload(row,profile,apply):
    source=(ROOT/row['file']).resolve()
    assert source.is_relative_to((ROOT/'deploy/out').resolve())and source.is_file()
    assert row['key'].startswith('Soyuz/releases/')and row['url']=='https://storage.yandexcloud.net/shaver/'+row['key']
    assert sha(source.read_bytes())==row['sha256']
    if not apply:return {'key':row['key'],'status':'dry-run'}
    for attempt in range(3):
        try:
            try:
                if public_read(row):return {'key':row['key'],'status':'verified','sha256':row['sha256']}
            except HTTPError as error:
                if error.code not in (403,404):raise
            command=['aws','--profile',profile,'--endpoint-url','https://storage.yandexcloud.net','s3','cp',str(source),'s3://shaver/'+row['key'],'--content-type',row['contentType'],'--cache-control',row['cacheControl'],'--only-show-errors']
            if row['contentEncoding']:command+=['--content-encoding',row['contentEncoding']]
            subprocess.run(command,check=True,capture_output=True,timeout=120)
            if not public_read(row):raise ValueError('Public bytes or HTTP metadata mismatch')
            return {'key':row['key'],'status':'uploaded','sha256':row['sha256']}
        except ImmutableConflict as error:
            return {'key':row['key'],'status':'failed','error':type(error).__name__,'details':str(error)[:180]}
        except Exception as error:
            if attempt==2:return {'key':row['key'],'status':'failed','error':type(error).__name__,'details':str(error)[:180]}
            time.sleep(attempt+1)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    pointer=json.loads((ROOT/'deploy/current.json').read_text());manifest_path=ROOT/pointer['manifest'];manifest_bytes=manifest_path.read_bytes();manifest=json.loads(manifest_bytes)
    assert manifest['projectId']==46815509 and manifest['origin']=='https://soyuz.hair'and manifest['bucket']=='shaver'
    assert manifest['prefix']=='Soyuz/releases/'+manifest['build']+'/'
    config=json.loads((ROOT/'deploy/production.json').read_text(encoding='utf-8'));rows=[]
    report=manifest_path.parent/'upload-report.json'
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)as pool:
        futures=[pool.submit(upload,row,config['awsProfile'],args.apply)for row in manifest['files']]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result());payload={'build':manifest['build'],'applied':args.apply,'total':len(manifest['files']),'results':rows,'manifestUnchanged':manifest_path.read_bytes()==manifest_bytes,'complete':len(rows)==len(futures),'ok':len(rows)==len(futures)and all(r['status']in ('verified','uploaded')for r in rows)}
            if len(rows)%20==0 or rows[-1]['status']=='failed' or len(rows)==len(futures):save_report(report,payload)
            if len(rows)%20==0 or rows[-1]['status']=='failed':print(len(rows),'/',len(futures),rows[-1]['status'],rows[-1]['key'],flush=True)
    assert manifest_path.read_bytes()==manifest_bytes
    if args.apply:assert all(r['status']in ('verified','uploaded')for r in rows),'Asset publication failed; see upload-report.json'
    print('PASS',len(rows),'public assets'if args.apply else'dry-run assets')
if __name__=='__main__':main()
