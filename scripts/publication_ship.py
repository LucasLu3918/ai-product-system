"""`aips publish ship`: one exact-candidate scan, then the exact push, then PR create.

Hook contract (personal mode): the agent-facing Hook sees exactly one Bash command, `aips publish ship ...`,
and classifies it as one protected operation (`publish_ship`). Its validation runs the same observations as
the individual operations and performs the single candidate scan, which it records as push-bound evidence.

Child contract: `git push` and `gh pr create` run inside this CLI process, not through the agent's Bash tool,
so the Hook never sees them and the one-protected-operation-per-invocation rule still applies to the agent.
Each child is re-validated against the same exact candidate, scan evidence and body digest immediately before
it runs; a changed candidate, remote tip or body stops the chain before the child executes.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import publication_authority as authority
import publication_planning as planning
import publication_scan_evidence as evidence
from publication_authority import PublicationError

OPERATION = 'publish_ship'
VALUE_FLAGS = ('--title', '--body-file', '--base', '--head')
REQUIRED_FLAGS = ('--title', '--body-file', '--base')
BRANCH_RE = re.compile(r'[A-Za-z0-9._/-]+')
PR_URL_RE = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+')
CHILD_TIMEOUT_SECONDS = 120


def _form(message: str, reason: str = 'COMMAND_FORM_UNSUPPORTED', phase: str = 'command_validation') -> PublicationError:
    return PublicationError(message, reason, detail_code='SHIP_FORM_UNSUPPORTED', phase=phase)


def parse_tokens(tokens: list[str]) -> dict[str, str | None]:
    """Strict literal parser shared by the Hook and the CLI: one value per flag, no other forms."""
    if any('\0' in token or '$' in token or '`' in token for token in tokens):
        raise PublicationError('ship arguments must be literal', 'COMMAND_FORM_UNSUPPORTED',
                               detail_code='PUBLICATION_ARGUMENT_DYNAMIC')
    values: dict[str, str] = {}
    index = 0
    while index < len(tokens):
        flag = tokens[index]
        if flag not in VALUE_FLAGS or flag in values or index + 1 >= len(tokens) or tokens[index + 1].startswith('-'):
            raise _form('ship accepts only one --title, --body-file, --base and optional --head, each with a separate value')
        values[flag] = tokens[index + 1]
        index += 2
    if any(flag not in values for flag in REQUIRED_FLAGS):
        raise _form('explicit PR title, body file and base branch required', 'PR_METADATA_INCOMPLETE')
    base = values['--base']
    if not BRANCH_RE.fullmatch(base):
        raise _form('ship base must be a plain branch name', 'PR_BASE_MISMATCH')
    head = values.get('--head')
    if head is not None and not BRANCH_RE.fullmatch(head):
        raise _form('ship head must be a plain branch name', 'PR_HEAD_MISMATCH')
    return {'title': values['--title'], 'body_file': values['--body-file'], 'base': base, 'head': head}


def _digest_file(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def _child_env() -> dict[str, str]:
    return {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GH_PROMPT_DISABLED': '1'}


def _run_push(root: Path, argv: list[str]) -> int:
    """Run the exact push; only the return code leaves this function, never remote output."""
    return subprocess.run(argv, cwd=root, env=_child_env(), capture_output=True, text=True,
                          timeout=CHILD_TIMEOUT_SECONDS, check=False).returncode


def _run_pr_create(root: Path, argv: list[str]) -> tuple[int, str]:
    proc = subprocess.run(argv, cwd=root, env=_child_env(), capture_output=True, text=True,
                          timeout=CHILD_TIMEOUT_SECONDS, check=False)
    return proc.returncode, proc.stdout


def _load_policy() -> tuple[dict[str, Any], str]:
    from check_secret_leakage import DEFAULT_POLICY, load_policy
    try:
        return load_policy(DEFAULT_POLICY)
    except OSError as exc:
        raise PublicationError('mandatory candidate secret-scan policy is unavailable',
                               'SECRET_SCAN_POLICY_UNAVAILABLE', phase='content_scan.policy_load',
                               context={'error_class': type(exc).__name__, 'component': 'check_secret_leakage'}) from exc


def _observe(cwd: Path, request: dict[str, Any]) -> dict[str, Any]:
    """Observe the exact candidate and the three child plans without executing anything."""
    root = Path(authority.git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    head = authority.git(root, 'rev-parse', 'HEAD^{commit}')
    if not re.fullmatch(r'[0-9a-f]{40,64}', head):
        raise PublicationError('candidate SHA unavailable', 'CANDIDATE_DIFF_UNAVAILABLE', phase='candidate_identity')
    branch = authority.git(root, 'branch', '--show-current')
    if not branch or not branch.startswith(authority.PERSONAL_BRANCH_PREFIXES):
        raise PublicationError('current engineering branch required', reason_code='BRANCH_NOT_ALLOWLISTED')
    if request.get('head') not in (None, branch):
        raise PublicationError('ship head must be the current candidate branch', reason_code='PR_HEAD_MISMATCH')
    title = str(request.get('title') or '')
    if not title.strip() or title.startswith('-'):
        raise _form('explicit PR title and body file required', 'PR_METADATA_INCOMPLETE')
    body = Path(str(request.get('body_file') or ''))
    body = body if body.is_absolute() else cwd / body
    if not body.is_file() or body.is_symlink():
        raise _form('explicit PR title and body file required', 'PR_METADATA_INCOMPLETE')
    body = body.resolve(strict=True)
    repo = planning._repo(root)
    remote_url = authority.git(root, 'remote', 'get-url', 'origin')
    default_branch = authority._remote_default_branch(root, remote_url)
    if request.get('base') != default_branch:
        raise PublicationError('personal PRs must target the remote default branch', reason_code='PR_BASE_MISMATCH')
    head_ref = 'refs/heads/' + branch
    push_argv = ['git', 'push', 'origin', head + ':' + head_ref]
    base = authority._personal_base(root, 'git_push', push_argv)
    push_scope = authority.action(root, 'git_push', push_argv, base, personal=True)
    worktree_state = authority.worktree_dirty_details(root)
    pr_argv = ['gh', 'pr', 'create', '--repo', repo, '--head', branch, '--base', default_branch,
               '--title', title, '--body-file', str(body)]
    return {'root': root, 'head': head, 'branch': branch, 'head_ref': head_ref, 'repo': repo,
            'default_branch': default_branch, 'base': base, 'push_argv': push_argv, 'pr_argv': pr_argv,
            'push_scope': push_scope, 'body': body, 'body_digest': _digest_file(body),
            'worktree_status': worktree_state['status'],
            'worktree_dirty_path_count': worktree_state.get('path_count', 0)}


def _ensure_scan(observed: dict[str, Any], policy: dict[str, Any], policy_hash: str) -> str:
    """Run the one exact-candidate scan, or reuse fresh evidence bound to this exact push scope."""
    root, scope = observed['root'], observed['push_scope']
    if evidence.valid(root, scope, policy_digest=policy_hash):
        return 'FRESH_EVIDENCE_REUSED'
    from check_secret_leakage import ScanError, scan_candidate
    scan_diagnostics: list[dict[str, Any]] = []
    try:
        findings, blockers, _, _ = scan_candidate(root, observed['base'], observed['head'], policy,
                                                  diagnostics=scan_diagnostics)
    except Exception as exc:
        safe = exc.safe_diagnostic() if isinstance(exc, ScanError) else {
            'reason_code': 'SECRET_SCAN_INTERNAL_ERROR', 'phase': 'content_scan.internal',
            'component': 'check_secret_leakage', 'error_class': type(exc).__name__}
        raise PublicationError('mandatory candidate and history secret scan could not complete',
                               safe['reason_code'], phase=safe['phase'],
                               context={'error_class': safe['error_class'], 'component': safe['component']}) from exc
    if scan_diagnostics:
        safe = scan_diagnostics[0]
        raise PublicationError('mandatory candidate and history secret scan could not complete',
                               safe['reason_code'], phase=safe['phase'],
                               context={'error_class': safe['error_class'], 'component': safe['component']})
    if findings or blockers:
        raise PublicationError('mandatory candidate and history secret scan blocked publication', 'CONTENT_SCAN_BLOCKED')
    evidence.store(root, scope, policy_digest=policy_hash)
    return 'SCANNED'


def _binding(observed: dict[str, Any], policy_hash: str) -> dict[str, Any]:
    root, scope = observed['root'], observed['push_scope']
    return {
        **authority.runtime_binding(root, candidate_sha=observed['head'], target_ref=observed['head_ref'], mode='personal'),
        'operation': OPERATION,
        'remote_oid': scope.get('expected_remote_oid'),
        'policy_digest': policy_hash,
        'scan_binding_digest': authority.digest(evidence.binding(root, scope, policy_digest=policy_hash)),
    }


def validate_for_hook(cwd: Path, tokens: list[str]) -> dict[str, Any]:
    """Hook validation for one `aips publish ship` invocation: exact candidate, scan evidence and binding."""
    observed = _observe(cwd, parse_tokens(tokens))
    policy, policy_hash = _load_policy()
    scan = _ensure_scan(observed, policy, policy_hash)
    return {'status': 'VALIDATED', 'scan': scan, 'binding': _binding(observed, policy_hash)}


def _require_evidence(root: Path, scope: dict[str, Any], policy_hash: str) -> None:
    if not evidence.valid(root, scope, policy_digest=policy_hash):
        raise PublicationError('fresh exact-candidate scan evidence required',
                               'PUBLICATION_SCAN_EVIDENCE_REQUIRED', phase='content_scan.evidence')


def _finish(result: dict[str, Any], status: str, state: str, next_step: str) -> dict[str, Any]:
    result.update(status=status, recovery={'state': state, 'next_step': next_step,
                                           'executed': result['executed'], 'requires_human': False})
    return result


def run(cwd: Path, request: dict[str, Any]) -> dict[str, Any]:
    """CLI chain: scan once, exact push, then PR create. Every child is re-validated before it runs."""
    result: dict[str, Any] = {'version': 1, 'command': 'aips publish ship', 'status': 'BLOCKED',
                              'executed': False, 'steps': [], 'diagnostics': []}
    phase = 'candidate_validation'
    try:
        if authority.publication_mode() != 'personal':
            raise PublicationError('publish ship is available only in personal publication mode',
                                   'ASSURANCE_MODE_BLOCKED', phase='authority_validation')
        observed = _observe(cwd, request)
        root, head, branch = observed['root'], observed['head'], observed['branch']
        result['worktree'] = {'status': observed['worktree_status'],
                              'dirty_path_count': observed['worktree_dirty_path_count']}
        policy, policy_hash = _load_policy()
        phase = 'content_scan'
        scan = _ensure_scan(observed, policy, policy_hash)
        result['steps'].append({'step': 'scan', 'status': 'PASS', 'evidence': scan})
        result['candidate'] = _binding(observed, policy_hash)

        phase = 'pr_observation'
        prs = planning._prs(root, observed['repo'], branch, observed['default_branch'])
        if any(row['state'] == 'MERGED' and row['headRefOid'] == head for row in prs):
            result['phase'] = 'post_merge_reconciliation'
            return _finish(result, 'COMPLETE', 'ALREADY_MERGED', 'POST_MERGE_RECONCILIATION')
        if sum(row['state'] == 'OPEN' for row in prs) > 1:
            raise PublicationError('multiple open PRs', 'PR_STATE_AMBIGUOUS', phase='pr_observation')
        if not any(row['state'] == 'OPEN' for row in prs) and any(
                row['state'] == 'CLOSED' and row['headRefOid'] == head for row in prs):
            raise PublicationError('closed candidate PR requires review', 'PR_STATE_AMBIGUOUS', phase='pr_observation')

        if observed['push_scope'].get('expected_remote_oid') == head:
            result['steps'].append({'step': 'push', 'status': 'SKIPPED_ALREADY_AT_CANDIDATE'})
        else:
            phase = 'push'
            # Re-observe the exact push scope and require fresh evidence for it before the child runs.
            fresh = authority.action(root, 'git_push', observed['push_argv'], observed['base'], personal=True)
            if fresh['candidate_commit'] != head:
                raise PublicationError('candidate changed after scan', 'CANDIDATE_CHANGED', phase='push')
            _require_evidence(root, fresh, policy_hash)
            result['executed'] = True
            try:
                returncode = _run_push(root, observed['push_argv'])
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise PublicationError('exact candidate push could not complete', 'SHIP_PUSH_FAILED',
                                       phase='push', context={'error_class': type(exc).__name__}) from exc
            if returncode or authority._tip(root, 'origin', observed['head_ref']) != head:
                raise PublicationError('exact candidate push did not reach the remote', 'SHIP_PUSH_FAILED', phase='push')
            result['steps'].append({'step': 'push', 'status': 'PUSHED', 'candidate_sha': head,
                                    'target_ref': observed['head_ref']})
            prs = planning._prs(root, observed['repo'], branch, observed['default_branch'])

        open_prs = [row for row in prs if row['state'] == 'OPEN']
        if open_prs:
            row = open_prs[0]
            if len(open_prs) > 1 or row['headRefOid'] != head:
                raise PublicationError('PR state is ambiguous or stale', 'PR_STATE_AMBIGUOUS', phase='pr_observation')
            result['steps'].append({'step': 'pr_create', 'status': 'SKIPPED_EXISTING_PR', 'pr_number': row['number']})
            return _finish(result, 'COMPLETE', 'EXISTING_PR', 'NONE')

        phase = 'pr_create'
        if _digest_file(observed['body']) != observed['body_digest']:
            raise PublicationError('PR body changed after scan', 'CANDIDATE_CHANGED', phase='pr_create')
        base = authority._personal_base(root, 'gh_pr_create', observed['pr_argv'])
        pr_scope = authority.action(root, 'gh_pr_create', observed['pr_argv'], base, personal=True)
        if pr_scope['candidate_commit'] != head:
            raise PublicationError('candidate changed before PR create', 'CANDIDATE_CHANGED', phase='pr_create')
        # The PR operation has its own binding; it reuses the one scan performed for this exact candidate.
        evidence.store(root, pr_scope, policy_digest=policy_hash)
        result['executed'] = True
        try:
            returncode, stdout = _run_pr_create(root, observed['pr_argv'])
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PublicationError('PR create could not complete', 'SHIP_PR_CREATE_FAILED',
                                   phase='pr_create', context={'error_class': type(exc).__name__}) from exc
        if returncode:
            raise PublicationError('PR create failed', 'SHIP_PR_CREATE_FAILED', phase='pr_create')
        pr_url = next((line.strip() for line in stdout.splitlines() if PR_URL_RE.fullmatch(line.strip())), None)
        result['steps'].append({'step': 'pr_create', 'status': 'CREATED', 'pr_url': pr_url})
        return _finish(result, 'COMPLETE', 'PUBLISHED', 'NONE')
    except PublicationError as exc:
        item = exc.diagnostic()
        item['phase'] = exc.phase or phase
        result['phase'] = item['phase']
        result['diagnostics'].append(item)
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        code = ('REMOTE_OBSERVATION_FAILED' if isinstance(exc, (OSError, subprocess.TimeoutExpired))
                and phase == 'pr_observation' else 'INTERNAL_DIAGNOSTIC_GAP')
        item = planning.diagnostic(code)
        item['error_class'] = type(exc).__name__
        item['phase'] = phase
        result['phase'] = phase
        result['diagnostics'].append(item)
    item = result['diagnostics'][-1]
    code = item.get('reason_code')
    state = ('RERUN_SHIP' if code in {'SHIP_PUSH_FAILED', 'SHIP_PR_CREATE_FAILED'}
             else 'REVALIDATE_BEFORE_RETRY' if code == 'CANDIDATE_CHANGED' else 'REPAIR_REQUIRED')
    _finish(result, 'BLOCKED', state, item.get('next_step', ''))
    result['recovery']['next_step_zh'] = item.get('next_step_zh', '')
    return result
