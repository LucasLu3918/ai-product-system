"""Guarded personal Git publication and optional external Ed25519 grants.

The administrator trust-root file selects high-assurance publication. Its absence
selects the explicitly lower-isolation personal workflow.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import yaml

CONFIG = Path('/etc/aips/publication-authority.yaml')
PUBLICATION_OPERATIONS = {'git_push', 'git_tag', 'gh_pr_create', 'gh_pr_merge', 'gh_release_create'}
PERSONAL_PUBLICATION_OPERATIONS = {'git_push', 'gh_pr_create'}
PERSONAL_BRANCH_PREFIXES = ('agent/', 'bugfix/', 'chore/', 'claude/', 'codex/', 'docs/', 'feature/', 'fix/', 'gemini/', 'work/')


class PublicationError(ValueError):
    pass


def publication_mode(config_path: Path | None = None) -> str:
    """Select personal mode only when the fixed administrator trust root is absent."""
    config_path = config_path or CONFIG
    try:
        info = config_path.lstat()
    except FileNotFoundError:
        return 'personal'
    except OSError as exc:
        raise PublicationError('publication mode configuration unavailable') from exc
    if not stat.S_ISREG(info.st_mode):
        raise PublicationError('publication mode configuration must be a regular file')
    return 'high_assurance'


def _personal_base(root: Path, operation: str, argv: list[str]) -> str:
    """Resolve a locally available exact merge base for personal-mode scope checks."""
    remote = 'origin'
    urls = git(root, 'remote', 'get-url', '--all', remote).splitlines()
    push_urls = git(root, 'remote', 'get-url', '--push', '--all', remote).splitlines()
    if len(urls) != 1 or len(push_urls) != 1 or urls[0] != push_urls[0]:
        raise PublicationError('personal publication requires one matching origin fetch and push URL')
    response = subprocess.run(['git', 'ls-remote', '--symref', '--', urls[0], 'HEAD'],
                              cwd=root, capture_output=True, text=True, timeout=15, check=False)
    match = re.search(r'^ref: refs/heads/([A-Za-z0-9_./-]+)\tHEAD$', response.stdout, re.MULTILINE)
    if response.returncode or not match:
        raise PublicationError('remote default branch unavailable')
    default_branch = match.group(1)
    default_tip = _tip(root, urls[0], 'refs/heads/' + default_branch)
    if not default_tip or not re.fullmatch(r'[0-9a-f]{40,64}', default_tip):
        raise PublicationError('remote default branch tip unavailable')
    if operation == 'gh_pr_create' and _option(argv, '--base') != default_branch:
        raise PublicationError('personal PRs must target the remote default branch')
    try:
        git(root, 'cat-file', '-e', default_tip + '^{commit}')
    except PublicationError as exc:
        raise PublicationError('fetch the current remote default branch before personal publication') from exc
    return default_tip


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(value: Any) -> str:
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def run(cwd: Path, *argv: str) -> str:
    proc = subprocess.run(list(argv), cwd=cwd, capture_output=True, text=True, timeout=15, check=False)
    if proc.returncode:
        raise PublicationError('required repository observation failed')
    return proc.stdout.strip()


def git(cwd: Path, *argv: str) -> str:
    return run(cwd, 'git', *argv)


def identity(cwd: Path) -> dict[str, str]:
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    if any(os.environ.get(key) for key in ['GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS']):
        raise PublicationError('alternate Git environment unsupported')
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    directory = Path(git(root, 'rev-parse', '--absolute-git-dir')).resolve()
    return {'repository_id': digest(str(common)), 'worktree_id': digest(str(directory))}


def approval_location(cwd: Path) -> Path | None:
    """Search overrides relative to worktree root, then worktree-scoped common storage."""
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    override = os.environ.get('AIPS_APPROVAL_RECORD')
    if override:
        path = Path(override).expanduser()
        return path if path.is_absolute() else root / path
    state = root / '.ai/STATE.yaml'
    if state.exists():
        doc = yaml.safe_load(state.read_text()) or {}
        pointer = (doc.get('governance') or {}).get('active_approval')
        if pointer:
            path = Path(pointer)
            return path if path.is_absolute() else root / path
    local = root / '.ai/approvals/ACTIVE.yaml'
    if local.exists():
        return local
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    scoped = common / 'aips/approvals' / identity(root)['worktree_id'].split(':')[1] / 'ACTIVE.yaml'
    return scoped if scoped.exists() else None


def _ref(cwd: Path, value: str) -> str:
    if not value.startswith(('refs/heads/', 'refs/tags/')):
        raise PublicationError('explicit full target ref required')
    git(cwd, 'check-ref-format', value)
    return value


def _tip(cwd: Path, remote: str, ref: str) -> str | None:
    lines = git(cwd, 'ls-remote', '--refs', '--', remote, ref).splitlines()
    matches = [line.split('\t')[0] for line in lines if line.endswith('\t' + ref)]
    if len(matches) > 1:
        raise PublicationError('ambiguous remote ref')
    return matches[0] if matches else None


def _option(argv: list[str], option: str) -> str:
    if argv.count(option) != 1:
        raise PublicationError('explicit unique ' + option + ' required')
    index = argv.index(option)
    if index + 1 >= len(argv) or argv[index + 1].startswith('-'):
        raise PublicationError('missing ' + option + ' value')
    return argv[index + 1]


def action(cwd: Path, operation: str, argv: list[str], base: str, *, personal: bool = False) -> dict[str, Any]:
    """Observe a supported standalone literal command; implicit/multi-target pushes deny."""
    if operation not in PUBLICATION_OPERATIONS or not argv or any('$' in word or '`' in word or '\0' in word for word in argv):
        raise PublicationError('literal publication command required')
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    head = git(root, 'rev-parse', 'HEAD^{commit}')
    if not re.fullmatch(r'[0-9a-f]{40,64}', base):
        raise PublicationError('explicit base commit SHA required')
    git(root, 'merge-base', '--is-ancestor', base, head)
    if git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise PublicationError('publication requires a clean worktree')
    diff = subprocess.run(['git', 'diff', '--binary', base, head, '--'], cwd=root, capture_output=True, timeout=15, check=False)
    files = subprocess.run(['git', 'diff', '--name-only', '-z', base, head, '--'], cwd=root, capture_output=True, timeout=15, check=False)
    if diff.returncode or files.returncode:
        raise PublicationError('candidate diff unavailable')
    result: dict[str, Any] = {
        **identity(root), 'branch': git(root, 'branch', '--show-current'),
        'candidate_commit': head, 'base_commit': base,
        'files': sorted(os.fsdecode(item) for item in files.stdout.split(b'\0') if item),
        'diff_digest': 'sha256:' + hashlib.sha256(diff.stdout).hexdigest(),
        'operations': [operation], 'argv': argv,
    }
    if not result['branch']:
        raise PublicationError('publication requires an explicit feature branch')
    remote = 'origin'
    force = False
    delete = False
    if operation == 'git_push':
        if argv[:2] != ['git', 'push']:
            raise PublicationError('use a standalone git push without wrappers/global options')
        args = argv[2:]
        flags = []
        while args and args[0].startswith('-'):
            flag, args = args[0], args[1:]
            if flag not in {'--force', '-f', '--delete'} and not flag.startswith('--force-with-lease='):
                raise PublicationError('unsupported push option')
            flags.append(flag)
        if len(args) != 2 or not re.fullmatch(r'[A-Za-z0-9_.-]+', args[0]):
            raise PublicationError('one named remote and one explicit refspec required')
        remote, spec = args
        if personal:
            fetch_urls = git(root, 'remote', 'get-url', '--all', 'origin').splitlines()
            push_urls = git(root, 'remote', 'get-url', '--push', '--all', 'origin').splitlines()
            if remote != 'origin' or len(fetch_urls) != 1 or len(push_urls) != 1 or fetch_urls[0] != push_urls[0]:
                raise PublicationError('personal mode permits only the verified single origin remote')
        delete = '--delete' in flags or spec.startswith(':')
        if '--delete' in flags:
            source, target = None, _ref(root, spec)
        else:
            if spec.count(':') != 1:
                raise PublicationError('explicit source SHA:full-ref required')
            source, target = spec.split(':')
            target = _ref(root, target)
            if source and source != head:
                raise PublicationError('push source must be exact current candidate SHA')
            source = source or None
        force = any(flag in {'-f', '--force'} or flag.startswith('--force-with-lease=') for flag in flags)
        result.update(source_commit=source, refspec=spec)
        if personal:
            branch = result['branch']
            if (delete or target != 'refs/heads/' + branch or
                    branch in {'main', 'master', 'trunk', 'develop', 'production', 'release'} or
                    not branch.startswith(PERSONAL_BRANCH_PREFIXES)):
                raise PublicationError('personal mode permits only the current engineering branch')
        for key in ['push.followTags', 'remote.' + remote + '.mirror']:
            proc = subprocess.run(['git', 'config', '--bool', '--get', key], cwd=root, capture_output=True, text=True, timeout=5, check=False)
            if proc.returncode not in {0, 1} or proc.stdout.strip() == 'true':
                raise PublicationError('implicit multi-ref publication configuration forbidden')
    elif operation == 'git_tag':
        # Local mutations still require exact authorization; read-only forms are classified elsewhere.
        if argv[:2] != ['git', 'tag'] or len(argv) != 3 or argv[2].startswith('-'):
            raise PublicationError('supported tag mutation is git tag <name>; other forms require separate review')
        target = _ref(root, 'refs/tags/' + argv[2])
        result['local_tag_oid'] = git(root, 'tag', '--list', argv[2]) or None
    else:
        if os.environ.get('GH_HOST', 'github.com') != 'github.com':
            raise PublicationError('unsupported GitHub host')
        expected = {'gh_pr_create': ['gh', 'pr', 'create'], 'gh_pr_merge': ['gh', 'pr', 'merge'],
                    'gh_release_create': ['gh', 'release', 'create']}[operation]
        if argv[:3] != expected:
            raise PublicationError('use standalone gh command with explicit --repo')
        # A second spelling such as -R/--repo= or -B may override inspected fields.
        valued = {'--repo', '--body', '--body-file'}
        switches = set()
        position = 3
        if operation == 'gh_pr_create':
            _option(argv, '--title')
            if ('--body' in argv) == ('--body-file' in argv):
                raise PublicationError('exactly one explicit PR body or body file required')
            valued |= {'--head', '--base', '--title', '--label', '--assignee', '--reviewer', '--milestone', '--project'}
            switches = {'--draft'}
        elif operation == 'gh_pr_merge':
            valued |= {'--match-head-commit', '--subject'}
            switches = {'--merge', '--squash', '--rebase'}
            position = 4
            if sum(flag in argv for flag in switches) != 1:
                raise PublicationError('exactly one explicit merge method required')
        else:
            valued = {'--repo', '--title', '--notes', '--notes-file'}
            switches = {'--verify-tag', '--draft', '--prerelease'}
            position = 4
            if '--verify-tag' not in argv:
                raise PublicationError('release creation requires an existing verified remote tag')
        while position < len(argv):
            flag = argv[position]
            if flag in valued:
                if position + 1 >= len(argv) or argv[position + 1].startswith('-'):
                    raise PublicationError('missing explicit option value')
                position += 2
            elif flag in switches:
                position += 1
            else:
                raise PublicationError('unsupported or ambiguous GitHub publication option')
        repo = _option(argv, '--repo')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise PublicationError('explicit GitHub owner/repository required')
        url = git(root, 'remote', 'get-url', '--push', remote)
        ssh_prefix = 'git' + '@' + 'github.com:'
        if url.removesuffix('.git') not in {'https://github.com/' + repo, ssh_prefix + repo}:
            raise PublicationError('gh repository does not match Git remote')
        result['github_repo'] = repo
        if operation == 'gh_pr_create':
            if (_option(argv, '--head') != result['branch'] or
                    personal and not result['branch'].startswith(PERSONAL_BRANCH_PREFIXES)):
                raise PublicationError('PR head must be the bound candidate branch')
            target = _ref(root, 'refs/heads/' + _option(argv, '--base'))
            if _tip(root, remote, 'refs/heads/' + result['branch']) != head:
                raise PublicationError('remote PR head differs from candidate')
        elif operation == 'gh_pr_merge':
            if len(argv) < 4 or not argv[3].isdigit() or any(flag in argv for flag in ['--auto', '--admin', '--delete-branch']):
                raise PublicationError('explicit PR number and immediate checked merge required')
            if _option(argv, '--match-head-commit') != head:
                raise PublicationError('merge must pin the exact candidate SHA')
            pr = json.loads(run(root, 'gh', 'pr', 'view', argv[3], '--repo', repo, '--json', 'headRefOid,baseRefOid,baseRefName'))
            if pr['headRefOid'] != head:
                raise PublicationError('PR head differs from candidate')
            result['pr_base_commit'] = pr['baseRefOid']
            target = _ref(root, 'refs/heads/' + pr['baseRefName'])
        else:
            if len(argv) < 4 or argv[3].startswith('-'):
                raise PublicationError('explicit release tag required')
            target = _ref(root, 'refs/tags/' + argv[3])
            if git(root, 'rev-parse', target + '^{commit}') != head:
                raise PublicationError('release tag must point to the exact candidate commit')
            result['tag_oid'] = git(root, 'rev-parse', target)
        inputs = {}
        for opt in ['--body-file', '--notes-file']:
            if opt in argv:
                path = Path(_option(argv, opt))
                if str(path) == '-':
                    raise PublicationError('stdin publication text cannot be bound')
                path = (path if path.is_absolute() else cwd / path).resolve(strict=True)
                inputs[opt] = {'path': str(path), 'digest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}
        result['file_inputs'] = inputs
    url = git(root, 'remote', 'get-url', '--push', remote)
    # Several push URLs cause several publications, which this single-target contract rejects.
    if len(git(root, 'remote', 'get-url', '--push', '--all', remote).splitlines()) != 1:
        raise PublicationError('exactly one push URL required')
    parsed = urlparse(url)
    if parsed.password or (parsed.scheme in {'http', 'https'} and parsed.username):
        raise PublicationError('credential-bearing remote URL forbidden')
    result.update(remote=remote, remote_url=url, target_ref=target,
                  expected_remote_oid=_tip(root, url, target), force=force, delete=delete)
    result['remote_state_enforcement'] = 'server_lease' if operation == 'git_push' else 'preexecution_observation'
    if operation == 'git_push':
        expected_lease = '--force-with-lease=' + target + ':' + (result['expected_remote_oid'] or '')
        allowed_flags = ([], [expected_lease]) if personal else ([expected_lease], [expected_lease, '--delete'])
        if flags not in allowed_flags:
            raise PublicationError('one explicit target/tip force-with-lease required; unconditional force forbidden')
    if operation == 'gh_pr_merge' and result['pr_base_commit'] != result['expected_remote_oid']:
        raise PublicationError('PR base differs from current remote tip')
    if operation == 'gh_release_create' and result['tag_oid'] != result['expected_remote_oid']:
        raise PublicationError('local and remote release tag differ')
    return result


def validate_personal_action(cwd: Path, operation: str, argv: list[str]) -> dict[str, Any]:
    """Validate a single ordinary engineering publication without minting approval data."""
    if operation not in PERSONAL_PUBLICATION_OPERATIONS:
        raise PublicationError('operation is unavailable in personal publication mode')
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    base = _personal_base(root, operation, argv)
    from check_secret_leakage import DEFAULT_POLICY, load_policy, scan_candidate
    policy, _ = load_policy(DEFAULT_POLICY)
    findings, blockers, _, _ = scan_candidate(root, base, 'HEAD', policy)
    if findings or blockers:
        raise PublicationError('mandatory candidate and history secret scan blocked publication')
    return action(root, operation, argv, base, personal=True)


def proposal(cwd: Path, operation: str, argv: list[str], base: str) -> dict[str, Any]:
    scope = action(cwd, operation, argv, base)
    return {'version': 2, 'approval': {'status': 'PENDING'}, 'scope': scope,
            'proposal': {'fingerprint': digest(scope)},
            'evidence': {'validation': [], 'unresolved': []}}


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise PublicationError('UTC timestamp required')
    try:
        date = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PublicationError('invalid UTC timestamp') from exc
    if date.tzinfo is None or date.utcoffset().total_seconds() != 0:
        raise PublicationError('UTC timestamp required')
    return date


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublicationError('authority redirects are forbidden')


class Authority:
    def __init__(self, config: dict[str, Any]):
        if config.get('version') != 1:
            raise PublicationError('invalid authority configuration')
        self.config = config
        parsed = urlparse(config.get('endpoint', ''))
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise PublicationError('authority requires a credential-free HTTPS endpoint')
        self.issuers = config.get('issuers') or {}
        if not isinstance(self.issuers, dict) or not self.issuers:
            raise PublicationError('trusted issuer keys required')

    def verify_signature(self, doc: dict[str, Any]) -> None:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        try:
            signature = doc['signature']
            if signature['algorithm'] != 'ed25519':
                raise PublicationError('unsupported signature algorithm')
            public = base64.b64decode(self.issuers[signature['issuer_key_id']], validate=True)
            raw = base64.b64decode(signature['value_b64'], validate=True)
            message = {key: value for key, value in doc.items() if key != 'signature'}
            Ed25519PublicKey.from_public_bytes(public).verify(raw, canonical(message))
        except (KeyError, ValueError, TypeError, InvalidSignature) as exc:
            raise PublicationError('untrusted or invalid publication signature') from exc

    def check(self, record: dict[str, Any], consume: bool) -> None:
        nonce = uuid.uuid4().hex
        request = {'version': 1, 'nonce': nonce, 'record': record,
                   'record_digest': digest(record), 'action_digest': digest(record['scope'])}
        url = self.config['endpoint'].rstrip('/') + ('/consume' if consume else '/status')
        data = canonical(request)
        req = Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        # Proxy environment is not an authorization root; TLS and signature remain mandatory.
        with build_opener(_NoRedirect()).open(req, timeout=10) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise PublicationError('oversized authority response')
        assertion = json.loads(raw)
        self.verify_signature(assertion)
        expected = {'version': 1, 'nonce': nonce, 'grant_id': record['approval']['id'],
                    'record_digest': request['record_digest'], 'action_digest': request['action_digest'],
                    'result': 'CONSUMED' if consume else 'AVAILABLE'}
        if any(assertion.get(key) != value for key, value in expected.items()):
            raise PublicationError('authority denied, stale or replayed grant')
        expires = _timestamp(assertion.get('expires_at'))
        now = datetime.now(UTC)
        if not 0 < (expires - now).total_seconds() <= 60:
            raise PublicationError('authority assertion expired or exceeds 60 seconds')


def protected_file(value: Path) -> Path:
    path = value.resolve(strict=True)
    for item in [path, *path.parents]:
        info = item.stat()
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
            raise PublicationError('authority configuration must be administrator-owned and not Agent-writable')
    return path


def configured_authority() -> Authority:
    # Fixed administrator-owned path; an Agent-owned external YAML is not a trust root.
    path = protected_file(CONFIG)
    if any(os.access(item, os.W_OK) for item in [path, *path.parents]):
        raise PublicationError('authority config/path is writable by this Agent, including ACL or privileged access')
    return Authority(yaml.safe_load(path.read_text()))


def verify(record: dict[str, Any], operation: str, cwd: Path, argv: list[str] | None,
           *, consume: bool = False, authority: Authority | None = None) -> None:
    if record.get('version') != 2 or operation not in PUBLICATION_OPERATIONS:
        raise PublicationError('signed v2 publication grant required; reissue legacy approvals')
    authority = authority or configured_authority()
    authority.verify_signature(record)
    approval = record.get('approval') or {}
    scope = record.get('scope') or {}
    if approval.get('status') != 'APPROVED' or not all(approval.get(key) for key in ['id', 'approved_by', 'approved_at', 'expires_at']):
        raise PublicationError('complete Human-issued approval required')
    now = datetime.now(UTC)
    issued, expires = _timestamp(approval['approved_at']), _timestamp(approval['expires_at'])
    if issued > now or expires <= now or not 0 < (expires - issued).total_seconds() <= 3600:
        raise PublicationError('approval expired, future-dated or exceeds one hour')
    if record.get('proposal', {}).get('fingerprint') != digest(scope):
        raise PublicationError('proposal scope fingerprint mismatch')
    if (record.get('evidence') or {}).get('unresolved'):
        raise PublicationError('unresolved publication evidence')
    if not (record.get('evidence') or {}).get('validation'):
        raise PublicationError('publication validation evidence required')
    if not argv:
        raise PublicationError('actual command required; stored command cannot supply execution scope')
    actual = action(cwd, operation, argv, scope.get('base_commit', ''))
    if actual != scope:
        raise PublicationError('actual publication action differs from approved scope')
    authority.check(record, consume)
