"""The three public documents describe this site and resolve the confirmed operator."""
import json,unittest
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
class LegalTest(unittest.TestCase):
 def test_three_documents_render_real_operator_and_current_business(self):
  registry=json.loads((ROOT/'content/legal/pages.json').read_text(encoding='utf-8'))
  self.assertEqual({p['slug']for p in registry['pages']},{'oferta','privacy-policy','privacy-data'})
  for page in registry['pages']:
   path=ROOT/'dist'/page['slug']/'index.html';self.assertTrue(path.is_file(),page['slug'])
   soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser');main=soup.select_one('.legal-page');self.assertIsNotNone(main)
   text=main.get_text(' ',strip=True).replace('\xa0',' ');self.assertIn('432909508772',text);self.assertIn('319435000029871',text);self.assertIn('shaverfamily@yandex.ru',text)
   self.assertNotIn('{{BUSINESS',text);self.assertNotIn('лукбук',text);self.assertNotIn('академии',text)
   self.assertEqual(len(soup.select('h1')),1);self.assertEqual(len(soup.select('.footer-legal a')),3)
   self.assertEqual(soup.select_one('link[rel=canonical]')['href'],'https://soyuz.hair/'+page['slug'])
   if page['slug']=='oferta':self.assertIn('11:00–22:00',text);self.assertIn('бессрочные',text);self.assertIn('многоразовые',text)
   if page['slug']=='privacy-data':self.assertIn('не является согласием',text)

if __name__=='__main__':unittest.main()
