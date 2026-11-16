import assert from 'node:assert/strict';
import {touchBrowser} from './touch-browser.mjs';

const browser = await touchBrowser();
try {
  await browser.viewport(390, 844, false);
  await browser.open(process.env.QA_URL || 'http://127.0.0.1:4321/');
  const frames = await browser.evaluate(`(async () => {
    const frames = [];
    document.querySelector('.of-rail').scrollIntoView({block:'center', behavior:'instant'});
    const end = performance.now() + 850;
    do {
      const button = document.querySelector('[data-action="offer-prev"]');
      if (button && !button.hidden) frames.push({width:button.getBoundingClientRect().width, opacity:Number(getComputedStyle(button).opacity), disabled:button.disabled});
      await new Promise(requestAnimationFrame);
    } while (performance.now() < end);
    return frames;
  })()`);
  assert.ok(frames.length > 4 && frames.at(-1).disabled, JSON.stringify(frames));
  const widths = frames.map(f => f.width);
  const min = Math.min(...widths), max = Math.max(...widths);
  assert.ok(max - min > 5, JSON.stringify(frames));
  assert.ok(frames.some(f => f.opacity > .42 && f.opacity < .98 && f.width > min + 1 && f.width < max - 1),
    `Geometry and disabled opacity did not animate together: ${JSON.stringify(frames)}`);
  assert.ok(Math.abs(frames.at(-1).opacity - .4) < .02, JSON.stringify(frames.at(-1)));
  console.log('PASS dock disabled opacity and geometry move together');
  for (const width of [320,390,768]) {
    await browser.viewport(width,844,false); await browser.open(process.env.QA_URL || 'http://127.0.0.1:4321/');
    await browser.center('.certificate-scene');
    for (let i=0;i<4;i++) {
      const bounds=await browser.evaluate(`(async()=>{const art=document.querySelectorAll('.certificate-art')[${i}],rows=[];document.querySelectorAll('[data-certificate]')[${i}].click();const end=performance.now()+650;do{const r=art.getBoundingClientRect();rows.push({left:r.left,right:r.right});await new Promise(requestAnimationFrame)}while(performance.now()<end);return rows})()`);
      assert.ok(bounds.every(r=>r.left>=-1&&r.right<=width+1),`certificate ${i} clips on ${width}: ${JSON.stringify(bounds)}`);
    }
    console.log(`PASS enlarged certificate bounds ${width}`);
  }
} finally { await browser.close(); }
