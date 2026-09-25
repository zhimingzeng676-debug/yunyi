"""Disposable owned process-tree fixture; no product code."""
import subprocess
import sys
import time
from pathlib import Path

root = Path(sys.argv[1])
role = sys.argv[2]
child = None
if role == 'parent':
    child = subprocess.Popen(
        [sys.executable, __file__, str(root), 'child'],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    (root / 'child.pid').write_text(str(child.pid))
try:
    while True:
        with (root / (role + '.ticks')).open('ab') as stream:
            stream.write(b'x')
        time.sleep(0.05)
finally:
    if child is not None:
        child.terminate()
