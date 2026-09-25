"""One synthetic read-only request per existing CLI; no credential inspection."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
name = sys.argv[1]
work = ROOT / '.spikes' / 'runtime' / ('live-' + name)
work.mkdir(parents=True, exist_ok=True)
schema = {'type': 'object', 'properties': {'ready': {'type': 'boolean'}}, 'required': ['ready'], 'additionalProperties': False}
(work / 'schema.json').write_text(json.dumps(schema), encoding='utf-8')
(work / 'empty-mcp.json').write_text('{"mcpServers":{}}', encoding='utf-8')
prompt = 'Dependency compatibility test. Return exactly the JSON object {"ready":true}. Do not use any tools, read any files, or modify anything.'
if name == 'claude':
    argv = ['C:/Users/32655/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe', '-p', '--safe-mode', '--tools', '', '--strict-mcp-config', '--mcp-config', str(work / 'empty-mcp.json'), '--setting-sources', '', '--output-format', 'json', '--json-schema', json.dumps(schema)]
elif name == 'codex':
    argv = ['C:/Users/32655/AppData/Local/OpenAI/Codex/bin/247581e40ee272fb/codex.exe', 'exec', '--ignore-user-config', '--ephemeral', '--sandbox', 'read-only', '--skip-git-repo-check', '--output-schema', str(work / 'schema.json'), '--output-last-message', str(work / 'response.json'), '--json', '-C', str(work), '-']
else:
    raise SystemExit('unknown harness')
env = dict(os.environ)
env.pop('CLAUDECODE', None)
start = time.monotonic()
proc = subprocess.Popen(argv, cwd=work, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
timed_out = False
try:
    out, err = proc.communicate(prompt.encode('utf-8'), timeout=55)
except subprocess.TimeoutExpired:
    timed_out = True
    import psutil
    root = psutil.Process(proc.pid)
    children = root.children(recursive=True)
    for child in reversed(children):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    proc.kill()
    out, err = proc.communicate(timeout=5)

def scrub(value):
    value = re.sub(r'(?i)(bearer\s+)[^\s"<>]+', r'\1[REDACTED]', value)
    value = re.sub(r'(?i)\b(sk-|sk-ant-)[a-z0-9_\-]+', '[REDACTED]', value)
    return value[:16000]

artifact = {'harness':name,'elapsed_seconds':round(time.monotonic()-start,2),'exit_code':proc.returncode,'timed_out':timed_out,'request_count_limit':1,'synthetic_prompt_only':True,'stdout':scrub(out.decode('utf-8',errors='replace')),'stderr':scrub(err.decode('utf-8',errors='replace'))}
result_file = work / 'response.json'
if result_file.exists():
    artifact['response_file'] = scrub(result_file.read_text(encoding='utf-8'))
(ROOT / 'docs' / 'evidence' / (name + '-live-spike.json')).write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(artifact,ensure_ascii=False))
sys.exit(0 if proc.returncode == 0 and not timed_out else 1)
