"""Release boundary, asset completeness, reproducible bytes and Tilda CSS isolation."""
import gzip,hashlib,importlib.util,json,re,unittest
from unittest.mock import patch
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import posixpath
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package',ROOT/'scripts/prepare-tilda-release.py');package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)

class ReleasePackageTest(unittest.TestCase):
 def test_asset_mime_is_portable_and_part_of_immutable_binary_identity(self):
  with patch('mimetypes.guess_type',return_value=('application/octet-stream',None)):
   for path,mime in [('photo.webp','image/webp'),('font.woff2','font/woff2'),('font.woff','font/woff'),('font.ttf','font/ttf'),('icon.svg','image/svg+xml'),('entry.js','application/javascript')]:self.assertEqual(package.content_type(path),mime)
  body=b'same bytes';key=package.asset_key('fonts/font.woff2',body,'a')
  self.assertEqual(key,package.asset_key('fonts/font.woff2',body,'b'))
  self.assertNotIn('/'+hashlib.sha256(body).hexdigest()[:20]+'/',key)
 def test_inline_and_external_styles_receive_the_same_specificity(self):
  soup=BeautifulSoup('<style>.info-trigger{color:var(--ink)}</style>','html.parser');package.protect_embedded_css(soup)
  self.assertEqual(soup.style.string,package.protected_css('.info-trigger{color:var(--ink)}'))
 def test_asset_rewrite_keeps_svg_fragment_and_query(self):
  self.assertEqual(package.public_urls('/brand/icons.svg?v=2#phone','https://cdn/'), 'https://cdn/brand/icons.svg?v=2#phone')
 def test_unchanged_media_survives_a_code_only_release_without_new_urls(self):
  old=package.asset_key('media/portrait.webp',b'photo','build-a');new=package.asset_key('media/portrait.webp',b'photo','build-b')
  self.assertEqual(old,new);self.assertNotEqual(new,package.asset_key('media/portrait.webp',b'replacement','build-b'))
  self.assertNotEqual(package.asset_key('_astro/entry.js',b'code','build-a'),package.asset_key('_astro/entry.js',b'code','build-b'))
 def test_news_snapshot_images_keep_their_relative_url_contract(self):
  feed='https://storage.yandexcloud.net/shaver/'+package.asset_key('data/news.json',b'{}','build-a')
  path='media/news/1962-344fe24f42df-640.webp'
  image='https://storage.yandexcloud.net/shaver/'+package.asset_key(path,b'photo','build-a')
  self.assertEqual(urljoin(feed,'../'+path),image)
  self.assertNotEqual(package.asset_key(path,b'photo','build-a'),package.asset_key(path,b'photo','build-b'))
 def test_gzip_has_a_portable_header_and_reproducible_bytes(self):
  body=b'SOYUZ export codec fixture';wire=package.gzip_bytes(body)
  self.assertEqual(wire,package.gzip_bytes(body));self.assertEqual(gzip.decompress(wire),body)
  self.assertEqual(wire[:4],b'\x1f\x8b\x08\x00');self.assertEqual(wire[4:8],b'\x00'*4);self.assertEqual(wire[9],255)
  self.assertEqual(package.CODEC['zlibVersion'],package.zlib.ZLIB_RUNTIME_VERSION)
 def test_css_isolation_preserves_keyframes_and_pseudo_elements(self):
  result=package.protected_css('@media(min-width:960px){a:hover, .x::before{color:red}}@keyframes x{from{opacity:0}to{opacity:1}}')
  self.assertIn('a:hover:not(#soyuz-export-style-a#soyuz-export-style-b)',result)
  self.assertIn('.x:not(#soyuz-export-style-a#soyuz-export-style-b)::before',result)
  self.assertIn('from{opacity:0}',result);self.assertNotIn('from:not',result)
 def test_every_referenced_public_asset_is_packaged_with_verified_bytes(self):
  pointer=json.loads((ROOT/'deploy/current.json').read_text());manifest_path=ROOT/pointer['manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'));rows={row['sourcePath']:row for row in manifest['files']}
  self.assertEqual(manifest['projectId'],46815509);self.assertEqual(manifest['origin'],'https://soyuz.hair');self.assertEqual(len(manifest['pages']),11)
  self.assertEqual(manifest['codec'],package.CODEC)
  self.assertFalse(any('/previews/'in p['route']for p in manifest['pages']))
  for row in rows.values():
   body=(ROOT/row['file']).read_bytes();self.assertEqual(hashlib.sha256(body).hexdigest(),row['sha256']);self.assertEqual(hashlib.sha256(gzip.decompress(body)if row['contentEncoding']=='gzip'else body).hexdigest(),row['contentSha256'])
   if row['contentEncoding']=='gzip':self.assertEqual(body[4:8],b'\x00'*4);self.assertEqual(body[9],255)
   path=row['file'].split('/public-assets/',1)[1];self.assertEqual(row['contentType'],package.content_type(path))
   self.assertEqual(row['key'],package.asset_key(path,(ROOT/'dist'/path).read_bytes(),manifest['build']));self.assertEqual(row['url'],'https://storage.yandexcloud.net/shaver/'+row['key']);self.assertIn('immutable',row['cacheControl'])
  feedrow=rows['data/news.json'];wire=(ROOT/feedrow['file']).read_bytes();feed=json.loads(gzip.decompress(wire)if feedrow['contentEncoding']=='gzip'else wire)
  for item in feed['items']:
   for variant in (item.get('image')or{}).get('variants',[]):
    path=posixpath.normpath(posixpath.join('data',urlsplit(variant['url']).path))
    self.assertIn(path,rows,path)
    self.assertEqual(urljoin(feedrow['url'],variant['url']),rows[path]['url'],path)
  for page in manifest['pages']:
   source=(ROOT/'dist'/('index.html'if page['route']=='/'else'404.html'if page['route']=='/404'else page['route'].strip('/')+'/index.html')).read_text(encoding='utf-8')
   for path in re.findall(r'''["'(](/(?!/)[^"')\s<>?#]+)''',source):
    target=ROOT/'dist'/path.lstrip('/')
    if target.is_file()and target.suffix!='.html':self.assertIn(path.lstrip('/'),rows,path)
   body=(manifest_path.parent/page['codeFile']).read_text(encoding='utf-8');head=(manifest_path.parent/page['headFile']).read_text(encoding='utf-8')
   self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),page['codeSha256']);self.assertEqual(hashlib.sha256(head.encode()).hexdigest(),page['headSha256'])
   self.assertEqual(len(BeautifulSoup(body,'html.parser').select('h1')),1)
   exported=BeautifulSoup(head,'html.parser');self.assertFalse(exported.select('meta[property="og:title"],meta[property="og:description"],meta[property="og:url"],meta[property="og:type"]'))
   self.assertFalse(exported.select('meta[name=viewport]'),'Native Tilda owns the single viewport tag')
   self.assertFalse(exported.select('link[rel=icon]'),'Native Tilda owns the site favicon')
   if page['route']=='/404':self.assertIn('noindex',exported.select_one('meta[name=robots]')['content']);self.assertEqual(page['alias'],'not-found')
   self.assertNotIn('#tildacopy',head)
   self.assertFalse(BeautifulSoup(body,'html.parser').select('.site-header,.footer,#mobile-menu'))
   self.assertFalse(BeautifulSoup(body,'html.parser').select('[data-booking-page]'),'Native canvas must have no second standalone width owner')
   self.assertNotRegex(body+head,r'https?://(?:127\.0\.0\.1|localhost)');self.assertNotIn('shaverfamily.ru',head)
  self.assertEqual(set(manifest['shared']),{'header','footer'})
  for key,row in manifest['shared'].items():
   code=(manifest_path.parent/row['codeFile']).read_text(encoding='utf-8');head=(manifest_path.parent/row['headFile']).read_text(encoding='utf-8')
   self.assertEqual(hashlib.sha256(code.encode()).hexdigest(),row['codeSha256']);self.assertEqual(hashlib.sha256(head.encode()).hexdigest(),row['headSha256']);self.assertIn('noindex',head)
   self.assertNotIn('type="module"',head)
if __name__=='__main__':unittest.main()
