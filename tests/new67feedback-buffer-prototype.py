"""Isolated native AudioBuffer experiment. Never imports or changes the product playback owner."""
import argparse
import hashlib
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--engine', choices=['chromium', 'webkit'], required=True)
parser.add_argument('--label', required=True)
args = parser.parse_args()
assert re.fullmatch(r'[\w-]+', args.label)
OUT = ROOT / 'tmp/planning/iteration67/feedback-buffer-prototype' / args.label
OUT.mkdir(parents=True, exist_ok=False)
config = json.loads((ROOT / 'src/config/feedback.json').read_text(encoding='utf-8'))
assets = {tone: (ROOT / ('public' + details['url'])).read_bytes() for tone, details in config['tones'].items()}
manifest = {tone: hashlib.sha256(data).hexdigest() for tone, data in assets.items()}
template = r'''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Isolated playback experiment</title>
<body><script>
window.rows=[];window.frame=0;window.preparation={};
requestAnimationFrame(function tick(){frame++;requestAnimationFrame(tick)});
const tones=__TONES__, volume=__VOLUME__, Ctor=window.AudioContext||window.webkitAudioContext;
let context, gain, active;
const buffers=new Map();
try {
  context=new Ctor({latencyHint:'interactive'});
  gain=context.createGain();gain.gain.value=volume;gain.connect(context.destination);
  preparation={startedAt:performance.now(),initialState:context.state,baseLatency:context.baseLatency,sampleRate:context.sampleRate};
  Promise.all(tones.map(async tone=>{
    const response=await fetch('/'+tone+'.wav');if(!response.ok)throw Error('HTTP '+response.status);
    const buffer=await context.decodeAudioData(await response.arrayBuffer());buffers.set(tone,buffer);
    preparation[tone]={decodedAt:performance.now(),duration:buffer.duration,channels:buffer.numberOfChannels};
  })).then(()=>{preparation.readyAt=performance.now();preparation.ready=true}).catch(error=>preparation.error=error.name+': '+error.message);
} catch(error) {preparation.error=error.name+': '+error.message}
for(const tone of tones){
  const button=document.createElement('button');button.id=tone;button.textContent=tone;
  button.style='min-height:48px;padding:12px;margin:8px';
  button.addEventListener('click',event=>{
    if(!event.isTrusted||!buffers.has(tone))return;
    const row={tone,acceptedAt:performance.now(),acceptedFrame:frame,trusted:event.isTrusted,stateBefore:context.state};rows.push(row);
    if(active){try{active.stop()}catch{}active.disconnect()}
    const resumed=context.resume();row.resumeRequestedAt=performance.now();
    resumed.then(()=>{row.resumeFulfilledAt=performance.now();row.stateAfter=context.state},error=>row.error=error.name);
    const source=context.createBufferSource();source.buffer=buffers.get(tone);source.connect(gain);active=source;
    row.contextTimeAtStart=context.currentTime;
    source.onended=()=>{row.endedAt=performance.now();row.contextTimeAtEnd=context.currentTime;source.disconnect();if(active===source)active=undefined};
    source.start();row.startRequestedAt=performance.now();row.startFrame=frame;
  });document.body.append(button);
}
</script></body></html>'''
html = template.replace('__TONES__', json.dumps(list(assets))).replace('__VOLUME__', str(config['volume'])).encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        tone = self.path.removeprefix('/').removesuffix('.wav')
        data = html if self.path == '/' else assets.get(tone)
        if data is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if self.path == '/' else 'audio/wav')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


report = {'engine': args.engine, 'assetHashes': manifest, 'rows': [], 'pageErrors': [],
          'scope': 'Independent native AudioContext fixture, trusted mouse accepted input, no app modules, no product edits',
          'hardwareAudibleLatency': False, 'mutedBrowserOutput': args.engine == 'chromium'}
(OUT / 'fixture.html').write_bytes(html)
server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = getattr(p, args.engine).launch(**({'channel': 'chrome', 'args': ['--mute-audio']} if args.engine == 'chromium' else {}))
        page = browser.new_page()
        page.on('pageerror', lambda e: report['pageErrors'].append(e.stack or str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.wait_for_function('preparation.ready||preparation.error', timeout=5000)
        report['preparation'] = page.evaluate('preparation')
        report['capabilities'] = page.evaluate('({AudioContext:typeof window.AudioContext,webkitAudioContext:typeof window.webkitAudioContext,AudioBufferSourceNode:typeof window.AudioBufferSourceNode,HTMLAudioElement:typeof window.HTMLAudioElement,userAgent:navigator.userAgent})')
        (OUT / f'{args.engine}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        assert not report['preparation'].get('error'), report['preparation']
        assert page.evaluate('rows.length') == 0, 'Preparation must not schedule or play any buffer'
        for tone in assets:
            for repeat in range(3):
                index = len(report['rows'])
                page.locator('#' + tone).click()
                try:
                    page.wait_for_function('i=>!!(rows[i]?.endedAt&&rows[i]?.resumeFulfilledAt)', arg=index, timeout=1500)
                finally:
                    report['rows'] = page.evaluate('rows')
                    for value in report['rows']:
                        value['acceptedToStartMs'] = value['startRequestedAt'] - value['acceptedAt']
                        value['framesToStart'] = value['startFrame'] - value['acceptedFrame']
                    (OUT / f'{args.engine}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                row = report['rows'][-1]
                row['acceptedToStartMs'] = row['startRequestedAt'] - row['acceptedAt']
                row['framesToStart'] = row['startFrame'] - row['acceptedFrame']
                assert 0 <= row['acceptedToStartMs'] < 16 and row['framesToStart'] == 0 and row['stateAfter'] == 'running' and 'error' not in row, row
                assert row['contextTimeAtEnd'] > row['contextTimeAtStart'], row
        browser.close()
    assert not report['pageErrors'], report['pageErrors']
    report['passed'] = len(report['rows'])
    (OUT / f'{args.engine}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
finally:
    server.shutdown()
    server.server_close()
print(f'PASS {args.engine}: {len(report["rows"])} isolated native AudioBuffer starts/resumes/ends; no product changes')
