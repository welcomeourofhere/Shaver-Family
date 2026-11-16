"""Verify the editorial layout, cold startup and motion on one frozen build."""
import functools, hashlib, http.server, json, os, pathlib, subprocess, threading

root = pathlib.Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def hashes():
    return {str(p.relative_to(root / 'dist')): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root / 'dist').rglob('*') if p.is_file()}

before = hashes()
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(root / 'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_address[1]}/'
env = {**os.environ, 'QA_URL': url, 'SWIPE_TEST_URL': url, 'QA_REPORT_PREFIX': 'iteration46',
       'SWIPE_TEST_REPORT': 'tmp/planning/iteration46-swipes.json', 'QA_BASELINE': 'tmp/baseline46/dist', 'QA_DESKTOP_HOME_ONLY': '1'}
commands = [
    ['node', 'tests/iteration46-startup.mjs'],
    ['node', 'tests/iteration46-editorial.mjs'],
    ['node', 'tests/iteration46-timing.mjs'],
    ['node', 'tests/iteration45-ui.mjs'],
    ['node', 'tests/iteration45-dock-motion.mjs'],
    ['node', 'tests/iteration44-story-zoom.mjs'],
    ['node', 'tests/iteration44-motion.mjs'],
    ['node', 'tests/iteration39-layout.mjs'],
    ['node', 'tests/iteration39-journeys.mjs'],
    ['node', 'tests/iteration39-motion.mjs'],
    ['node', 'tests/iteration43-interrupt.mjs'],
    ['node', 'tests/iteration43-focus.mjs'],
    ['node', 'tests/iteration37-swipes.mjs'],
    ['python', 'tests/iteration39-desktop.py'],
    ['node', 'tests/iteration46-captures.mjs'],
]
results = []
final_only = bool(os.environ.get('QA_ARTICLE_FINAL_ONLY'))
if final_only:
    commands = [['node', 'tests/iteration46-editorial.mjs'], ['node', 'tests/iteration44-story-zoom.mjs'],
                ['node', 'tests/iteration39-journeys.mjs'], ['node', 'tests/iteration46-startup.mjs'],
                ['node', 'tests/iteration46-timing.mjs'], ['node', 'tests/iteration46-captures.mjs']]
try:
    for command in commands:
        result = subprocess.run(command, cwd=root, env=env, timeout=600)
        results.append({'command': command, 'exit': result.returncode})
        if result.returncode: raise SystemExit(result.returncode)
    if before != hashes(): raise SystemExit('Built artifact changed during verification')
finally:
    report = root / ('tmp/planning/iteration46-final-verification.json' if final_only else 'tmp/planning/iteration46-verification.json')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'commands': results, 'files': len(before), 'artifactUnchanged': before == hashes(),
                                  'indexSha256': before['index.html'], 'published': False}, indent=2), encoding='utf-8')
    server.shutdown()
    server.server_close()
