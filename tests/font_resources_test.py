"""Verify the small compatibility font transformation, including preserved originals."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.local/font-tools'))
from fontTools.ttLib import TTFont
spec=importlib.util.spec_from_file_location('display_font',ROOT/'scripts/prepare-display-font.py');display=importlib.util.module_from_spec(spec);spec.loader.exec_module(display)
class BodyFonts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=json.loads((ROOT/'content/body-fonts.json').read_text(encoding='utf-8'))['fonts']
    def test_original_and_derivative_hashes(self):
        self.assertEqual(len(self.rows),3)
        for row in self.rows:
            for name,key in [('source','sourceSha256'),('output','sha256')]:self.assertEqual(hashlib.sha256((ROOT/row[name]).read_bytes()).hexdigest(),row[key])
    def test_only_new_unicode_mapping_is_no_break_space(self):
        for row in self.rows:
            original=TTFont(ROOT/row['source']).getBestCmap();derived=TTFont(ROOT/row['output']).getBestCmap()
            self.assertEqual(derived,{**original,0xA0:original[0x20]})
    def test_contours_advances_and_shaping_are_preserved(self):
        for row in self.rows:
            original=TTFont(ROOT/row['source']);derived=TTFont(ROOT/row['output'])
            self.assertEqual(display.outline_signature(original),display.outline_signature(derived));self.assertEqual(dict(original['hmtx'].metrics),dict(derived['hmtx'].metrics))
            for table in ['GDEF','GPOS','GSUB']:
                self.assertEqual(original.getTableData(table),derived.getTableData(table))
    def test_derived_family_and_original_copyright(self):
        for row in self.rows:
            original=TTFont(ROOT/row['source']);derived=TTFont(ROOT/row['output'])
            self.assertIn('SOYUZ UI',derived['name'].getDebugName(1));self.assertEqual(original['name'].getDebugName(0),derived['name'].getDebugName(0))
if __name__=='__main__':unittest.main()
