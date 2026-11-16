from runpy import run_path
from pathlib import Path
globals().update({k:v for k,v in run_path(str(Path(__file__).with_name('iteration18-browser.py')),run_name='qa_helpers').items() if not k.startswith('__')})
