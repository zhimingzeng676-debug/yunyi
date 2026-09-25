"""Check rename invariants against the immutable pre-migration commit."""
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'd80b5e4'

def original(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def rename(text):
    return text.replace('Agent NetPilot', '云驿（yunyi）').replace('NETPILOT', 'YUNYI').replace('netpilot', 'yunyi').replace('NetPilot', 'Yunyi')

counts = []
for suffix in ('foundation', 'execution', 'integration'):
    old = f'.kiro/specs/netpilot-{suffix}'
    new = ROOT / f'.kiro/specs/yunyi-{suffix}'
    assert not (ROOT / old).exists()
    for filename in ('tasks.md', 'requirements.md', 'spec.json'):
        before = original(f'{old}/{filename}').decode('utf-8').replace('\r\n', '\n')
        after = (new / filename).read_text(encoding='utf-8')
        assert after == rename(before), f'Unexpected non-naming edit: {new / filename}'
    meta = json.loads((new / 'spec.json').read_text(encoding='utf-8'))
    assert not meta['ready_for_implementation']
    assert all(not item['approved'] for item in meta['approvals'].values())
    tasks = (new / 'tasks.md').read_text(encoding='utf-8')
    ids = re.findall(r'^- \[([ x])\] (\d+\.\d+) ', tasks, re.M)
    counts.append({'spec':f'yunyi-{suffix}', 'tasks':len(ids), 'completed':sum(mark == 'x' for mark, _ in ids)})

preserved = []
line_ending_differences = []
paths = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE], cwd=ROOT).decode().splitlines()
for path in paths:
    if path.startswith('docs/evidence/') or path in ('docs/source-design.md','.spikes/tdd_probe/test_window.py','.spikes/tdd_probe/window.py'):
        before = original(path)
        after = (ROOT / path).read_bytes()
        # Existing Windows working copies may use CRLF while the original commit uses LF.
        # Do not rewrite evidence to make those bytes match; preserve committed blobs too.
        if before != after:
            assert before.replace(b'\r\n', b'\n') == after.replace(b'\r\n', b'\n'), f'Historical content changed: {path}'
            line_ending_differences.append(path)
        committed = subprocess.check_output(['git','rev-parse',f'{BASE}:{path}'],cwd=ROOT)
        indexed = subprocess.check_output(['git','rev-parse',f':{path}'],cwd=ROOT)
        assert indexed == committed, f'Historical blob changed in index: {path}'
        preserved.append(path)

claude = json.loads((ROOT / 'examples/claude-mcp.json').read_text(encoding='utf-8'))
codex = tomllib.loads((ROOT / 'examples/codex-mcp.toml').read_text(encoding='utf-8'))
for config in (claude['mcpServers'], codex['mcp_servers']):
    assert set(config) == {'yunyi'}
    assert config['yunyi']['args'] == ['-m','yunyi','mcp','--session','example']
    assert set(config['yunyi']['env']) == {'YUNYI_SESSION_ID'}

for file in [ROOT / 'README.md', ROOT / 'docs/sdd-review.md', *ROOT.glob('.kiro/specs/yunyi-*/*.md')]:
    for link in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'):
            continue
        assert (file.parent / link.split('#')[0]).exists(), f'Broken link: {file}: {link}'

assert sum(x['tasks'] for x in counts) == 40
assert sum(x['completed'] for x in counts) == 2
assert not (ROOT / 'src').exists()
report = {
    'baseline_commit':BASE, 'passed':True, 'specs':counts,
    'approvals_unchanged':True, 'task_order_and_requirements_unchanged':True,
    'historical_committed_blobs_preserved':len(preserved),
    'existing_worktree_line_ending_differences':line_ending_differences, 'examples_parse':True,
    'spec_and_entry_links_valid':True, 'product_code_created':False,
    'legacy_user_data_exists':(Path.home()/'.netpilot').exists(),
    'new_user_data_exists':(Path.home()/'.yunyi').exists(),
    'spike_database_files':[str(p.relative_to(ROOT)) for p in (ROOT/'.spikes').rglob('*') if p.is_file() and p.suffix in ('.db','.sqlite','.sqlite3')],
}
(ROOT/'docs/evidence/yunyi-naming-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
