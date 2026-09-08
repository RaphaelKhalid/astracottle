"""Offline release scan. Reports categories and relative filenames, never matches.

Examples:
  python public_safety_check.py release-data
  python public_safety_check.py --git-index path/to/repository path/to/static-output
This is a defense in addition to allowlisted export and human review.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

PRIVATE_KEYS = {
    'closing_account_usage', 'quota_before', 'quota_after', 'quota_start', 'quota_end',
    'weekly_used_percent', 'usedPercent', 'windowDurationMins', 'resetsAt',
    'task_start_percent', 'experiment_first_percent', 'experiment_last_percent',
    'thread_id', 'threadId', 'turn_id', 'turnId', 'clientThreadId', 'hostId',
    'account_id', 'accountId', 'auth_type', 'auth', 'authorization', 'access_token',
    'refresh_token', 'id_token', 'api_key', 'apiKey', 'OPENAI_API_KEY',
    'modelProvider', 'instructionSources', 'transport_config', 'config_summary',
    'cwd', 'username', 'email', 'run_name', 'starts', 'event_counts',
    'encrypted_content', 'reasoning_text', 'raw_reasoning', 'reasoning_content',
}
PRIVATE_FILENAMES = {
    'auth.json', 'account_close.json', 'transport_config.json', 'quota_start.json',
    'quota_end.json', 'pilot-source.zip', 'pilot-data.json', 'pilot-report.md',
    'automation.toml', '.env', '.env.local', '.env.production',
}
PATTERNS = {
    'absolute local home path': re.compile(r'(?i)(?:[A-Z]:[\\/]+(?:Users|Documents and Settings)[\\/]|/(?:Users|home)/[^/\s]+/)'),
    'session-style UUID': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I),
    'API credential': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
    'GitHub credential': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'private key': re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
    'bearer credential': re.compile(r'(?i)\bbearer\s+[A-Za-z0-9_./+=-]{24,}'),
    'JWT credential': re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b'),
}
EMAIL = re.compile(r'\b[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def key_findings(value, prefix='$'):
    findings = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PRIVATE_KEYS:
                findings.append({'category': 'private JSON field', 'location': prefix + '.' + key})
            findings.extend(key_findings(child, prefix + '.' + key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(key_findings(child, f'{prefix}[{index}]'))
    return findings


def scan_text(text, is_json=False, local_identifiers=()):
    found = []
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            found.append({'category': name})
    if any(not item.lower().endswith('@users.noreply.github.com') for item in EMAIL.findall(text)):
        found.append({'category': 'email address other than public GitHub noreply'})
    for identifier in local_identifiers:
        if len(identifier) >= 4 and re.search(r'(?<![A-Za-z0-9])' + re.escape(identifier) + r'(?![A-Za-z0-9])', text, re.I):
            found.append({'category': 'known local identity'})
            break
    if is_json:
        try:
            found.extend(key_findings(json.loads(text)))
        except ValueError:
            found.append({'category': 'invalid JSON'})
    return found


def candidates(root, git_index=False):
    if git_index:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                                check=True, capture_output=True)
        return [root / x for x in result.stdout.decode('utf-8').split('\0') if x]
    if root.is_file():
        return [root]
    return [p for p in root.rglob('*') if p.is_file()
            and not any(part in {'.git', 'node_modules', '__pycache__', '.next'}
                        for part in p.relative_to(root).parts)]


def scan_paths(roots, git_index_root=None):
    identifiers = {os.environ.get('USERNAME', ''), pathlib.Path.home().name}
    # Generic hosted-CI account names are not personal identities; path and credential scans still apply.
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        identifiers -= {'runner', 'runneradmin'}
    findings, binaries, count = [], [], 0
    targets = [(root, False) for root in roots]
    if git_index_root is not None:
        targets.insert(0, (git_index_root, True))
    for root, indexed in targets:
        for path in candidates(root, indexed):
            label = path.name if root.is_file() else path.relative_to(root).as_posix()
            count += 1
            parts = pathlib.PurePosixPath(label).parts
            if (path.name in PRIVATE_FILENAMES or path.suffix.lower() in {'.zip', '.sqlite', '.db', '.jsonl'}
                    or any(part in {'.codex', '.vercel', 'runs', 'controls'} for part in parts)):
                findings.append({'file': label, 'category': 'private runtime or archive candidate'})
            try:
                if indexed:
                    # Scan the actual staged blob, not a potentially different
                    # working-tree file with the same name.
                    staged = subprocess.run(['git', '-C', str(root), 'show', ':' + label],
                                            check=True, capture_output=True)
                    text = staged.stdout.decode('utf-8')
                else:
                    text = (subprocess.run(['git', '-C', str(root), 'show', ':' + label], check=True, capture_output=True).stdout.decode('utf-8') if indexed else path.read_text(encoding='utf-8'))
            except UnicodeDecodeError:
                binaries.append(label)
                continue
            for finding in scan_text(text, path.suffix.lower() == '.json', identifiers):
                findings.append({'file': label, **finding})
    return {'status': 'pass' if not findings and not binaries else 'fail', 'files_scanned': count,
            'findings': findings, 'binary_files_require_visual_review': binaries,
            'scope': 'Allowlisted text release scan; not a proof that arbitrary media is non-private.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', type=pathlib.Path)
    parser.add_argument('--git-index', type=pathlib.Path)
    parser.add_argument('--report', type=pathlib.Path)
    args = parser.parse_args()
    if not args.paths and args.git_index is None:
        parser.error('Supply a directory/file or --git-index repository.')
    result = scan_paths(args.paths, args.git_index)
    serialized = json.dumps(result, indent=2)
    if args.report:
        args.report.write_text(serialized + '\n', encoding='utf-8')
    print(serialized)
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
