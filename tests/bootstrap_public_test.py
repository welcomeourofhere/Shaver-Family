import gzip,hashlib,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bootstrap',ROOT/'scripts/bootstrap-public.py');bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap)
class BootstrapPublicTest(unittest.TestCase):
 def test_decodes_and_restores_source_references(self):
  url=bootstrap.PREFIX+'version/media/photo.webp';source=b'{"image":"/media/photo.webp"}';decoded=b'{"image":"'+url.encode()+b'"}';wire=gzip.compress(decoded)
  row={'url':bootstrap.PREFIX+'version/data/test.json','sourcePath':'data/test.json','contentEncoding':'gzip','sha256':bootstrap.sha(wire),'contentSha256':bootstrap.sha(decoded),'sourceSha256':bootstrap.sha(source)}
  self.assertEqual(bootstrap.decode_source(row,wire,{url:'media/photo.webp'}),source)
  with self.assertRaises(ValueError):bootstrap.decode_source(row,wire+b'corrupt',{})
 def test_refuses_path_escape(self):
  with self.assertRaises(ValueError):bootstrap.target_for(ROOT/'public','../private.txt')
  self.assertEqual(bootstrap.target_for(ROOT/'public','media/photo.webp'),(ROOT/'public/media/photo.webp').resolve())
if __name__=='__main__':unittest.main()
