"""Check real published responses and platform metadata without disabling TLS validation."""
import argparse,json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--origin',default='https://soyuz.hair');parser.add_argument('--output-dir',type=Path);args=parser.parse_args();origin=args.origin.rstrip('/');assert origin in ['https://soyuz.hair','https://stay-tan-habanero.tilda.ws']
manifest_path=ROOT/json.loads((ROOT/'deploy/current.json').read_text())['manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'));rows=[]
for page in manifest['pages']:
 route='/'+page['alias']if page['route']=='/404'else page['route'];response=urlopen(origin+route,timeout=20);soup=BeautifulSoup(response.read(),'html.parser')
 assert response.status==200 and len(soup.select('h1'))==1 and soup.title.get_text()==page['title'],route
 assert len(soup.select('link[rel=canonical]'))==1 and soup.select_one('link[rel=canonical]')['href']==page['canonical'],route
 assert len(soup.select('meta[name=description]'))==1 and soup.select_one('meta[name=description]')['content']==page['description'],route
 for name in ['og:title','og:description','og:url','og:type','og:image']:assert len(soup.find_all('meta',property=name))==1,(route,name)
 source_head=BeautifulSoup((manifest_path.parent/page['headFile']).read_text(encoding='utf-8'),'html.parser')
 source_body=BeautifulSoup((manifest_path.parent/page['codeFile']).read_text(encoding='utf-8'),'html.parser')
 required={tag.get(attribute)for doc in(source_head,source_body)for tag in doc.find_all(['link','script'])for attribute in('href','src')if(tag.get(attribute)or'').startswith('https://storage.yandexcloud.net/shaver/Soyuz/releases/')}
 actual={tag.get(attribute)for tag in soup.find_all(['link','script'])for attribute in('href','src')}
 assert required and required<=actual,(route,'Published resources do not match the candidate',sorted(required-actual))
 for expected in source_head.find_all('meta',attrs={'name':lambda value:value and value.startswith('twitter:')}):
  tags=soup.find_all('meta',attrs={'name':expected['name']})
  assert len(tags)==1 and tags[0].get('content')==expected.get('content'),(route,expected['name'])
 assert soup.html.get('lang')=='ru'and all(image.has_attr('alt')for image in soup.select('main img')),(route,'Language/own image alt')
 if page['noindex']:assert any('noindex'in tag['content']for tag in soup.select('meta[name=robots]'))
 else:assert not any('noindex'in tag['content']for tag in soup.select('meta[name=robots]'))
 assert 'G-9GCNDWN2P9'not in str(soup)and '106175596'not in str(soup)
 assert 'G-TF121LKSEQ'in str(soup)and '114263185'in str(soup)
 rows.append({'route':route,'status':response.status,'metadataUnique':True,'canonical':True,'ownCounters':True,'candidateResources':len(required),'twitterUniqueAndCurrent':True,'langAndAlt':True})
try:urlopen(origin+'/release63-missing-page',timeout=20)
except HTTPError as error:
 soup=BeautifulSoup(error.read(),'html.parser');assert error.code==404 and soup.title.get_text()=='Страница не найдена — Барбершоп СОЮЗ, Киров';assert 'noindex'in soup.select_one('meta[name=robots]')['content'];rows.append({'missingStatus':404,'own404':True})
else:raise AssertionError('Missing page returned a successful response')
home=BeautifulSoup(urlopen(origin+'/',timeout=20).read(),'html.parser')
assert home.select_one('meta[name=google-site-verification]')['content']=='MmQQFIhbtKcfhtNTO_oVJJC31nq5u-oQby_P7IAPsXA'
assert home.select_one('meta[name=yandex-verification]')['content']=='456eed219e008bca'
assert 'data-news-id='not in str(home)
out=args.output_dir or ROOT/'tmp/planning/releases'/manifest['build'];out.mkdir(parents=True,exist_ok=True);label='public'if origin=='https://soyuz.hair'else'technical';(out/f'routes-{label}.json').write_text(json.dumps({'origin':origin,'build':manifest['build'],'cases':rows,'verificationMeta':True,'postsNotInHTML':True},indent=2),encoding='utf-8',newline='');print('PASS',len(rows),label,'published candidate routes, unique metadata, resources, counters, verification and 404')
