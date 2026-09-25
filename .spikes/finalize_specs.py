"""Finalize reviewed SDD drafts without fabricating user approvals."""
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
template = (root / '.kiro/settings/templates/specs/init.json').read_text(encoding='utf-8')
stamp = datetime.now(timezone.utc).isoformat()
for name in ('netpilot-foundation','netpilot-execution','netpilot-integration'):
    folder = root / '.kiro/specs' / name
    draft = folder / 'tasks.draft.md'
    target = folder / 'tasks.md'
    if draft.exists():
        assert not target.exists(), 'refuse to overwrite an existing tasks.md'
        text = draft.read_text(encoding='utf-8')
        text = text.replace('完整串行任务草案；独立任务图审查后定稿。','完整串行任务清单；独立任务图审查通过，用户批准待定。')
        text = text.replace('完整串行任务草案。','完整串行任务清单，独立审查通过，用户批准待定。')
        target.write_text(text,encoding='utf-8')
        draft.unlink()
    meta = json.loads(template.replace('{{FEATURE_NAME}}',name).replace('{{TIMESTAMP}}',stamp))
    meta['phase'] = 'tasks-generated'
    for phase in ('requirements','design','tasks'):
        meta['approvals'][phase] = {'generated':True,'approved':False}
    meta['ready_for_implementation'] = False
    meta['discovery'] = {'path':'D','direction_confirmed':True,'confirmation':'用户本对话确认多规格路线'}
    meta['review'] = {'design':'GO','task_graph':'PASS','evidence':'docs/evidence/sdd-reviews.md'}
    meta['approval_note'] = '按用户要求准备完整规格包供一次具体审阅；未把路线确认推断为每阶段内容批准。'
    (folder/'spec.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Finalized three reviewed specification packages; implementation approval remains false.')
