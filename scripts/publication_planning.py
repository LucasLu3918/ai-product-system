"""Read-only worktree-bound publication planning; observations never grant authority."""
from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

import publication_authority as authority
import yaml


def diagnostic(code: str) -> dict[str, str]:
    return authority.PublicationError('', code).diagnostic()


def _repo(root: Path) -> str:
    url = authority.git(root, 'remote', 'get-url', '--push', 'origin')
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?', url)
    if not match:
        raise authority.PublicationError('supported credential-free GitHub origin required', reason_code='REMOTE_CONFIGURATION_INVALID')
    return match.group(1)


def _prs(root: Path, repo: str, branch: str, base_branch: str) -> list[dict[str, Any]]:
    raw = authority.run(root, 'gh', 'pr', 'list', '--repo', repo, '--head', branch,
                        '--base', base_branch, '--state', 'all', '--limit', '100',
                        '--json', 'number,state,headRefOid,headRefName,baseRefName,isDraft,mergeCommit')
    try:
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) >= 100:
            raise ValueError('ambiguous PR discovery')
        for row in rows:
            if (not isinstance(row, dict) or type(row.get('number')) is not int or
                    row.get('state') not in {'OPEN', 'CLOSED', 'MERGED'} or
                    row.get('headRefName') != branch or row.get('baseRefName') != base_branch or
                    not re.fullmatch(r'[0-9a-f]{40,64}', str(row.get('headRefOid'))) or
                    type(row.get('isDraft')) is not bool):
                raise ValueError('invalid PR metadata')
        # Keep only the declared observation fields even if an upstream adds data.
        rows = [{key: row.get(key) for key in ('number', 'state', 'headRefOid', 'headRefName',
                'baseRefName', 'isDraft', 'mergeCommit')} for row in rows]
        for row in rows:
            commit = row['mergeCommit']
            if commit is not None:
                oid = commit.get('oid') if isinstance(commit, dict) else None
                if not re.fullmatch(r'[0-9a-f]{40,64}', str(oid)):
                    raise ValueError('invalid merge commit')
                row['mergeCommit'] = {'oid': oid}
        return sorted(rows, key=lambda row: row['number'])
    except (ValueError, TypeError) as exc:
        raise authority.PublicationError('PR observation unavailable', 'PR_STATE_AMBIGUOUS') from exc


def _invocation(root: Path, operation: str, argv: list[str]) -> dict[str, Any]:
    return {'operation': operation, 'cwd': str(root), 'argv': argv, 'command': shlex.join(argv),
            'execution': 'standalone_native_tool', 'revalidate_before_execution': True}


