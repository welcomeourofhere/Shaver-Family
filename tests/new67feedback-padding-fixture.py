"""Native compiled-page playback with only literal tap/select WAV silent-tail response fixtures."""
import argparse
import ast
import hashlib
import io
import json
import threading
import wave
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import TimeoutError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--label', required=True)
parser.add_argument('--engine', choices=['chromium', 'webkit'], required=True)
parser.add_argument('--repeats', type=int, choices=[1, 2], default=2)
parser.add_argument('--open-mode',choices=['original','reference','tail208'],default='original')
parser.add_argument('--roles',default='tap,select,open,close')
parser.add_argument('--all-reference',action='store_true')
parser.add_argument('--collect-all',action='store_true',help='Continue to next fresh role context after failure, never replay the failed cue')
parser.add_argument('--seek-reset',action='store_true',help='Original PCM; fixture only restores unconditional currentTime=0 setter')
args = parser.parse_args()
roles=args.roles.split(',');assert roles and len(roles)==len(set(roles))and all(t in ['tap','select','open','close']for t in roles)
OUT = ROOT / 'tmp/planning/iteration67/feedback-padding-fixture' / args.label
OUT.mkdir(parents=True, exist_ok=False)
BUILD = ROOT / 'tmp/frozen67-3ba/native'
feedback_path, = BUILD.glob('_astro/feedback.*.js')
original_bundle=feedback_path.read_bytes()
bundle_hash = hashlib.sha256(original_bundle).hexdigest()
served_bundle=original_bundle
if args.seek_reset:
    fragment=b'l.currentTime!==0&&(l.currentTime=0)'
    assert original_bundle.count(fragment)==1
    served_bundle=original_bundle.replace(fragment,b'l.currentTime=0')
assets = {tone: (BUILD / f'audio/67/{tone}.wav').read_bytes() for tone in ['tap', 'select', 'open', 'close']}
provenance = {}
durations={}if args.seek_reset or args.all_reference else{'tap':.128,'select':.128,**({'open':.208}if args.open_mode=='tail208'else{})}
for tone in durations:
    original = assets[tone]
    with wave.open(io.BytesIO(original), 'rb') as reader:
        params = reader.getparams()
        prefix = reader.readframes(reader.getnframes())
    target_frames = round(params.framerate * durations[tone])
    assert params.nframes < target_frames and params.sampwidth == 2 and params.nchannels == 1
    tail = b'\0' * ((target_frames - params.nframes) * params.sampwidth * params.nchannels)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as writer:
        writer.setparams(params)
        writer.writeframes(prefix + tail)
    assets[tone] = buffer.getvalue()
    provenance[tone] = {'originalSha256': hashlib.sha256(original).hexdigest(), 'fixtureSha256': hashlib.sha256(assets[tone]).hexdigest(),
                        'pcmPrefixSha256': hashlib.sha256(prefix).hexdigest(), 'originalFrames': params.nframes,
                        'fixtureFrames': target_frames, 'addedSilentSamples': len(tail)//2, 'onlySilentTail': True}
    (OUT / f'{tone}-{round(durations[tone]*1000)}.wav').write_bytes(assets[tone])
if args.open_mode=='reference':
    assets['open']=(ROOT/'tmp/frozen67-baseline5d/native/audio/open.wav').read_bytes()
    provenance['open']={'control':'literal baseline5d open208ms, not a padded new voice','fixtureSha256':hashlib.sha256(assets['open']).hexdigest()}
tree = ast.parse((ROOT / 'tests/new67feedback-latency.py').read_text(encoding='utf-8'))
spy = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SPY' for t in n.targets))
if args.all_reference:
    assets={tone:(ROOT/f'tmp/frozen67-baseline5d/native/audio/{tone}.wav').read_bytes()for tone in assets}
    provenance={tone:{'control':'literal baseline5d PCM','fixtureSha256':hashlib.sha256(data).hexdigest()}for tone,data in assets.items()}
report = {'engine': args.engine, 'build': '3ba12c28fc1d550e9d1b', 'bundleSha256': bundle_hash,'servedBundleSha256':hashlib.sha256(served_bundle).hexdigest(),'unconditionalSeekFixture':args.seek_reset,'allReferencePCM':args.all_reference,
          'roles':roles,'openMode':args.open_mode,'provenance': provenance, 'rows': [], 'servedAudio': [], 'pageErrors': [],
          'scope': 'Unchanged actual compiled JS with eager preparation; only HTTP WAV response fixtures. Each native playing/promise precedes next input. No warm play, retry, hardware measurement or product edit.'}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path=='/'+feedback_path.relative_to(BUILD).as_posix()and args.seek_reset:
            report['servedJsSha256']=hashlib.sha256(served_bundle).hexdigest();self.send_response(200);self.send_header('Content-Type','application/javascript');self.send_header('Content-Length',str(len(served_bundle)));self.end_headers();self.wfile.write(served_bundle);return
        tone = path.removeprefix('/audio/67/').removesuffix('.wav')
        if not path.startswith('/audio/67/') or tone not in assets:
            return super().do_GET()
        body = assets[tone]
        report['servedAudio'].append({'tone': tone, 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)})
        self.send_response(200)
        self.send_header('Content-Type', 'audio/wav')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def copyfile(self, source, outputfile):
        try:
            return super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            report['clientDisconnects'] = report.get('clientDisconnects', 0) + 1

    def log_message(self, *_args):
        pass


