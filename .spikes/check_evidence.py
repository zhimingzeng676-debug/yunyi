"""Preflight proof checks and anti-cheat negative control, not product tests."""
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs' / 'evidence'
red = json.loads(json.loads((E / 'verify-red.json').read_text(encoding='utf-8'))['stdout'])
green = json.loads(json.loads((E / 'verify-green.json').read_text(encoding='utf-8'))['stdout'])
suite = ET.parse(E / 'tdd-red-tests.xml').getroot().find('testsuite')
assert suite is not None

def strict_red(exit_code, junit_path):
    if exit_code != 1 or not junit_path.exists():
        return False
    suites = list(ET.parse(junit_path).getroot().iter('testsuite'))
    return (sum(int(s.get('tests','0')) for s in suites) > 0
            and sum(int(s.get('failures','0')) for s in suites) > 0
            and sum(int(s.get('errors','0')) for s in suites) == 0
            and sum(int(s.get('skipped','0')) for s in suites) == 0)

assert strict_red(1, E / 'tdd-red-tests.xml')
assert not strict_red(1, E / 'missing-runner-no-junit.xml')
assert not strict_red(2, E / 'tdd-red-tests.xml')
assert not strict_red(5, E / 'tdd-red-tests.xml')
assert not strict_red(0, E / 'tdd-red-tests.xml')
assert int(suite.get('failures')) == 18 and int(suite.get('tests')) == 30
actual_hash = hashlib.sha256((ROOT / '.spikes' / 'tdd_probe' / 'test_window.py').read_bytes()).hexdigest()
assert actual_hash == red['testFileChecksums']['test_window.py']
assert green['testsPassed'] and green['testFilesUnchanged'] and not green['skipMarkersFound']

# Run the unmodified GREEN verifier against a disposable deliberately changed copy.
tamper = ROOT / '.spikes' / 'runtime' / 'tampered-green'
tamper.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / '.spikes' / 'tdd_probe' / 'window.py', tamper / 'window.py')
test_bytes = (ROOT / '.spikes' / 'tdd_probe' / 'test_window.py').read_bytes()
(tamper / 'test_window.py').write_bytes(test_bytes + b'\n# deliberate negative-control modification\n')
argv = ['node', str(ROOT / '.tools/node_modules/tsx/dist/cli.mjs'),
        'C:/Users/32655/.claude/skills/agentic-tdd/skills/tdd/scripts/verify-green.ts',
        '--working-dir',str(tamper),'--test-files','test_window.py',
        '--test-command','D:/anaconda3/envs/pack311/python.exe -m pytest -q',
        '--language','python','--checksums-json',json.dumps(red['testFileChecksums'])]
probe = subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=40)
tamper_result = json.loads(probe.stdout)
assert probe.returncode == 1 and tamper_result['testsPassed'] and not tamper_result['testFilesUnchanged']
(E / 'tampered-green-negative-control.json').write_text(json.dumps({'exit_code':probe.returncode,'result':tamper_result},indent=2),encoding='utf-8')

live_results = {}
for name in ['claude','codex']:
    artifact = json.loads((E / (name+'-live-spike.json')).read_text(encoding='utf-8'))
    assert artifact['exit_code'] == 0 and not artifact['timed_out']
    if name == 'claude':
        envelope = json.loads(artifact['stdout'])
        result = envelope['structured_output']
        assert envelope['is_error'] is False
    else:
        result = json.loads(artifact['response_file'])
        events = [json.loads(line) for line in artifact['stdout'].splitlines()]
        assert not any(x.get('item',{}).get('type') in ('command_execution','mcp_tool_call') for x in events)
    assert result == {'ready': True}
    live_results[name] = {'ready':True,'elapsed_seconds':artifact['elapsed_seconds']}
result = {'scope':'dependency_and_workflow_spikes_only','strict_red':True,
          'red_cases':{'failed':18,'passed':12},'green_cases':30,
          'test_hash_unchanged':True,'changed_test_rejected':True,
          'invalid_runner_no_junit_rejected':True,'non_test_exit_codes_rejected':True,
          'live_minimum_requests':live_results,
          'product_implemented':False,'minimum_product_loop_verified':False}
(E / 'preflight-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