def _with_lifecycle(result: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    """Add explicit, non-authorizing Prepare state without changing legacy status."""
    status = result.get('status')
    observation = result.get('observation') or {}
    if root is None and observation.get('worktree'):
        root = Path(observation['worktree'])
    candidate: dict[str, Any] = dict(result.get('candidate') or {})
    candidate.setdefault('status', 'PASS' if result.get('scan') == 'PASS' else 'NOT_VALIDATED')
    if root is not None and observation.get('branch') and observation.get('head'):
        try:
            candidate.update(authority.runtime_binding(
                root, candidate_sha=observation['head'],
                target_ref='refs/heads/' + observation['branch'],
                mode=observation.get('mode') or result.get('mode') or 'UNKNOWN'))
        except (OSError, authority.PublicationError, ValueError, TypeError):
            candidate.update(worktree_id=observation.get('worktree_id', 'UNKNOWN'),
                             candidate_sha=observation.get('head', 'UNKNOWN'),
                             target_ref='refs/heads/' + observation['branch'],
                             mode=observation.get('mode') or result.get('mode') or 'UNKNOWN',
                             runtime_version='UNKNOWN', runtime_revision='UNKNOWN',
                             binding_fingerprint='UNKNOWN')
    result['candidate'] = candidate
    authorization_status = {
        'PLANNED': 'NOT_GRANTED',
        'VALIDATED': 'NOT_GRANTED',
        'AWAITING_AUTHORITY': 'AWAITING_HUMAN_AUTHORITY',
        'BLOCKED': 'DENIED',
        'COMPLETE': 'NOT_GRANTED_FOR_THIS_INVOCATION',
    }.get(status, 'NOT_EVALUATED')
    result['authorization'] = {
        'status': authorization_status,
        'authorized': False,
        'host_decision': 'NOT_EVALUATED',
    }
    result['execution'] = {
        'status': 'ALREADY_COMPLETE' if status == 'COMPLETE' else 'NOT_EXECUTED',
        'attempted': False,
        'completed': status == 'COMPLETE',
    }
    return result


def prepare(worktree: Path, *, title: str, body_file: Path, runtime: str = 'codex',
            expected_fingerprint: str | None = None, host_denied: bool = False,
            merge_intent: bool = False, auto_merge: bool = False,
            host_denial_class: str = "unknown") -> dict[str, Any]:
    """Re-observe Git/PR state each time; no cached step, grant or permission is trusted."""
    result: dict[str, Any] = {'version': 1, 'status': 'BLOCKED', 'authorized': False,
                              'diagnostics': [], 'invocations': [], 'host_permission': 'UNKNOWN',
                              'runtime': runtime, 'next_step': 'REOBSERVE', 'phase': 'candidate_validation'}
    phase = 'candidate_validation'
    if host_denied:
        result['host_permission'] = 'DENIED'
        codes = {
            'merge-without-review': 'HOST_MERGE_WITHOUT_REVIEW',
            'read-only-diagnostic': 'HOST_READ_ONLY_DENIED',
            'unknown': 'HOST_PERMISSION_DENIED',
        }
        result['diagnostics'] = [diagnostic(codes.get(host_denial_class,
                                                      'HOST_PERMISSION_DENIED'))]
        return _with_lifecycle(result)
    if auto_merge and not merge_intent:
        result['diagnostics'] = [diagnostic('AUTO_MERGE_REQUIRES_INTENT')]
        return _with_lifecycle(result)
    try:
        root = worktree.expanduser().resolve(strict=True)
        actual = Path(authority.git(root, 'rev-parse', '--show-toplevel')).resolve()
        if root != actual:
            raise authority.PublicationError('explicit worktree root required', 'CWD_MISMATCH')
        phase = 'authority_validation'
        mode = authority.publication_mode()
        result['mode'] = mode
        result['assurance'] = 'ADVISORY' if runtime in {'codex', 'opencode'} else 'NATIVE_PER_CALL_REQUIRED'
        result['native_merge_confirmation'] = 'REQUIRED' if runtime in {'claude-code', 'gemini-cli'} else 'UNSUPPORTED'
        if mode == 'high_assurance':
            # Validate present configuration; never downgrade or consume a grant.
            try:
                authority.configured_authority()
            except (authority.PublicationError, OSError, ValueError, TypeError, yaml.YAMLError) as exc:
                raise authority.PublicationError('invalid present trust root', 'AUTHORITY_CONFIG_INVALID') from exc
        branch = authority.git(root, 'branch', '--show-current')
        head = authority.git(root, 'rev-parse', 'HEAD^{commit}')
        if not branch or not branch.startswith(authority.PERSONAL_BRANCH_PREFIXES):
            raise authority.PublicationError('current engineering branch required', reason_code='BRANCH_NOT_ALLOWLISTED')
        if not title.strip() or not body_file.is_file() or body_file.is_symlink():
            raise authority.PublicationError('explicit PR title and body file required', 'PR_METADATA_INCOMPLETE')
        body_file = body_file.resolve(strict=True)
        body_bytes = body_file.read_bytes()
        phase = 'remote_observation'
        repo = _repo(root)
        push = ['git', 'push', 'origin', head + ':refs/heads/' + branch]
        base = authority._personal_base(root, 'git_push', push)
        remote_url = authority.git(root, 'remote', 'get-url', 'origin')
        base_branch = authority._remote_default_branch(root, remote_url)
        remote_head = authority._tip(root, 'origin', 'refs/heads/' + branch)
        if mode == 'high_assurance':
            push.insert(2, '--force-with-lease=refs/heads/' + branch + ':' + (remote_head or ''))
        phase = 'pr_observation'
        prs = _prs(root, repo, branch, base_branch)
        merged = [row for row in prs if row['state'] == 'MERGED' and row['headRefOid'] == head]
        if merged:
            # A squash merge need not make the feature HEAD an ancestor of main.
            # Bind the exact PR head and verify its GitHub merge commit in the live base.
            if authority.worktree_dirty_details(root)['status'] == 'DIRTY':
                raise authority.PublicationError('dirty candidate', 'WORKTREE_DIRTY',
                    context={'worktree': root, 'candidate_sha': head}, phase='post_merge_reconciliation')
            commit = (merged[-1].get('mergeCommit') or {}).get('oid', '')
            if not re.fullmatch(r'[0-9a-f]{40,64}', commit):
                raise authority.PublicationError('merge commit unavailable', 'PR_STATE_AMBIGUOUS')
            authority.git(root, 'merge-base', '--is-ancestor', commit, base)
            observation = {**authority.identity(root), 'worktree': str(root), 'head': head,
                           'base': base, 'mode': mode, 'prs': prs, 'merge_commit': commit}
            fingerprint = authority.digest(observation)
            if expected_fingerprint and expected_fingerprint != fingerprint:
                raise authority.PublicationError('stale observation', 'CANDIDATE_CHANGED')
            result.update(status='COMPLETE', phase='post_merge_reconciliation',
                          next_step='POST_MERGE_RECONCILIATION', recovery_state='ALREADY_MERGED',
                          operation='POST_MERGE_RECONCILIATION', idempotent=True,
                          observation=observation, fingerprint=fingerprint, scan='NOT_REQUIRED_ALREADY_MERGED')
            return _with_lifecycle(result, root)
        # Reuse the exact existing syntax, identity, clean-tree and ancestry checks.
        phase = 'push_validation'
        scope = authority.action(root, 'git_push', push, base, personal=mode == 'personal')
        phase = 'content_scan'
        from check_secret_leakage import DEFAULT_POLICY, load_policy, scan_candidate
        policy, policy_hash = load_policy(DEFAULT_POLICY)
        findings, blockers, _, _ = scan_candidate(root, base, head, policy)
        if findings or blockers:
            raise authority.PublicationError('candidate/history scan blocked', 'CONTENT_SCAN_BLOCKED')
        observation = {
            'worktree': str(root), 'repository_id': scope['repository_id'],
            'worktree_id': scope['worktree_id'], 'head': head, 'base': base,
            'branch': branch, 'base_branch': base_branch, 'mode': mode,
            'remote_digest': authority.digest(remote_url), 'remote_head': remote_head,
            'diff_digest': scope['diff_digest'], 'policy_digest': policy_hash,
            'prs': prs, 'runtime': runtime, 'merge_intent': merge_intent,
            'auto_merge': auto_merge,
            'title_digest': authority.digest(title), 'body_digest': authority.digest(body_bytes.hex()),
            'body_file': str(body_file),
        }
        fingerprint = authority.digest(observation)
        result.update(observation=observation, fingerprint=fingerprint, scan='PASS')
        if expected_fingerprint and expected_fingerprint != fingerprint:
            raise authority.PublicationError('stale publication observation', 'CANDIDATE_CHANGED')
        open_prs = [row for row in prs if row['state'] == 'OPEN']
        if len(open_prs) > 1:
            raise authority.PublicationError('multiple open PRs', 'PR_STATE_AMBIGUOUS')
        if remote_head != head:
            result.update(status='PLANNED', phase='push', next_step='PUSH')
            result['invocations'] = [_invocation(root, 'git_push', push)]
        elif open_prs:
            row = open_prs[0]
            if row['headRefOid'] != head:
                raise authority.PublicationError('stale PR head', 'PR_STATE_AMBIGUOUS')
            result.update(status='PLANNED', phase='checks', next_step='CHECKS_AND_MERGE_INTENT', pr_number=row['number'])
            if merge_intent and not row['isDraft']:
                # Respect the enabled repository merge methods; no admin/auto merge.
                phase = 'merge_validation'
                metadata = json.loads(authority.run(root, 'gh', 'api', 'repos/' + repo))
                method = next((name for name, key in (('squash', 'allow_squash_merge'),
                               ('merge', 'allow_merge_commit'), ('rebase', 'allow_rebase_merge'))
                               if metadata.get(key) is True), None)
                if not method:
                    raise authority.PublicationError('no enabled merge method', 'PR_STATE_AMBIGUOUS')
                argv = ['gh', 'pr', 'merge', str(row['number']), '--repo', repo,
                        '--' + method, '--match-head-commit', head]
                if auto_merge:
                    argv.append('--auto')
                authority.action(root, 'gh_pr_merge', argv, base, personal=mode == 'personal')
                result['invocations'] = [_invocation(root, 'gh_pr_merge', argv)]
                result['phase'] = 'merge'
                result['next_step'] = 'NATIVE_MERGE_CONFIRMATION' if runtime in {'claude-code', 'gemini-cli'} else 'TASK_AUTHORIZED_MERGE'
        else:
            if any(row['headRefOid'] == head and row['state'] == 'CLOSED' for row in prs):
                raise authority.PublicationError('closed candidate PR requires review', 'PR_STATE_AMBIGUOUS')
            argv = ['gh', 'pr', 'create', '--repo', repo, '--head', branch, '--base', base_branch,
                    '--title', title, '--body-file', str(body_file)]
            authority.action(root, 'gh_pr_create', argv, base, personal=mode == 'personal')
            result.update(status='PLANNED', phase='pr_create', next_step='CREATE_PR')
            result['invocations'] = [_invocation(root, 'gh_pr_create', argv)]
        if mode == 'high_assurance' and result['status'] != 'COMPLETE':
            result['diagnostics'].append(diagnostic('AUTHORITY_REQUIRED'))
            result['next_step'] = 'EXTERNAL_GRANT_THEN_' + result['next_step']
            result['status'] = 'AWAITING_AUTHORITY'
        return _with_lifecycle(result, root)
    except authority.PublicationError as exc:
        item = exc.diagnostic()
        item['phase'] = exc.phase or phase
        result['phase'] = item['phase']
        result['diagnostics'].append(item)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError, subprocess.TimeoutExpired) as exc:
        error_code = ('REMOTE_OBSERVATION_FAILED' if isinstance(exc, (OSError, subprocess.TimeoutExpired)) and phase in {'remote_observation', 'pr_observation'}
                      else 'CONTENT_SCAN_BLOCKED' if phase == 'content_scan'
                      else 'INTERNAL_DIAGNOSTIC_GAP')
        if isinstance(exc, subprocess.TimeoutExpired) and phase in {'remote_observation', 'pr_observation'}:
            item = authority.PublicationError(
                'remote observation timed out', error_code,
                context={'error_class': 'TimeoutExpired'}, phase=phase,
                detail_code='REMOTE_OBSERVATION_TIMEOUT').diagnostic()
        else:
            item = diagnostic(error_code)
            if error_code == 'INTERNAL_DIAGNOSTIC_GAP':
                item['error_class'] = type(exc).__name__
        item['phase'] = phase
        result['phase'] = phase
        result['diagnostics'].append(item)
    result.update(status='BLOCKED', invocations=[])
    return _with_lifecycle(result, locals().get('root'))


