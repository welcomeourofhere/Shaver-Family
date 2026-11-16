import {writeFileSync, mkdirSync} from 'node:fs';
import {touchBrowser} from './touch-browser.mjs';
const b = await touchBrowser(), base = process.env.QA_URL || 'http://127.0.0.1:4321/';
mkdirSync('docs/previews', {recursive:true});
async function capture(name) {
  const result = await b.send('Page.captureScreenshot', {format:'png'});
  writeFileSync(`docs/previews/round45-${name}.png`, Buffer.from(result.data, 'base64'));
}
try {
  await b.viewport(390,844,true); await b.open(base);
  await b.tap(await b.point('[data-open-menu]')); await capture('menu-390');
  await b.tap(await b.point('[data-open-menu]')); await b.center('#faq');
  await b.evaluate("document.querySelector('#faq-price summary').click()"); await b.settle(); await capture('faq-390');
  await b.open(base); await b.center('.certificate-scene'); await capture('certificates-390');
  await b.open(base); await b.center('.team-grid');
  await b.evaluate("document.querySelector('[data-team-open=\"souz-sofya-shalaginova\"]').click()"); await b.settle(); await capture('article-390');
  await b.evaluate("document.querySelector('#team-dialog-souz-sofya-shalaginova blockquote').scrollIntoView({block:'center'})"); await b.settle(); await capture('article-quote-390');
  console.log('Captured mobile menu, FAQ, certificates and article.');
} finally { await b.close(); }
