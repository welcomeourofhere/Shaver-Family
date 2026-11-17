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
 def test_shared_chrome_uses_native_tilda_landmarks_without_changing_inner_markup(self):
  soup=BeautifulSoup('<a class="skip" href="#main">К содержанию</a><header id="site-top" class="site-header shell" data-owner="header"><nav aria-label="Разделы"><a href="#services">Услуги</a></nav></header><dialog id="mobile-menu" data-mobile="kept"><a href="#contacts">Контакты</a></dialog><main data-booking-page><article><footer class="article-footer">Автор</footer></article></main><footer class="footer shell" data-owner="footer"><a href="/privacy-policy">Документы</a></footer>','html.parser')
  shared=package.split_shared_chrome(soup)
  header=BeautifulSoup(shared['header'],'html.parser');footer=BeautifulSoup(shared['footer'],'html.parser')
  self.assertEqual(header.select_one('.site-header').name,'div');self.assertEqual(footer.select_one('.footer').name,'div')
  self.assertEqual(header.select_one('.site-header')['id'],'site-top');self.assertEqual(header.select_one('.site-header')['data-owner'],'header');self.assertEqual(footer.select_one('.footer')['data-owner'],'footer')
  self.assertEqual(header.select_one('nav')['aria-label'],'Разделы');self.assertEqual(header.select_one('nav a')['href'],'/#services')
  self.assertEqual(header.select_one('a')['class'],['skip']);self.assertEqual(header.select_one('.skip')['href'],'#main');self.assertIsNone(soup.select_one('.skip'))
  self.assertEqual(header.select_one('#mobile-menu').name,'dialog');self.assertEqual(header.select_one('#mobile-menu')['data-mobile'],'kept');self.assertEqual(header.select_one('#mobile-menu a')['href'],'/#contacts')
  self.assertEqual(footer.select_one('a')['href'],'/privacy-policy');self.assertFalse(header.select('header,footer'));self.assertFalse(footer.select('header,footer'))
  self.assertEqual(soup.select_one('footer.article-footer').get_text(),'Автор');self.assertFalse(soup.select('.site-header,.footer,#mobile-menu,[data-booking-page]'))
 def test_native_host_canvas_delegates_opaque_background_to_root(self):
  rules=package.tinycss2.parse_stylesheet(package.HOST_CSS,skip_whitespace=True,skip_comments=True)
  rule=next(rule for rule in rules if rule.type=='qualified-rule'and 'body.t-body'in package.tinycss2.serialize(rule.prelude).split(','))
  self.assertEqual(set(package.tinycss2.serialize(rule.prelude).split(',')),{'body.t-body','#allrecords','#t-header','#t-footer'})
  background=next(item for item in package.tinycss2.parse_declaration_list(rule.content)if item.type=='declaration'and item.lower_name=='background')
  self.assertTrue(background.important);self.assertEqual(package.tinycss2.serialize(background.value).strip(),'transparent')
 def test_host_renderer_changes_build_but_preserves_binary_representation(self):
  prepared={'_astro/entry.js':b'console.log("same")','media/portrait.webp':b'same image','fonts/ui.woff2':b'same font'}
  before=package.build_identity(prepared);fingerprint=package.exporter_fingerprint()
  with patch.object(package,'HOST_CSS',package.HOST_CSS+'\nbody.t-body{isolation:isolate}'):
   after=package.build_identity(prepared);changed=package.exporter_fingerprint()
  self.assertNotEqual(before,after);self.assertNotEqual(fingerprint['hostCssSha256'],changed['hostCssSha256'])
  self.assertEqual(fingerprint['sourceSha256'],changed['sourceSha256'])
  for path in ['media/portrait.webp','fonts/ui.woff2']:
   body=prepared[path];self.assertEqual(package.asset_key(path,body,before),package.asset_key(path,body,after));self.assertEqual(prepared[path],body)
  self.assertNotEqual(package.asset_key('_astro/entry.js',prepared['_astro/entry.js'],before),package.asset_key('_astro/entry.js',prepared['_astro/entry.js'],after))
 def test_exporter_fingerprint_is_portable_but_detects_renderer_source_change(self):
  with patch.object(package.Path,'read_bytes',return_value=b'first\r\nsecond\r\n'):windows=package.exporter_fingerprint()
  with patch.object(package.Path,'read_bytes',return_value=b'first\nsecond\n'):posix=package.exporter_fingerprint()
  self.assertEqual(windows,posix)
  before=package.build_identity({})
  with patch.object(package.Path,'read_bytes',return_value=b'changed renderer\n'):after=package.build_identity({})
  self.assertNotEqual(before,after)
 def test_fixture_reproduces_native_classes_and_opaque_project_background(self):
  spec=importlib.util.spec_from_file_location('freeze_fixture',ROOT/'scripts/freeze-release-fixture.py');freeze=importlib.util.module_from_spec(spec);spec.loader.exec_module(freeze)
  document=freeze.native_document('Host test','<style>'+package.HOST_CSS+'</style>','<div id="t-header" class="t-records"></div><main>Content</main><div id="t-footer" class="t-records"></div>',freeze.host_background('#FFFCF7'))
  soup=BeautifulSoup(document,'html.parser')
  for node in [soup.body,soup.select_one('#allrecords')]:self.assertEqual(node['style'],'background-color:#fffcf7')
  self.assertIn('t-body',soup.body['class']);self.assertIn('t-records',soup.select_one('#allrecords')['class'])
  self.assertEqual(soup.select_one('[data-native-host-background]').get_text(),'body.t-body,.t-records{background-color:#fffcf7}')
  for selector in ['#t-header','#t-footer']:self.assertIn('t-records',soup.select_one(selector)['class'])
  self.assertIsNone(BeautifulSoup(freeze.native_document('No background','',''),'html.parser').body.get('style'))
  with self.assertRaises(freeze.argparse.ArgumentTypeError):freeze.host_background('#ffffff00')
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
 def test_current_package_prepares_exact_tilda_payload_without_normalizing_bytes(self):
  spec=importlib.util.spec_from_file_location('tilda_update',ROOT/'scripts/prepare-tilda-update.py');update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)
  payload=update.prepare(ROOT,require_uploaded=False)
  self.assertEqual(len(payload['rows']),13);self.assertFalse(payload['assetsVerified'])
  for row in payload['rows']:
   for field in ['head','code']:self.assertEqual(hashlib.sha256(row[field].encode('utf-8')).hexdigest(),row[field+'Sha256'])
 def test_every_referenced_public_asset_is_packaged_with_verified_bytes(self):
  pointer=json.loads((ROOT/'deploy/current.json').read_text());manifest_path=ROOT/pointer['manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'));rows={row['sourcePath']:row for row in manifest['files']}
  self.assertEqual(manifest['projectId'],46815509);self.assertEqual(manifest['origin'],'https://soyuz.hair');self.assertEqual(len(manifest['pages']),11)
  self.assertEqual(manifest['codec'],package.CODEC)
  self.assertEqual(manifest['exporter'],package.exporter_fingerprint())
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
   body=(manifest_path.parent/page['codeFile']).read_bytes().decode('utf-8');head=(manifest_path.parent/page['headFile']).read_bytes().decode('utf-8')
   self.assertIn(package.HOST_CSS,head)
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
   code=(manifest_path.parent/row['codeFile']).read_bytes().decode('utf-8');head=(manifest_path.parent/row['headFile']).read_bytes().decode('utf-8')
   self.assertIn(package.HOST_CSS,head)
   self.assertEqual(hashlib.sha256(code.encode()).hexdigest(),row['codeSha256']);self.assertEqual(hashlib.sha256(head.encode()).hexdigest(),row['headSha256']);self.assertIn('noindex',head)
   self.assertNotIn('type="module"',head)
if __name__=='__main__':unittest.main()
