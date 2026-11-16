import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('known_work_albums',Path(__file__).resolve().parents[1]/'scripts/vk-known-work-albums.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)

class KnownWorkAlbums(unittest.TestCase):
 def test_only_verified_six_ids_and_photos_get_without_album_discovery(self):
  with patch.object(reader.api,'read_pages',return_value=[])as call:
   result=reader.collect('fixture-only-key')
  self.assertEqual(len(result['albums']),6)
  self.assertEqual({a['id']for a in result['albums']},{313537350,312750596,311695116,311570476,312351342,297253623})
  self.assertEqual(len({a['masterId']for a in result['albums']}),6)
  self.assertTrue(all(c.args[1]=='photos.get'for c in call.call_args_list))
  self.assertEqual([c.args[2]['album_id']for c in call.call_args_list],[a['id']for a in reader.ALBUMS])
 def test_first_access_refusal_stops_without_trying_more_albums(self):
  with patch.object(reader.api,'read_pages',side_effect=reader.api.ReadError('api_error',1051))as call:
   with self.assertRaises(reader.api.ReadError):reader.collect('fixture-only-key')
  self.assertEqual(call.call_count,1)

if __name__=='__main__':unittest.main()
