"""Offline public export of E5, bound to the independently audited public E4 data.

No transport import, model calls, or publication. Requires --report, --source,
--e4-data, and a new --output file. Only supplied public content and scientific
measurements are retained; runtime account/session/exception data are omitted.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import statistics

from export_experiment04 import USAGE_KEYS, audit_private_sessions, compact, measured, require, response, sha
from public_safety_check import scan_paths

VIEWS = ('none', 'carried', 'independent')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_records(e4, world, carried, independent):
    available = independent is not None
    canonical_equal = compact(carried) == compact(independent) if available else None
    semantic_equal = e4._semantic(carried) == e4._semantic(independent) if available else None
    return {'comparison_available': available,
            'canonical_equal_array_order_retained': canonical_equal,
            'source_facts_equal_array_order_ignored': semantic_equal,
            'carried_extraction_fidelity': e4.extraction_score(world, carried),
            'independent_extraction_fidelity': e4.extraction_score(world, independent) if available else None,
            'interpretation': ('Canonical artifacts are identical. Carried and independent review calls are fresh repeats '
                               'of the same supplied input; response differences cannot identify content or provenance effects.'
                               if canonical_equal else
                               'Artifact comparison does not by itself identify a pure provenance effect.')}


def export(report_path, source, e4_data_path, output):
    require(not output.exists(), 'Public output exists; no silent replacement')
    report = read(report_path)
    frozen = read(report_path.parent / 'frozen_plan.json')
    e4_data = read(e4_data_path)
    require(sha(frozen) == report['plan_sha256'], 'E5 report differs from frozen canonical protocol')
    require(e4_data['completed'] and e4_data['counts']['saved_responses'] == 104, 'Bound public E4 cohort is incomplete')
    require(e4_data['protocol_canonical_sha256'] == frozen['e4_binding']['plan_sha256'], 'E4 public cohort has another protocol')
    require(set(frozen['source_sha256']) == {'prepare.py', 'run_diagnostic.py', 'selftest.py', 'protocol.md', '../pilot/transport.py'},
            'Unknown E5 source inventory')
    for name, digest in frozen['source_sha256'].items():
        if pathlib.PurePosixPath(name).name == name:
            require(file_hash(source / name) == digest, 'Scientific E5 source differs from preregistration')
    e4_source = source.parent / 'experiment04'
    for name, digest in frozen['e4_binding']['source_sha256'].items():
        if pathlib.PurePosixPath(name).name == name:
            require(file_hash(e4_source / name) == digest, 'Scientific E4 reference differs from the bound study')
    # prepare.py imports only the pure, already-verified E4 cases module.
    spec = importlib.util.spec_from_file_location('audited_e5_prepare', source / 'prepare.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    e4 = module.e4
    definitions = {w['world_id']: w for w in e4.worlds()}
    prior_worlds = {w['world_id']: w for w in e4_data['worlds']}
    require(len(frozen['cases']) == 8 and {c['world_id'] for c in frozen['cases']} == set(definitions), 'E5 did not retain all eight E4 worlds')
    require(len(report['worlds']) == 8 and {w['world_id'] for w in report['worlds']} == set(definitions), 'E5 report world inventory differs')
    require(len({w['world_id'] for w in report['worlds']}) == 8, 'Duplicate E5 world report')
    require(type(report['completed']) is bool, 'Invalid completion flag')
    require(frozen['record_capacity'] == e4_data['protocol']['record_capacity']['canonical_json_characters'], 'Independent record capacity differs from carried-record capacity')
    require(frozen['monitor_schema'] == e4.MONITOR_SCHEMA, 'Unexpected monitor schema')
    expected_order, expected_orders = module.counterbalanced_orders(list(definitions))
    require([c['world_id'] for c in frozen['cases']] == expected_order, 'Frozen world order differs from fixed counterbalance')
    require(frozen['call_schedule'] == module.call_schedule(frozen['cases']), 'Frozen call schedule differs from candidate eligibility and order')
    require(32 <= len(frozen['call_schedule']) <= 56 and frozen['budget']['scheduled_calls'] == len(frozen['call_schedule']), 'Invalid fixed E5 schedule size')
    require([x['call_number'] for x in frozen['call_schedule']] == list(range(1, len(frozen['call_schedule']) + 1)), 'Nonsequential call schedule')
    require(all(x['role'] == 'independent_record' for x in frozen['call_schedule'][:8]), 'Reviews occur before all independent record commitments')
    case_manifest, public_worlds, runs = [], {}, {}
    for case in frozen['cases']:
        wid, world = case['world_id'], case['world']
        require(world == definitions[wid], 'E5 world differs from original immutable E4 source world')
        prior = prior_worlds[wid]
        prior_hidden = next(c for c in prior['conditions'] if c['condition'] == 'request_hidden')
        prior_record = prior['records']['request_hidden']
        require(case['carried_record'] == prior_record['record'] and case['carried_record_sha256'] == sha(prior_record['record']),
                'E5 carried record differs from the audited original actor input')
        require(case['natural_action'] == prior_hidden['action'] and case['natural_action_sha256'] == sha(prior_hidden['action']),
                'E5 fixed natural candidate differs from the audited E4 actor output')
        grade = e4.evaluate(world, case['natural_action'])
        require(grade == case['natural_grade'] == prior_hidden['grade'] and grade['valid'], 'Natural action grade differs from independent reference')
        expected_request = {'instructions': e4_data['protocol']['instructions']['record'],
                            'input': e4.record_packet(world, False), 'schema': world['record_schema']}
        require(case.get('independent_record_request_sha256') == sha(expected_request), 'Independent request scientific commitment differs')
        require(case['independent_record_request'] == expected_request,
                'Independent generator has different instructions, evidence, schema or query timing from the carried record')
        require(set(expected_request['input']) == {'immutable_policy', 'source_packets'}, 'Independent generator sees selected query or candidate metadata')
        expected_constructed = module.fault_copy(world, case['natural_action'])
        if expected_constructed['eligible']:
            expected_constructed['action_sha256'] = sha(expected_constructed['action'])
            require(e4.evaluate(world, expected_constructed['action']) == expected_constructed['grade'] and
                    expected_constructed['grade']['valid'] and expected_constructed['grade']['violation'],
                    'Constructed edit is not independently a valid policy violation')
        require(case['constructed'] == expected_constructed, 'Constructed candidate differs from the frozen deterministic fault rule')
        require(case['monitor_orders'] == expected_orders[wid], 'Candidate monitor order differs from fixed counterbalance')
        require(set(case) == {'world_id', 'family', 'world', 'independent_record_request', 'carried_record',
                             'carried_record_sha256', 'natural_action', 'natural_action_sha256', 'natural_grade',
                             'constructed', 'monitor_orders', 'independent_record_request_sha256'}, 'Unknown scientific case fields; manual review required')
        case_manifest.append(copy.deepcopy(case))
        candidates = {'natural': {'origin': 'actor_generated', 'action': case['natural_action'], 'grade': grade, 'monitors': {}}}
        if expected_constructed['eligible']:
            candidates['constructed'] = {k: copy.deepcopy(expected_constructed[k]) for k in
                                         ('origin', 'action', 'grade', 'edit', 'changed_fields')}
            candidates['constructed']['monitors'] = {}
        public_worlds[wid] = {'world_id': wid, 'family': case['family'], 'independent_record': None,
                              'independent_record_gate_failures': [], 'candidates': candidates}
        runs[wid] = {'trial_id': wid, 'decisions': []}
    case_by_id = {c['world_id']: c for c in frozen['cases']}
    monitor_inputs = {}
    for entry in frozen['call_schedule']:
        wid = entry['world_id']
        case, row = case_by_id[wid], public_worlds[wid]
        folder = report_path.parent / wid
        if entry['role'] == 'independent_record':
            name = 'independent_record.json'
            path = folder / name
            if not path.exists():
                continue
            request = case['independent_record_request']
            d = response(path, request['input'], request['schema'], entry['call_number'], e4)
            runs[wid]['decisions'].append(d)
            errors = list(d['schema_errors'])
            if d['status'] != 'completed':
                errors.append('Independent record response did not complete')
            if not d['schema_errors']:
                record = d['parsed']
                if len(compact(record)) > frozen['record_capacity']:
                    errors.append('Independent record exceeded fixed capacity')
                public_record = {'record': record, 'sha256': sha(record), 'canonical_characters': len(compact(record)),
                                 'extraction_score': e4.extraction_score(case['world'], record)}
                row['independent_record'] = public_record
                commit_path = folder / 'committed_independent_record.json'
                if commit_path.exists():
                    require(not errors and read(commit_path) == public_record, 'Independent committed record differs from its emitted public response')
                    row['independent_record_commit_verified'] = True
            row['independent_record_gate_failures'] = errors
            continue
        require(entry['role'] == 'monitor' and entry['cohort'] in row['candidates'] and entry['view'] in VIEWS,
                'Unknown frozen review schedule entry')
        cohort, view = entry['cohort'], entry['view']
        path = folder / ('monitor_' + cohort + '_' + view + '.json')
        if not path.exists():
            continue
        require(all(w.get('independent_record_commit_verified') for w in public_worlds.values()), 'Monitor precedes a verified independent record commitment')
        candidate = row['candidates'][cohort]
        artifact = {'none': None, 'carried': case['carried_record'], 'independent': row['independent_record']['record']}[view]
        packet = module.monitor_packet(case['world'], candidate['action'], artifact)
        require(set(packet) == {'query', 'original_evidence', 'candidate_action', 'public_evidence'}, 'Review packet contains origin or experimental labels')
        d = response(path, packet, frozen['monitor_schema'], entry['call_number'], e4)
        runs[wid]['decisions'].append(d)
        monitor_inputs[(wid, cohort, view)] = packet
        valid = module.valid_review(d['parsed'])
        candidate.setdefault('monitor_validation_errors', {})[view] = [] if valid else ['Invalid monitor score, flag, schema or evidence length']
        if valid:
            candidate['monitors'][view] = d['parsed']
    for wid, row in public_worlds.items():
        case = case_by_id[wid]
        independent = row['independent_record']['record'] if row['independent_record'] is not None else None
        row['record_comparison'] = compare_records(e4, case['world'], case['carried_record'], independent)
        for cohort, candidate in row['candidates'].items():
            packets = {v: monitor_inputs[(wid, cohort, v)] for v in VIEWS if (wid, cohort, v) in monitor_inputs}
            if len(packets) == 3:
                stripped = []
                for packet in packets.values():
                    p = copy.deepcopy(packet)
                    p.pop('public_evidence')
                    stripped.append(p)
                require(stripped[0] == stripped[1] == stripped[2], 'Review views differ by more than neutral public evidence content')
                candidate['matched_packets_verified'] = True
            if 'carried' in packets and 'independent' in packets:
                same_input = compact(packets['carried']) == compact(packets['independent'])
                require(same_input == row['record_comparison']['canonical_equal_array_order_retained'],
                        'Canonical artifact equality differs from complete monitor-input equality')
                candidate['carried_independent_same_input_repeat'] = same_input
                if 'carried' in candidate['monitors'] and 'independent' in candidate['monitors']:
                    a, b = candidate['monitors']['carried'], candidate['monitors']['independent']
                    candidate['carried_independent_flag_disagreement'] = a['flag'] != b['flag']
                    candidate['carried_independent_response_canonical_equal'] = compact(a) == compact(b)
        raw = next(w for w in report['worlds'] if w['world_id'] == wid)
        require(raw['family'] == row['family'] and set(raw['candidates']) == set(row['candidates']), 'Reported cohort population differs')
        if raw['independent_record'] is not None:
            require(raw['independent_record'] == row['independent_record'] and row.get('independent_record_commit_verified'),
                    'Reported independent commitment differs from saved public record')
        for cohort, raw_candidate in raw['candidates'].items():
            for key in ('origin', 'action', 'grade', 'monitors'):
                require(raw_candidate[key] == row['candidates'][cohort][key], 'Reported candidate or monitor differs from independent reconstruction')
            if cohort == 'constructed':
                for key in ('edit', 'changed_fields'):
                    require(raw_candidate[key] == row['candidates'][cohort][key], 'Reported constructed mutation differs')
        folder = report_path.parent / wid
        if folder.exists():
            actual = {p.name for p in folder.glob('*.json') if
                      (p.name == 'independent_record.json' or p.name.startswith('monitor_')) and not p.name.endswith('.request.json')}
            require(actual == {d['filename'] for d in runs[wid]['decisions']}, 'Unregistered responses; no selective omission allowed')
    decisions = sorted((d for run in runs.values() for d in run['decisions']), key=lambda d: d['call_number'])
    require([d['call_number'] for d in decisions] == list(range(1, len(decisions) + 1)), 'Missing or reordered saved responses')
    session_count = audit_private_sessions([report_path.parent / run['trial_id'] / d['filename']
                                            for run in runs.values() for d in run['decisions']])
    started = report.get('calls_started', len(decisions))
    require(type(started) is int and len(decisions) <= started <= len(frozen['call_schedule']), 'Invalid attempted-call count')
    if report['completed']:
        require(len(decisions) == len(frozen['call_schedule']) and all(d['status'] == 'completed' for d in decisions), 'Completed E5 run lacks its scheduled completed responses')
    public_rows = list(public_worlds.values())
    summary = module.summarize({'worlds': public_rows})
    if 'summary' in report:
        require(report['summary'] == summary, 'Reported summary differs from independently reconstructed labels and reviews')
    keys = ('experiment', 'purpose', 'record_capacity', 'monitor_instructions', 'monitor_schema',
            'randomization', 'call_schedule', 'failure_policy', 'analysis', 'limitations')
    require(set(frozen) == set(keys) | {'budget', 'e4_binding', 'cases', 'source_sha256'}, 'Unknown E5 protocol fields; manual review required')
    protocol = {key: copy.deepcopy(frozen[key]) for key in keys}
    protocol['budget'] = {key: frozen['budget'][key] for key in
                          ('total_calls_max', 'scheduled_calls', 'independent_records', 'natural_reviews', 'constructed_reviews', 'model', 'effort')}
    protocol['source_sha256'] = {pathlib.PurePosixPath(k).name: v for k, v in frozen['source_sha256'].items()}
    protocol['e4_binding'] = {'experiment': frozen['e4_binding']['experiment'], 'plan_sha256': frozen['e4_binding']['plan_sha256'],
                            'public_dataset_sha256': file_hash(e4_data_path),
                            'source_sha256': {pathlib.PurePosixPath(k).name: v for k, v in frozen['e4_binding']['source_sha256'].items()}}
    publication = read(source / 'publication.json')
    require(re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?', publication['repository']), 'Unexpected public repository URL')
    require(re.fullmatch(r'[0-9a-f]{40}', publication['preregistration_commit']), 'Invalid preregistration commit')
    require(publication['canonical_plan_sha256'] == report['plan_sha256'], 'Public preregistration hash differs')
    data = {'experiment_id': 'experiment-05', 'title': 'Carried versus independently generated public evidence',
            'scope': 'Fixed E4 hidden-request candidates; natural and constructed cohorts analyzed separately',
            'protocol_canonical_sha256': report['plan_sha256'],
            'protocol_hash_scope': 'Original canonical frozen plan. Scientific protocol and cases follow; generic runtime guard prose and source-directory prefixes are omitted, and the audited public E4 dataset hash is added.',
            'protocol': protocol, 'case_manifest': case_manifest, 'completed': report['completed'],
            'stop_status': 'completed' if report['completed'] else 'stopped_or_incomplete',
            'counts': {'planned_calls': len(frozen['call_schedule']), 'calls_started': started, 'saved_responses': len(decisions),
                       'saved_independent_record_responses': sum(d['filename'] == 'independent_record.json' for d in decisions),
                       'saved_natural_reviews': sum(d['filename'].startswith('monitor_natural_') for d in decisions),
                       'saved_constructed_reviews': sum(d['filename'].startswith('monitor_constructed_') for d in decisions)},
            'worlds': public_rows, 'runs': list(runs.values()), 'summary': summary,
            'record_comparison_counts': {
                'worlds_with_comparable_records': sum(w['record_comparison']['comparison_available'] for w in public_rows),
                'canonical_identical_worlds': sum(w['record_comparison']['canonical_equal_array_order_retained'] is True for w in public_rows),
                'semantic_identical_worlds': sum(w['record_comparison']['source_facts_equal_array_order_ignored'] is True for w in public_rows),
                'same_input_review_pairs': sum(c.get('carried_independent_same_input_repeat') is True for w in public_rows for c in w['candidates'].values())},
            'token_totals': {key: sum((d['usage'] or {}).get(key, 0) for d in decisions) for key in USAGE_KEYS},
            'latency': {'median_seconds': statistics.median(d['elapsed_seconds'] for d in decisions) if decisions else None,
                        'total_seconds': round(sum(d['elapsed_seconds'] for d in decisions), 3)},
            'publication': {key: publication[key] for key in ('repository', 'preregistration_commit', 'canonical_plan_sha256')},
            'audit': {'bound_to_audited_public_e4_data': True, 'action_grades_independently_recomputed': True,
                      'constructed_edits_checked': True, 'record_commitments_and_query_blinding_checked': True,
                      'neutral_artifact_only_packet_difference_checked': True, 'factual_record_errors_filtered': False,
                      'distinct_application_sessions_verified': session_count},
            'privacy_note': 'Public supplied packets, responses, scientific grades, tokens and latencies only. No private reasoning, account state, session identifiers or exception text.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    scan = scan_paths([output])
    require(scan['status'] == 'pass' and not scan['binary_files_require_visual_review'], 'Public release safety scan failed; do not publish')
    return {'status': 'ready', 'completed': report['completed'], 'saved_responses': len(decisions), 'privacy_findings': len(scan['findings']), 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=pathlib.Path)
    parser.add_argument('--source', required=True, type=pathlib.Path)
    parser.add_argument('--e4-data', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(export(args.report, args.source, args.e4_data, args.output)))


if __name__ == '__main__':
    main()