def diagnose(worktree: Path, command: str) -> dict[str, Any]:
    """Validate a native literal command without execution or grant consumption."""
    from publication_commands import CommandError, command_form_detail, shell_commands
    try:
        root = worktree.expanduser().resolve(strict=True)
        if Path(authority.git(root, 'rev-parse', '--show-toplevel')).resolve() != root:
            raise authority.PublicationError('worktree root mismatch', 'CWD_MISMATCH')
        parsed = shell_commands(command)
        if len(parsed) != 1:
            raise authority.PublicationError('standalone command required', 'COMMAND_FORM_UNSUPPORTED',
                                             detail_code=command_form_detail(command))
        argv = parsed[0]
        operation = ('git_push' if argv[:2] == ['git', 'push'] else
                     'gh_pr_create' if argv[:3] == ['gh', 'pr', 'create'] else
                     'gh_pr_merge' if argv[:3] == ['gh', 'pr', 'merge'] else None)
        if not operation:
            raise authority.PublicationError('unsupported planning operation', 'COMMAND_FORM_UNSUPPORTED')
        mode = authority.publication_mode()
        if mode == 'high_assurance':
            try:
                authority.configured_authority()
            except (authority.PublicationError, OSError, ValueError, TypeError, yaml.YAMLError) as exc:
                raise authority.PublicationError('invalid present trust root', 'AUTHORITY_CONFIG_INVALID') from exc
        observed = authority.validate_personal_action(root, operation, argv)
        if mode == 'high_assurance':
            # Diagnostics must honor the selected mode's stricter exact lease syntax.
            authority.action(root, operation, argv, observed['base_commit'], personal=False)
        result = {'version': 2, 'status': 'VALIDATED' if mode == 'personal' else 'AWAITING_AUTHORITY',
                  'authorized': False, 'read_only': True, 'executed': False,
                  'grant_consumed': False, 'operation': operation, 'mode': mode,
                  'diagnostics': [] if mode == 'personal' else [diagnostic('AUTHORITY_REQUIRED')]}
        candidate_sha = observed.get('candidate_commit') or observed.get('candidate_sha')
        if not candidate_sha or not re.fullmatch(r'[0-9a-f]{40,64}', candidate_sha):
            candidate_sha = authority.git(root, 'rev-parse', 'HEAD^{commit}')
        target_ref = observed.get('target_ref')
        if not target_ref:
            if operation == 'git_push':
                refspec = next((token for token in reversed(argv) if ':' in token), '')
                target_ref = refspec.split(':', 1)[1] if ':' in refspec else 'UNKNOWN'
            elif operation == 'gh_pr_create' and '--base' in argv:
                target_ref = 'refs/heads/' + argv[argv.index('--base') + 1]
            else:
                merge = observed.get('merge_confirmation') or {}
                target_ref = ('refs/heads/' + merge['base_branch']) if merge.get('base_branch') else 'UNKNOWN'
        result['candidate'] = {'status': 'PASS', **authority.runtime_binding(
            root, candidate_sha=candidate_sha, target_ref=target_ref, mode=mode)}
        return _with_lifecycle(result, root)
    except authority.PublicationError as exc:
        return {'status': 'BLOCKED', 'authorized': False, 'diagnostics': [exc.diagnostic()]}
    except CommandError as exc:
        item = authority.PublicationError('', 'COMMAND_FORM_UNSUPPORTED', detail_code=exc.detail_code).diagnostic()
        item['phase'] = 'command_validation'
        return _with_lifecycle({'status': 'BLOCKED', 'authorized': False, 'diagnostics': [item]})
    except (OSError, subprocess.TimeoutExpired) as exc:
        item = diagnostic('REMOTE_OBSERVATION_FAILED')
        item['error_class'] = type(exc).__name__
        item['phase'] = 'remote_observation'
        return _with_lifecycle({'status': 'BLOCKED', 'authorized': False, 'diagnostics': [item]})
    except (ValueError, TypeError, yaml.YAMLError) as exc:
        item = diagnostic('INTERNAL_DIAGNOSTIC_GAP')
        item['error_class'] = type(exc).__name__
        item['phase'] = 'diagnostic_processing'
        return _with_lifecycle({'status': 'BLOCKED', 'authorized': False, 'diagnostics': [item]})

