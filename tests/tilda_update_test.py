import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('tilda_update',Path(__file__).resolve().parents[1]/'scripts/prepare-tilda-update.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class TildaUpdateTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.folder=self.root/'deploy/out/new';self.folder.mkdir(parents=True)
  self.registry={'projectId':46815509,'build':'published','pages':[]};self.manifest={'projectId':46815509,'origin':'https://soyuz.hair','build':'new','pages':[],'shared':{},'files':[{'key':'Soyuz/releases/new/asset','sha256':'wire'}]}
  for i,route in enumerate(['/']+['/page-'+str(i)for i in range(10)]+['/soyuz-header','/soyuz-footer']):
   alias=route.strip('/');entry={'alias':alias,'headFile':str(i)+'.head','codeFile':str(i)+'.body'}
   for field,file_key,hash_key in [('head','headFile','headSha256'),('body','codeFile','codeSha256')]:
    body=(field+str(i)).encode();(self.folder/entry[file_key]).write_bytes(body);entry[hash_key]=hashlib.sha256(body).hexdigest()
   if i<11:self.manifest['pages'].append({'route':route,**entry})
   else:self.manifest['shared']['header'if i==11 else'footer']=entry
   self.registry['pages'].append({'route':route,'alias':alias,'pageid':100+i,'recordid':200+i,'headSha256':'before-head','codeSha256':'before-body'})
  self.report={'build':'new','applied':True,'complete':True,'ok':True,'total':1,'results':[{'key':'Soyuz/releases/new/asset','sha256':'wire','status':'verified'}]}
  self.write()
 def write(self):
  config={'projectId':46815509,'origin':'https://soyuz.hair','pages':[r['route']for r in self.manifest['pages']]}
  for path,value in [(self.root/'deploy/production.json',config),(self.root/'deploy/current.json',{'build':'new','manifest':'deploy/out/new/manifest.json'}),(self.root/'deploy/tilda-pages.json',self.registry),(self.folder/'manifest.json',self.manifest),(self.folder/'upload-report.json',self.report)]:path.write_text(json.dumps(value),encoding='utf-8')
  (self.root/'deploy/project-head.html').write_text('<script>publicConfig</script>',encoding='utf-8')
 def test_verified_payload_has_exact_preconditions_and_shared_publication_order(self):
  before=(self.root/'deploy/tilda-pages.json').read_bytes();payload=module.prepare(self.root)
  self.assertEqual(payload['previousPublishedBuild'],'published');self.assertEqual(len(payload['rows']),13)
  self.assertEqual([x.get('sharedKind')for x in payload['rows'][:2]],['header','footer'])
  self.assertEqual(payload['rows'][0]['expectedBefore']['codeSha256'],'before-body');self.assertEqual(payload['rows'][0]['code'],'body11')
  self.assertEqual((self.root/'deploy/tilda-pages.json').read_bytes(),before)
 def test_incomplete_wrong_or_duplicated_public_asset_verification_is_rejected(self):
  original=copy.deepcopy(self.report)
  for change in [{'complete':False},{'applied':False},{'build':'stale'},{'results':[{'key':'Soyuz/releases/new/asset','sha256':'different','status':'verified'}]},{'results':original['results']*2}]:
   with self.subTest(change=change):
    self.report=copy.deepcopy(original);self.report.update(change);self.write()
    with self.assertRaises(ValueError):module.prepare(self.root)
 def test_modified_page_or_native_target_is_rejected(self):
  (self.folder/'0.head').write_text('unexpected',encoding='utf-8')
  with self.assertRaises(ValueError):module.prepare(self.root)
  (self.folder/'0.head').write_text('head0',encoding='utf-8')
  self.registry['pages'][0]['recordid']=self.registry['pages'][1]['recordid'];self.write()
  with self.assertRaises(ValueError):module.prepare(self.root)
if __name__=='__main__':unittest.main()
