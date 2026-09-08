"""Verify the frozen experiment source without starting a model or loading auth."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
folder = root / 'experiments' / 'experiment02'
plan = json.loads((folder / 'plan.json').read_text(encoding='utf-8'))
for name, expected in plan['source_sha256'].items():
    target = (folder / name).resolve()
    if not target.is_relative_to(root):
        raise SystemExit('Frozen source path escapes the repository')
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise SystemExit('Frozen source mismatch: ' + name)
canonical = json.dumps(plan, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
if hashlib.sha256(canonical.encode()).hexdigest() != 'd86d50f1221fd85bdf84562839a1e416922e086af06ea18b5334849a21ccba44':
    raise SystemExit('Preregistered plan changed; register a separate experiment')
print('Frozen experiment source and canonical plan match the preregistration.')
