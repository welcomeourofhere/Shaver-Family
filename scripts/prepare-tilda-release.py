"""Reproducible Astro -> Tilda/S3 package; no external writes."""
from __future__ import annotations
import gzip,hashlib,json,posixpath,re,zlib
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
import tinycss2

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
CONFIG=json.loads((ROOT/'deploy/production.json').read_text(encoding='utf-8'))
assert CONFIG['projectId']==46815509 and CONFIG['origin']=='https://soyuz.hair'
assert CONFIG['bucket']=='shaver' and CONFIG['prefix']=='Soyuz/releases/'
TEXT={'.css','.js','.mjs','.svg','.json','.txt','.xml'}
CONTENT_TYPES={'.css':'text/css','.js':'application/javascript','.mjs':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.txt':'text/plain','.xml':'application/xml','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.avif':'image/avif','.ico':'image/x-icon','.mp4':'video/mp4','.webm':'video/webm','.mp3':'audio/mpeg','.wav':'audio/wav','.woff':'font/woff','.woff2':'font/woff2','.ttf':'font/ttf','.otf':'font/otf'}
CODEC={'format':'gzip','level':9,'mtime':0,'os':255,'zlibVersion':zlib.ZLIB_RUNTIME_VERSION}
PATTERN=re.compile(r'(?<![\w:./-])(?:https://soyuz\.hair)?/(?:_astro|media|brand|fonts|data|reference|audio|offer-icons)/[^\s\x22\x27<>),;`]*')
RELATIVE=re.compile(r'[\x22\x27](\.{1,2}/[^\x22\x27\s]+)[\x22\x27]')
HOST_CSS='''body.t-body,#allrecords,#t-header,#t-footer{background:transparent!important}
#allrecords .t123,#allrecords .t123>.t-container,#allrecords .t123 .t-col,#allrecords .t123 .t-width{width:100%;max-width:none;margin:0;padding:0;float:none}
#allrecords .t-rec{padding:0!important}
/* Native shared-page wrappers must not bound the sticky header or clip its menus. */
#t-header,#t-header>.t-rec,#t-header .t123,#t-header .t123>.t-container,#t-header .t123>.t-container_100,#t-header .t123 .t-col,#t-header .t123 .t-width{display:contents}
#allrecords{overflow:visible}
html[data-booking-layout="docked"][data-booking-state="open"] #allrecords{width:calc(100% - var(--booking-width))}'''

def sha(data):return hashlib.sha256(data).hexdigest()
def content_type(path):return CONTENT_TYPES.get(Path(path).suffix.lower(),'application/octet-stream')
def exporter_fingerprint():
    # Source snapshots normalize newlines; preserve that identity across OSes.
    source=Path(__file__).read_bytes().replace(b'\r\n',b'\n')
    return {'version':6,'sourceSha256':sha(source),'sourceNormalization':'UTF-8 LF','hostCssSha256':sha(HOST_CSS.encode('utf-8'))}
def build_identity(prepared,pages=()):
    digest=hashlib.sha256(b'SOYUZ public assets and HTML v6 exporter identity')
    for value in (CODEC,exporter_fingerprint()):digest.update(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
    for path in sorted(prepared):
        body=prepared[path];kind=Path(path).suffix.lower()
        normalized=public_urls(body.decode('utf-8'),'@ASSET_BASE@/').encode('utf-8')if kind in TEXT else body
        digest.update(path.encode());digest.update(content_type(path).encode());digest.update(normalized)
    for page in sorted(pages,key=lambda item:item['source']):
        html=public_urls(page['html'].replace('\r\n','\n'),'@ASSET_BASE@/')
        ids=list(dict.fromkeys(re.findall(r'info-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',html)))
        for index,identifier in enumerate(ids):
            if html.count(identifier)!=2:raise ValueError('Expected one tooltip control and one panel: '+page['source'])
            html=html.replace(identifier,f'info-UUID-{index}')
        digest.update(b'\0HTML\0'+page['source'].encode()+b'\0'+html.encode())
    return digest.hexdigest()[:20]
def gzip_bytes(body):
    buffer=BytesIO()
    with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,compresslevel=CODEC['level'],mtime=CODEC['mtime'])as archive:archive.write(body)
    return buffer.getvalue()
def public_urls(text,base,urls=None):
    def replace(match):
        url=urlsplit(match.group());path=url.path.lstrip('/')
        return (urls or{}).get(path,base+path)+('?' +url.query if url.query else'')+('#'+url.fragment if url.fragment else'')
    return PATTERN.sub(replace,text)

def protect_embedded_css(soup):
    # Astro inlines small component styles; keep the same cascade as external CSS.
    for style in soup.select('style'):style.string=protected_css(style.get_text())
def asset_key(path,body,build):
    # The fallback feed resolves ../media/news relative to its own release directory.
    version=build if Path(path).suffix.lower()in TEXT or path.startswith('media/news/')else'assets/'+sha(content_type(path).encode()+b'\0'+body)[:20]
    return CONFIG['prefix']+version+'/'+path
def split_shared_chrome(soup):
    shared={}
    for key,selector in [('header','a.skip,.site-header,#mobile-menu'),('footer','footer.footer')]:
        nodes=soup.select(selector)
        assert len(nodes)==(3 if key=='header'else 1),'Missing or duplicate shared '+key
        for node in nodes:
            # Tilda already supplies the outer header/footer landmarks.
            if node.name in ('header','footer'):node.name='div'
            for link in node.select('a[href^="#"]'):link['href']='/'+link['href']
        shared[key]='\n'.join(str(node.extract())for node in nodes)
    # In Tilda, #allrecords owns the booking canvas; keep no nested standalone owner.
    for node in soup.select('[data-booking-page]'):del node['data-booking-page']
    return shared
def protected_css(css):
    # Same export isolation as Shaver Family; no component restyling or DOM repair.
    guard=tinycss2.parse_component_value_list(':not(#soyuz-export-style-a#soyuz-export-style-b)')
    def protect(tokens):
        groups=[];current=[]
        for token in tokens:
            if token.type=='literal'and token.value==',':groups.extend([current,[token]]);current=[]
            else:current.append(token)
        groups.append(current)
        for group in groups:
            if len(group)==1 and group[0].type=='literal'and group[0].value==',':continue
            start=next((i for i,t in enumerate(group)if t.type not in ('whitespace','comment')),len(group));end=len(group)
            for i in range(start,len(group)):
                token=group[i]
                if token.type=='whitespace'or token.type=='literal'and token.value in ('>','+','~','||'):end=i;break
                if token.type=='literal'and token.value==':'and i+1<len(group):
                    following=group[i+1]
                    if following.type=='literal'and following.value==':'or following.type=='ident'and following.value.lower()in ('before','after','first-line','first-letter'):end=i;break
            group[end:end]=guard
        return [token for group in groups for token in group]
    def walk(rules):
        for rule in rules:
            if rule.type=='qualified-rule':rule.prelude=protect(rule.prelude)
            elif rule.type=='at-rule'and rule.lower_at_keyword in ('media','supports','container','layer','document','scope','starting-style')and rule.content is not None:
                nested=tinycss2.parse_rule_list(rule.content);walk(nested);rule.content=tinycss2.parse_component_value_list(tinycss2.serialize(nested))
    rules=tinycss2.parse_stylesheet(css);walk(rules);return tinycss2.serialize(rules)

def main():
    pages=[];assets=set();scanned=set()
    def include(path):
        path=unquote(urlsplit(path).path).lstrip('/')
        target=(DIST/path).resolve()
        if not target.is_relative_to(DIST.resolve()):raise ValueError('Asset outside dist')
        if target.is_dir():
            for child in target.rglob('*'):
                if child.is_file():include(child.relative_to(DIST.resolve()).as_posix())
            return
        if not target.is_file():raise ValueError('Missing public dependency: '+path)
        assets.add(path)
        if path in scanned:return
        scanned.add(path)
        if target.suffix.lower()in TEXT:scan(target.read_text(encoding='utf-8'),path)
    def scan(text,owner):
        for m in PATTERN.finditer(text):include(m.group())
        for m in RELATIVE.finditer(text):
            value=urlsplit(m[1]).path
            if Path(value).suffix.lower()not in TEXT|{'.woff','.woff2','.ttf','.webp','.png','.jpg','.jpeg','.mp4','.mp3','.ico'}:continue
            path=posixpath.normpath(posixpath.join(posixpath.dirname(owner),value))
            if (DIST/path).is_file():include(path)
    for route in CONFIG['pages']:
        path='index.html'if route=='/'else'404.html'if route=='/404'else route.strip('/')+'/index.html'
        source=(DIST/path).read_text(encoding='utf-8');soup=BeautifulSoup(source,'html.parser')
        assert soup.head and soup.body and len(soup.select('h1'))==1,route
        canonical=soup.select_one('link[rel=canonical]');expected=CONFIG['origin']+route
        assert canonical and canonical['href']==expected,(route,canonical)
        robots=soup.select_one('meta[name=robots]')['content'];assert ('noindex'in robots)==(route=='/404'),(route,robots)
        assert not re.search(r'https?://(?:localhost|127\.0\.0\.1)',source)
        scan(source,path);pages.append({'route':route,'source':path,'html':source,'soup':soup})
        protect_embedded_css(soup)
    # Keep the approved canonical icons/fonts available to source checks and CI.
    for directory in ['brand','fonts']:include(directory+'/')
    # The previous sharing artwork remains an approved export alongside the current badge.
    seo_assets=json.loads((ROOT/'content/seo-assets.json').read_text(encoding='utf-8'))
    for role in ['social','legacySocial']:
        if role in seo_assets:include(seo_assets[role]['path'].removeprefix('public/'))
    # Include the native renderer/host contract, not only resource bytes.
    prepared={}
    for path in sorted(assets):
        body=(DIST/path).read_bytes();kind=Path(path).suffix.lower()
        if kind=='.css':body=protected_css(body.decode('utf-8')).encode()
        prepared[path]=body
    build=build_identity(prepared,pages);prefix=CONFIG['prefix']+build+'/'
    base=f'https://storage.yandexcloud.net/{CONFIG["bucket"]}/{prefix}'
    urls={path:f'https://storage.yandexcloud.net/{CONFIG["bucket"]}/'+asset_key(path,prepared[path],build)for path in assets}
    out=ROOT/'deploy/out'/build;out.mkdir(parents=True,exist_ok=True)
    def rewrite(text):return public_urls(text,base,urls)
    files=[]
    for path in sorted(assets):
        source=DIST/path;body=prepared[path];kind=source.suffix.lower();mime=content_type(path)
        if kind in TEXT:body=rewrite(body.decode('utf-8')).encode('utf-8')
        content_hash=sha(body);encoding='gzip'if kind in TEXT else None
        delivered=gzip_bytes(body)if encoding else body
        target=out/'public-assets'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(delivered)
        files.append({'file':target.relative_to(ROOT).as_posix(),'sourcePath':path,'sourceSha256':sha(source.read_bytes()),'key':asset_key(path,prepared[path],build),'url':urls[path],'bytes':len(delivered),'contentBytes':len(body),'sha256':sha(delivered),'contentSha256':content_hash,'contentType':mime,'contentEncoding':encoding,'cacheControl':'public,max-age=31536000,immutable'})
    emitted=[];shared=None;shared_head=''
    for item in pages:
        soup=item['soup']
        chrome=split_shared_chrome(soup)
        if item['route']=='/':
            shared=chrome
            # Service pages preview the same CSS but never execute a content-page entry.
            shared_head=''.join(str(node)for node in soup.head.find_all(recursive=False)if node.name=='style'or node.name=='link'and ('stylesheet'in node.get('rel',[])or node.get('as')=='font')or node.name=='script'and not node.get('src')and node.get('type')!='application/ld+json')
        for tag in list(soup.head.find_all(['meta','title','link'],recursive=False)):
            if tag.name=='meta'and tag.get('charset'):tag.decompose()
            elif tag.name=='meta'and (tag.get('name')in ('description','viewport')or tag.get('name')=='robots'and item['route']!='/404'):tag.decompose()
            elif tag.name=='meta'and tag.get('property')in ('og:title','og:description','og:url','og:type'):tag.decompose()
            elif tag.name=='title'or tag.name=='link'and any(role in tag.get('rel',[])for role in ['canonical','icon']):tag.decompose()
        metadata=BeautifulSoup(item['html'],'html.parser')
        route=item['route'];name='home'if route=='/'else route.strip('/').replace('/','-')
        head=rewrite(soup.head.decode_contents());code=rewrite(soup.body.decode_contents())
        host='<style>'+HOST_CSS+'</style>'
        head=host+head
        headfile=f'{name}.head.html';codefile=f'{name}.body.html'
        (out/headfile).write_text(head,encoding='utf-8',newline='');(out/codefile).write_text(code,encoding='utf-8',newline='')
        emitted.append({'route':route,'alias':''if route=='/'else'not-found'if route=='/404'else route.strip('/'),'title':metadata.title.get_text(),'description':metadata.select_one('meta[name=description]')['content'],'canonical':CONFIG['origin']+route,'noindex':route=='/404','headFile':headfile,'codeFile':codefile,'headSha256':sha(head.encode()),'codeSha256':sha(code.encode()),'codeBytes':len(code.encode())})
    assert shared is not None
    shared_pages={}
    for key,body in shared.items():
        head=rewrite('<meta name="robots" content="noindex, nofollow">'+shared_head+'<style>'+HOST_CSS+'</style>');code=rewrite(body)
        headfile=f'shared-{key}.head.html';codefile=f'shared-{key}.body.html'
        (out/headfile).write_text(head,encoding='utf-8',newline='');(out/codefile).write_text(code,encoding='utf-8',newline='')
        shared_pages[key]={'alias':'soyuz-'+key,'title':'Шапка СОЮЗа'if key=='header'else'Подвал СОЮЗа','noindex':True,'headFile':headfile,'codeFile':codefile,'headSha256':sha(head.encode()),'codeSha256':sha(code.encode())}
    manifest={'schemaVersion':2,'codec':CODEC,'exporter':exporter_fingerprint(),'build':build,'projectId':CONFIG['projectId'],'origin':CONFIG['origin'],'bucket':CONFIG['bucket'],'prefix':prefix,'assetBase':base,'pages':emitted,'shared':shared_pages,'files':files}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    (ROOT/'deploy/current.json').write_text(json.dumps({'build':build,'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()},indent=2)+'\n',encoding='utf-8',newline='')
    media_lock={'schemaVersion':1,'build':build,'assetBase':base,'files':[{key:row[key]for key in ['sourcePath','sourceSha256','url','sha256','contentSha256','contentEncoding']}for row in files if not row['sourcePath'].startswith('_astro/')]}
    (ROOT/'deploy/media-lock.json').write_text(json.dumps(media_lock,indent=2)+'\n',encoding='utf-8',newline='')
    print(json.dumps({'build':build,'pages':len(pages),'assets':len(files),'encodedBytes':sum(f['bytes']for f in files),'manifest':str(out/'manifest.json')},ensure_ascii=False))
if __name__=='__main__':main()