def save():
    (OUT / f'{args.engine}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(BUILD)))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f'http://127.0.0.1:{server.server_port}/'
failed = False
try:
    with sync_playwright() as p:
        browser = getattr(p, args.engine).launch(**({'channel': 'chrome', 'args': ['--mute-audio']} if args.engine == 'chromium' else {}))
        for tone in roles:
            role_failed=False
            context = browser.new_context(viewport={'width': 800, 'height': 900})
            context.add_init_script(spy)
            context.route('**/*', lambda r: r.continue_() if urlsplit(r.request.url).netloc == urlsplit(origin).netloc else r.abort())
            page = context.new_page()
            page.on('pageerror', lambda e: report['pageErrors'].append(e.stack or str(e)))
            page.goto(origin, wait_until='domcontentloaded')
            page.wait_for_function('__preparedAudio.length===4&&__preparedAudio.every(a=>a.readyState>=2)', timeout=5000)
            entry = {'tone': tone, 'preInput': page.evaluate('({at:performance.now(),playRequests:__feedback.length,prepared:__preparedAudio.map(a=>({src:a.src,ready:a.readyState,time:a.currentTime,paused:a.paused,ended:a.ended}))})')}
            report['rows'].append(entry)
            assert entry['preInput']['playRequests'] == 0
            page.evaluate("""tone=>{const b=document.createElement('button');b.id='feedback-latency-probe';b.textContent='Проверка действия';b.style='position:fixed;top:100px;left:50px;z-index:9999;min-height:48px;padding:12px;background:#ffcc29';b.dataset.uiKind=tone==='select'?'selection':tone==='open'||tone==='close'?'disclosure':'filled';if(tone==='open'||tone==='close')b.setAttribute('aria-expanded',String(tone==='close'));b.addEventListener('click',e=>{if(b.hasAttribute('aria-expanded'))b.setAttribute('aria-expanded',String(b.getAttribute('aria-expanded')!=='true'));__accepted.push({at:performance.now(),frame:__frames,type:e.type,trusted:e.isTrusted})});document.body.append(b)}""", tone)
            for repeat in range(args.repeats):
                if tone in ['open', 'close']:
                    page.locator('#feedback-latency-probe').evaluate('(b,t)=>b.setAttribute("aria-expanded",String(t==="close"))', tone)
                rect = page.locator('#feedback-latency-probe').bounding_box()
                page.mouse.move(rect['x']+rect['width']/2, rect['y']+rect['height']/2)
                page.mouse.down()
                page.wait_for_timeout(20)
                page.mouse.up()
                page.wait_for_function('n=>__feedback.length===n', arg=repeat+1)
                try:
                    page.wait_for_function('i=>__feedback[i].playingAt&&__feedback[i].fulfilledAt', arg=repeat, timeout=1500)
                except TimeoutError:
                    failed = True
                    role_failed=True
                entry['samples'] = page.evaluate('__feedback.map((r,i)=>({...r,stateAfter:{readyState:__feedbackPlayers[i].readyState,paused:__feedbackPlayers[i].paused,ended:__feedbackPlayers[i].ended,currentTime:__feedbackPlayers[i].currentTime,duration:__feedbackPlayers[i].duration,error:__feedbackPlayers[i].error?.code}}))')
                for sample in entry['samples']:
                    sample['acceptedToPlayMs'] = sample['at'] - sample['accepted']
                    sample['framesToPlay'] = sample['frame'] - sample['acceptedFrame']
                    if 'playingAt' in sample:
                        sample['acceptedToPlayingMs'] = sample['playingAt'] - sample['accepted']
                save()
                if role_failed:
                    break
                # Finish this exact playback before the next accepted event; no later event can satisfy an old listener.
                page.wait_for_timeout(200)
            context.close()
            if failed and not args.collect_all:
                break
        browser.close()
finally:
    server.shutdown()
    server.server_close()
    save()
assert feedback_path.read_bytes() and hashlib.sha256(feedback_path.read_bytes()).hexdigest() == bundle_hash
assert not report['pageErrors'], report['pageErrors']
assert not failed, 'One native playback did not confirm playing/promise within1500ms; preserved raw report'
assert len(report['rows']) == len(roles) and all(len(r['samples']) == args.repeats for r in report['rows'])
for row in report['rows']:
    for sample in row['samples']:
        assert sample['src'] == f'/audio/67/{row["tone"]}.wav' and sample['framesToPlay'] == 0 and 0 <= sample['acceptedToPlayMs'] < 16 and 'error' not in sample, sample
print(f'PASS {args.engine}: {len(roles)*args.repeats} independent native plays, seekReset={args.seek_reset} openMode={args.open_mode}; product unchanged')
