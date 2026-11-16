"""The exporter removes shared chrome before Tilda inserts its native pages."""
import importlib.util,unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package',ROOT/'scripts/prepare-tilda-release.py');package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)
class SharedShellTest(unittest.TestCase):
 def test_shared_navigation_and_dialog_are_emitted_once_outside_content(self):
  soup=BeautifulSoup('<body><div data-booking-page><header class="site-header"><a href="#services">Услуги</a></header><dialog id="mobile-menu"><a href="#masters">Мастера</a></dialog><main><h1>СОЮЗ</h1></main><footer class="footer"><a href="#contacts">Контакты</a></footer><nav data-mobile-nav></nav></div><dialog id="booking-drawer"></dialog><script type="module" src="/_astro/runtime.js"></script></body>','html.parser')
  shared=package.split_shared_chrome(soup)
  self.assertFalse(soup.select('.site-header,.footer,#mobile-menu'))
  self.assertFalse(soup.select('[data-booking-page]'))
  combined=BeautifulSoup(shared['header']+soup.body.decode_contents()+shared['footer'],'html.parser')
  for selector in ['.site-header','.footer','#mobile-menu','#booking-drawer','[data-mobile-nav]','h1','script[src]']:self.assertEqual(len(combined.select(selector)),1,selector)
  self.assertIn('href="/#services"',shared['header']);self.assertIn('href="/#contacts"',shared['footer'])
  self.assertEqual(len(soup.select('script[type=module]')),1)

if __name__=='__main__':unittest.main()
