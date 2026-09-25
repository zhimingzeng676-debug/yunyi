"""Mechanical draft completeness check; not a replacement for human approval."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
results = []
for folder in sorted((root / '.kiro' / 'specs').iterdir()):
    requirements = (folder / 'requirements.md').read_text(encoding='utf-8')
    design = (folder / 'design.md').read_text(encoding='utf-8')
    taskfile = folder / 'tasks.md'
    if not taskfile.exists():
        taskfile = folder / 'tasks.draft.md'
    tasks = taskfile.read_text(encoding='utf-8')
    ids = set(re.findall(r'^- (\d+\.\d+) ', requirements, re.M))
    mapped = set()
    for line in re.findall(r'_Requirements: ([\d., ]+)_', tasks):
        mapped.update(v.strip() for v in line.split(','))
    task_ids = re.findall(r'^- \[[ x]\] (\d+\.\d+) ', tasks, re.M)
    dependencies = []
    for text in re.findall(r'_Depends: ([\d., ]+)_', tasks):
        dependencies.extend(v.strip() for v in text.split(','))
    problems = []
    if ids - mapped:
        problems.append('unmapped requirements: ' + str(sorted(ids - mapped)))
    if mapped - ids:
        problems.append('undefined requirement references: ' + str(sorted(mapped - ids)))
    missing_design = [v for v in ids if not re.search(r'(?<![\d.])' + re.escape(v) + r'(?![\d.])', design)]
    if missing_design:
        problems.append('missing design mapping: ' + str(missing_design))
    if len(task_ids) != len(set(task_ids)):
        problems.append('duplicate task ids')
    if set(dependencies) - set(task_ids):
        problems.append('unknown task dependency: ' + str(set(dependencies) - set(task_ids)))
    for heading in ['Boundary Commitments','Out of Boundary','Allowed Dependencies','Revalidation Triggers','File Structure Plan']:
        if heading not in design:
            problems.append('missing section: ' + heading)
    results.append({'spec':folder.name,'requirements':len(ids),'tasks':len(task_ids),'problems':problems})
artifact = {'passed':all(not r['problems'] for r in results),'specs':results,'limitations':'Checks references and required sections only; no approval or semantic GO implied.'}
(root / 'docs' / 'evidence' / 'yunyi-sdd-mechanical-check.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(artifact,ensure_ascii=False,indent=2))
raise SystemExit(0 if artifact['passed'] else 1)
