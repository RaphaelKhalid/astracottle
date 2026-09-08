"""Offline verification of the unchanged Experiment 004 preregistration."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
folder = root / 'experiments/experiment04'
plan = json.loads((folder / 'plan.json').read_text(encoding='utf-8'))
for name, expected in plan['source_sha256'].items():
    target = (folder / name).resolve()
    if not target.is_relative_to(root):
        raise SystemExit('Frozen source path escapes repository')
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise SystemExit('Frozen source mismatch: ' + name)
canonical = json.dumps(plan, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
if hashlib.sha256(canonical.encode()).hexdigest() != 'dfa36888516b64772223e202f83ffdb4dfebf794101761fa7af881bade0a5f55':
    raise SystemExit('Preregistered plan changed; register a separate experiment')
print('Experiment 004 source and canonical plan match the preregistration.')
