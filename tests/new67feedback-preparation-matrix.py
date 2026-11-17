"""Two HTTP response fixtures over an unchanged native build: isolate PCM from preparation timing."""
import argparse
import ast
import hashlib
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import TimeoutError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--label', required=True)
args = parser.parse_args()
OUT = ROOT / 'tmp/planning/iteration67/feedback-preparation-matrix' / args.label
OUT.mkdir(parents=True, exist_ok=False)
candidate = ROOT / 'tmp/frozen67-3ba/native'
baseline = ROOT / 'tmp/frozen67-baseline5d/native'
feedback_path, = candidate.glob('_astro/feedback.*.js')
original_js = feedback_path.read_bytes()
body = original_js.decode('utf-8')
assert body.count(',a.load()') == 1 and body.count('t(),i(),document.addEventListener') == 1
lazy_js = body.replace(',a.load()', '').replace('t(),i(),document.addEventListener', 't(),document.addEventListener').encode('utf-8')
current_pcm = (candidate / 'audio/67/select.wav').read_bytes()
old_pcm = (baseline / 'audio/select.wav').read_bytes()
tree = ast.parse((ROOT / 'tests/new67feedback-latency.py').read_text(encoding='utf-8'))
spy = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPY' for t in n.targets))
results = []
with sync_playwright() as p:
    browser = p.webkit.launch()
    for cell, script, pcm, eager in [('B-newPCM-oldPreparation', lazy_js, current_pcm, False), ('C-oldPCM-eagerPreparation', original_js, old_pcm, True)]:
        row = {'cell': cell, 'candidateBuild': '3ba12c28fc1d550e9d1b', 'baselinePCMBuild': '5d36176754bbdd000991',
               'originalJsSha256': hashlib.sha256(original_js).hexdigest(), 'servedJsSha256': hashlib.sha256(script).hexdigest(),
               'servedPcmSha256': hashlib.sha256(pcm).hexdigest(), 'pageErrors': [], 'servedOverrides': [],
               'scope': 'HTTP response fixtures only; one first accepted select; no product/build bytes changed, warm play, retry or next input'}

        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                data = script if path == '/' + feedback_path.relative_to(candidate).as_posix() else pcm if path == '/audio/67/select.wav' else None
                if data is None:
                    return super().do_GET()
                row['servedOverrides'].append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript' if path.endswith('.js') else 'audio/wav')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def copyfile(self, source, outputfile):
                try:
                    return super().copyfile(source, outputfile)
                except (ConnectionResetError, BrokenPipeError):
                    row['clientDisconnects'] = row.get('clientDisconnects', 0) + 1

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(candidate)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f'http://127.0.0.1:{server.server_port}/'
        try:
            context = browser.new_context(viewport={'width': 800, 'height': 900})
            context.add_init_script(spy)
            context.route('**/*', lambda route: route.continue_() if urlsplit(route.request.url).netloc == urlsplit(origin).netloc else route.abort())
            page = context.new_page()
            page.on('pageerror', lambda e: row['pageErrors'].append(e.stack or str(e)))
            page.goto(origin, wait_until='domcontentloaded')
            page.wait_for_timeout(450)
            if eager:
                page.wait_for_function('__preparedAudio.length===4&&__preparedAudio.every(a=>a.readyState>=2)', timeout=5000)
            row['preInput'] = page.evaluate('({at:performance.now(),playRequests:__feedback.length,explicitLoads:__preparedAudio.map(a=>({src:a.src,ready:a.readyState,time:a.currentTime,paused:a.paused,ended:a.ended}))})')
            assert row['preInput']['playRequests'] == 0
            page.evaluate("""()=>{const b=document.createElement('button');b.id='feedback-latency-probe';b.textContent='Проверка действия';b.style='position:fixed;top:100px;left:50px;z-index:9999;min-height:48px;padding:12px;background:#ffcc29';b.dataset.uiKind='selection';b.addEventListener('click',e=>__accepted.push({at:performance.now(),frame:__frames,type:e.type,trusted:e.isTrusted}));document.body.append(b)}""")
            rect = page.locator('#feedback-latency-probe').bounding_box()
            page.mouse.move(rect['x'] + rect['width']/2, rect['y'] + rect['height']/2)
            page.mouse.down()
            page.wait_for_timeout(20)
            page.mouse.up()
            page.wait_for_function('__feedback.length===1')
            try:
                page.wait_for_function('__feedback[0].playingAt&&__feedback[0].fulfilledAt', timeout=1500)
                row['nativeConfirmed'] = True
            except TimeoutError:
                row['nativeConfirmed'] = False
            row['samples'] = page.evaluate('__feedback.map((r,i)=>({...r,stateAfter:{readyState:__feedbackPlayers[i].readyState,paused:__feedbackPlayers[i].paused,ended:__feedbackPlayers[i].ended,currentTime:__feedbackPlayers[i].currentTime,duration:__feedbackPlayers[i].duration,error:__feedbackPlayers[i].error?.code}}))')
            for sample in row['samples']:
                sample['acceptedToPlayMs'] = sample['at'] - sample['accepted']
                sample['framesToPlay'] = sample['frame'] - sample['acceptedFrame']
                if 'playingAt' in sample:
                    sample['acceptedToPlayingMs'] = sample['playingAt'] - sample['accepted']
            assert any(r['path'] == '/audio/67/select.wav' for r in row['servedOverrides']), 'No proof that native audio received fixture PCM'
            context.close()
        finally:
            server.shutdown()
            server.server_close()
            results.append(row)
            (OUT / 'webkit.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    browser.close()
assert feedback_path.read_bytes() == original_js, 'Frozen feedback bundle changed'
print(json.dumps([{'cell': r['cell'], 'nativeConfirmed': r['nativeConfirmed'], 'samples': r['samples'], 'pageErrors': r['pageErrors']} for r in results], ensure_ascii=False, indent=2))
