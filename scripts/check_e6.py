"""Offline verification of Experiment 006 and its frozen scientific dependencies."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
folder = root / 'experiments/experiment06'
plan = json.loads((folder / 'plan.json').read_text(encoding='utf-8'))
canonical = json.dumps(plan, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
if hashlib.sha256(canonical.encode()).hexdigest() != '96487f3bd5b2ffa4e01253e3e7d15f29278333e6db68cb03be0dba7b2f12ff47':
    raise SystemExit('E6 plan changed; register a separate cohort')
for name, expected in plan['source_sha256'].items():
    target = (folder / name).resolve()
    if not target.is_relative_to(root) or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise SystemExit('Frozen E6 source/dependency mismatch: ' + name)
if plan['budget']['total_calls_max'] != 40 or len(plan['call_schedule']) != 40:
    raise SystemExit('Unexpected E6 call budget')
print('Experiment 006 sources, dependencies, and canonical plan match preregistration.')