def recovery_guidance(result: dict[str, Any]) -> dict[str, Any]:
    """Non-authorizing status guidance; never executes a publication action."""
    status = str(result.get('status') or 'BLOCKED')
    next_step = str(result.get('next_step') or 'REOBSERVE')
    diagnostics = result.get('diagnostics') or []
    codes = [item.get('reason_code') for item in diagnostics if isinstance(item, dict)]
    if status == 'COMPLETE':
        state, human, retry = 'ALREADY_MERGED', False, False
    elif any(str(code).startswith('HOST_') for code in codes):
        state, human, retry = 'HOST_PERMISSION_REQUIRED', True, False
    elif status == 'AWAITING_AUTHORITY':
        state, human, retry = 'HUMAN_AUTHORITY_REQUIRED', True, False
    elif next_step == 'NATIVE_MERGE_CONFIRMATION':
        state, human, retry = 'HUMAN_CONFIRMATION_REQUIRED', True, False
    elif 'REQUIRED_CHECKS_PENDING' in codes:
        state, human, retry = 'CHECKS_PENDING', False, True
    elif any(isinstance(item, dict) and item.get('retryable') is True and
             item.get('category') in {'NETWORK', 'RATE_LIMITED', 'GITHUB_SERVER_ERROR', 'TIMEOUT'}
             for item in diagnostics):
        state, human, retry = 'READ_OBSERVATION_RETRYABLE', False, True
    elif status == 'BLOCKED':
        state, human, retry = 'REPAIR_REQUIRED', False, False
    elif next_step == 'CHECKS_AND_MERGE_INTENT':
        state, human, retry = 'RECHECK_REQUIRED_CHECKS', False, True
    else:
        state, human, retry = 'REVALIDATE_BEFORE_NATIVE_ACTION', False, False
    return {
        'state': state, 'next_step': next_step,
        'requires_human': human, 'retry_read_only': retry,
        'executed': False, 'authorized': False,
        'instruction': 'Reobserve the exact PR, branch and checks before any native mutation; '
                       'this recovery report never authorizes publication.',
    }

