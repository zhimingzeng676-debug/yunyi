"""Invoke the unmodified Agentic TDD verification scripts using argv."""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.spikes' / 'tdd_probe'
SCRIPTS = Path('C:/Users/32655/.claude/skills/agentic-tdd/skills/tdd/scripts')
TSX = ROOT / '.tools' / 'node_modules' / 'tsx' / 'dist' / 'cli.mjs'
EVIDENCE = ROOT / 'docs' / 'evidence'
TEST_COMMAND = 'D:/anaconda3/envs/pack311/python.exe -m pytest -q'

def invoke(name, extra, label=None):
    argv = ['node', str(TSX), str(SCRIPTS / (name + '.ts')), '--working-dir', str(WORK), *extra]
    completed = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=45)
    artifact = {'script': name, 'exit_code': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr}
    (EVIDENCE / ((label or name) + '.json')).write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(artifact, ensure_ascii=False))
    if completed.returncode:
        raise SystemExit(completed.returncode)
    return json.loads(completed.stdout)

phase = sys.argv[1]
if phase == 'red':
    raw = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'test_window.py', '--junitxml=' + str(EVIDENCE / 'tdd-red-tests.xml')], cwd=WORK, capture_output=True, text=True, encoding='utf-8', timeout=30)
    (EVIDENCE / 'tdd-red-tests.log').write_text(raw.stdout + raw.stderr, encoding='utf-8')
    assert raw.returncode == 1, 'RED must be collected failing tests, not invocation or collection error'
    assert 'AssertionError' in raw.stdout
    report = ET.parse(EVIDENCE / 'tdd-red-tests.xml').getroot()
    suites = list(report.iter('testsuite'))
    assert sum(int(s.get('tests', '0')) for s in suites) > 0
    assert sum(int(s.get('errors', '0')) for s in suites) == 0
    assert sum(int(s.get('failures', '0')) for s in suites) > 0
    invoke('init-state', ['--spec', 'Disposable threshold toolchain spike', '--entry-mode', 'PLAN_EXECUTION', '--framework-json', json.dumps({'language':'python','testRunner':'pytest','testCommand':TEST_COMMAND}), '--work-units-json', json.dumps([{'id':'window','name':'window spike','specContract':'trailing-success threshold and positive threshold validation','unitType':'code','wave':'backend'}]), '--parallel', '1'])
    red = invoke('verify-red', ['--test-files','test_window.py','--test-command',TEST_COMMAND,'--language','python','--entry-mode','plan-execution'])
    invoke('update-state', ['--unit-id','window','--status','RED_VERIFICATION','--red-json',json.dumps(red),'--test-files','test_window.py','--impl-files','window.py'], 'state-red')
elif phase == 'green':
    red_artifact = json.loads((EVIDENCE / 'verify-red.json').read_text(encoding='utf-8'))
    red = json.loads(red_artifact['stdout'])
    green = invoke('verify-green', ['--test-files','test_window.py','--test-command',TEST_COMMAND,'--language','python','--checksums-json',json.dumps(red['testFileChecksums'])])
    invoke('update-state', ['--unit-id','window','--status','GREEN_VERIFICATION','--green-json',json.dumps(green)], 'state-green')
elif phase == 'check':
    invoke('check-state', [])
elif phase == 'finish':
    reviews = json.loads((EVIDENCE / 'tdd-independent-reviews.json').read_text(encoding='utf-8'))
    assert reviews['spec']['status'] == 'COMPLIANT'
    assert reviews['adversarial']['status'] == 'PASS'
    assert reviews['quality']['status'] == 'Approved'
    # The review prompts emit verdicts, while the report renderer expects lowercase statuses.
    normalized = {key: dict(reviews[key]) for key in ('spec', 'adversarial', 'quality')}
    for key, status in [('spec', 'compliant'), ('adversarial', 'passed'), ('quality', 'approved')]:
        normalized[key]['status'] = status
    invoke('update-state', ['--unit-id','window','--status','COMPLETED',
        '--spec-compliance-json',json.dumps(normalized['spec']),
        '--adversarial-json',json.dumps(normalized['adversarial']),
        '--code-quality-json',json.dumps(normalized['quality'])], 'state-completed')
    state_path = WORK / '.tdd-state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    # update-state has no attempt-count option; record actual dispatch counts without altering proofs.
    state['workUnits'][0]['testWriterAttempts'] = 1
    state['workUnits'][0]['codeWriterAttempts'] = 1
    state['framework'].update(testFilePattern='test_*.py', sourceDir='.', testDir='.')
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    invoke('log-event', ['--event','unit.completed','--unit-id','window'])
    invoke('check-state', [])
    invoke('generate-report', [])
else:
    raise SystemExit('expected red, green, check or finish')
