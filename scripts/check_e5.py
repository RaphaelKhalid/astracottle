"""Offline verification of Experiment 005 and its original E4 scientific source."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
folder=root/'experiments/experiment05'
plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
for base,items in [(folder,plan['source_sha256']),(root/'experiments/experiment04',plan['e4_binding']['source_sha256'])]:
    for name,expected in items.items():
        target=(base/name).resolve()
        if not target.is_relative_to(root) or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise SystemExit('Frozen source mismatch: '+name)
canonical=json.dumps(plan,sort_keys=True,ensure_ascii=False,separators=(',',':'))
if hashlib.sha256(canonical.encode()).hexdigest()!='3ebf86c15ea3f06c3a1adb79e273440d05674489282fb91c49b049478b9e7d02':
    raise SystemExit('E5 plan changed; register a separate cohort')
print('Experiment 005 source and canonical plan match preregistration.')