def doctor(worktree: Path, *, branch: str | None = None, pr_number: int | None = None,
           worktree_details: bool = False) -> dict[str, Any]:
    """Read-only, phase-separated publication evidence. This never grants or executes authority."""
    result: dict[str, Any] = {'version': 2, 'status': 'UNKNOWN', 'authorized': False,
                              'api_write_performed': False, 'phases': [], 'diagnostics': [],
                              'next_step': 'REVIEW_EVIDENCE_BEFORE_ANY_PUBLICATION'}
    try:
        root = worktree.expanduser().resolve(strict=True)
        actual = Path(authority.git(root, 'rev-parse', '--show-toplevel')).resolve()
        if root != actual:
            raise authority.PublicationError('worktree root mismatch', 'CWD_MISMATCH', phase='worktree_identity')
        head = authority.git(root, 'rev-parse', 'HEAD^{commit}')
        if not re.fullmatch(r'[0-9a-f]{40,64}', head):
            raise authority.PublicationError('candidate SHA unavailable', 'CANDIDATE_DIFF_UNAVAILABLE', phase='candidate_identity')
        dirty = authority.worktree_dirty_details(root)
        branch_name = authority.git(root, 'branch', '--show-current') or None
        if worktree_details:
            result['worktree_details'] = dirty
        result['candidate_sha'] = head
        result['worktree'] = {'branch': branch_name, 'status': dirty['status']}
        result['phases'].append({'phase': 'worktree_validation', 'status': dirty['status'],
                                 'blocking': dirty['status'] == 'DIRTY'})
        if dirty['status'] == 'DIRTY':
            item = authority.PublicationError('publication requires a clean worktree', 'WORKTREE_DIRTY',
                context={'worktree': root, 'candidate_sha': head}, phase='worktree_validation').diagnostic()
            if not worktree_details:
                item.pop('worktree_details', None)
            result['diagnostics'].append(item)

        repo = _repo(root)
        remote_url = authority.git(root, 'remote', 'get-url', 'origin')
        base_branch = branch or authority._remote_default_branch(root, remote_url)
        result['repository'] = repo
        result['policy_branch'] = base_branch
        result['phases'].append({'phase': 'repository_identity', 'status': 'PASS', 'repository': repo})

        from repository_governance_snapshot import build_snapshot, query_github_api
        snapshot = build_snapshot(repo, base_branch, lambda endpoint: query_github_api(root, endpoint))
        result['governance'] = snapshot
        policy_status = snapshot['protection_state']
        result['phases'].append({'phase': 'protection_policy_evidence', 'status': policy_status,
                                 'evidence_level': snapshot['evidence_level'],
                                 'blocking': policy_status == 'UNKNOWN'})
        if policy_status == 'UNKNOWN':
            item = authority.PublicationError('branch protection evidence unavailable',
                'PROTECTION_EVIDENCE_UNAVAILABLE', phase='protection_policy_evidence').diagnostic()
            item['api_sources'] = snapshot['sources']
            result['diagnostics'].append(item)

        if pr_number is not None:
            pr_call = subprocess.run(['gh', 'pr', 'view', str(pr_number), '--repo', repo,
                '--json', 'number,state,headRefOid,headRefName,baseRefName,isDraft,mergeable,mergeStateStatus'],
                cwd=root, capture_output=True, text=True, timeout=15, check=False)
            try:
                pr_data = json.loads(pr_call.stdout) if pr_call.returncode == 0 else None
            except json.JSONDecodeError:
                pr_data = None
            if isinstance(pr_data, dict) and pr_data.get('number') == pr_number:
                result['pr'] = {key: pr_data.get(key) for key in ('number', 'state', 'headRefOid',
                    'headRefName', 'baseRefName', 'isDraft', 'mergeable', 'mergeStateStatus')}
                result['phases'].append({'phase': 'pr_state_observation', 'status': 'OBSERVED'})
            else:
                result['phases'].append({'phase': 'pr_state_observation', 'status': 'UNKNOWN',
                                         'error_class': 'GITHUB_CLI_OR_PR_STATE_UNAVAILABLE'})
                item = authority.PublicationError('PR observation unavailable', 'PR_STATE_AMBIGUOUS',
                                                  phase='pr_state_observation').diagnostic()
                result['diagnostics'].append(item)

        blockers = [phase for phase in result['phases'] if phase.get('blocking') or phase['status'] == 'UNKNOWN']
        result['status'] = 'OBSERVED' if not blockers else 'INCOMPLETE'
        return result
    except authority.PublicationError as exc:
        item = exc.diagnostic()
        item['phase'] = exc.phase or 'worktree_identity'
        result['diagnostics'].append(item)
        result['phases'].append({'phase': item['phase'], 'status': 'UNKNOWN', 'blocking': True})
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired):
        item = diagnostic('REMOTE_OBSERVATION_FAILED')
        item['phase'] = 'remote_observation'
        result['diagnostics'].append(item)
        result['phases'].append({'phase': 'remote_observation', 'status': 'UNKNOWN', 'blocking': True})
    result['status'] = 'INCOMPLETE'
    return result
