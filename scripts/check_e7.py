"""Check frozen E7 scientific source and canonical preregistration offline."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
folder=root/'experiments/experiment07'
plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
canonical=json.dumps(plan,sort_keys=True,ensure_ascii=False,separators=(',',':'))
if hashlib.sha256(canonical.encode()).hexdigest()!='c7658352c573dc64bf2597a89db6f3267297f4e862f08080317e4c0b698a77b4':
    raise SystemExit('E7 plan changed; register a separate cohort')
for name,expected in plan['source_sha256'].items():
    target=(folder/name).resolve()
    if not target.is_relative_to(root) or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
        raise SystemExit('Frozen E7 source/dependency mismatch: '+name)
print('Experiment 007 source, dependencies and canonical plan match preregistration.')
