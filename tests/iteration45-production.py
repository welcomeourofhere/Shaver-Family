"""Verify the current build without changing the generated files."""
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
env = {**os.environ, 'QA_URL': f'http://127.0.0.1:{server.server_address[1]}/', 'QA_REPORT_PREFIX': 'iteration45'}
commands = [
    (['node', 'tests/iteration45-ui.mjs'], {}),
    (['node', 'tests/iteration45-dock-motion.mjs'], {}),
    (['node', 'tests/iteration44-ui.mjs'], {}),
    (['node', 'tests/iteration44-story-zoom.mjs'], {}),
    (['node', 'tests/iteration44-motion.mjs'], {}),
    (['node', 'tests/iteration39-layout.mjs'], {}),
    (['node', 'tests/iteration39-journeys.mjs'], {}),
    (['node', 'tests/iteration39-motion.mjs'], {'QA_MOTION_ONLY': 'dock'}),
    (['node', 'tests/iteration43-interrupt.mjs'], {}),
    (['node', 'tests/iteration43-focus.mjs'], {}),
]
results = []
try:
    for command, extra in commands:
        result = subprocess.run(command, cwd=root, env={**env, **extra}, timeout=240)
        results.append({'command': command, **extra, 'exit': result.returncode})
        if result.returncode: raise SystemExit(result.returncode)
    if before != hashes(): raise SystemExit('Built artifact changed during verification')
finally:
    report = root / 'tmp/planning/iteration45-verification.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'commands': results, 'files': len(before), 'artifactUnchanged': before == hashes(),
                                  'indexSha256': before['index.html'], 'published': False}, indent=2), encoding='utf-8')
    server.shutdown()
    server.server_close()
