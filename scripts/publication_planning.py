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
        raise authority.PublicationError('supported credential-free GitHub origin required')
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


def prepare(worktree: Path, *, title: str, body_file: Path, runtime: str = 'codex',
            expected_fingerprint: str | None = None, host_denied: bool = False,
            merge_intent: bool = False, auto_merge: bool = False) -> dict[str, Any]:
    """Re-observe Git/PR state each time; no cached step, grant or permission is trusted."""
    result: dict[str, Any] = {'version': 1, 'status': 'BLOCKED', 'authorized': False,
                              'diagnostics': [], 'invocations': [], 'host_permission': 'UNKNOWN',
                              'runtime': runtime, 'next_step': 'REOBSERVE'}
    if host_denied:
        result['host_permission'] = 'DENIED'
        result['diagnostics'] = [diagnostic('HOST_PERMISSION_DENIED')]
        return result
    if auto_merge and not merge_intent:
        result['diagnostics'] = [diagnostic('AUTO_MERGE_REQUIRES_INTENT')]
        return result
    try:
        root = worktree.expanduser().resolve(strict=True)
        actual = Path(authority.git(root, 'rev-parse', '--show-toplevel')).resolve()
        if root != actual:
            raise authority.PublicationError('explicit worktree root required', 'CWD_MISMATCH')
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
            raise authority.PublicationError('current engineering branch required')
        if not title.strip() or not body_file.is_file() or body_file.is_symlink():
            raise authority.PublicationError('explicit PR title and body file required', 'PR_METADATA_INCOMPLETE')
        body_file = body_file.resolve(strict=True)
        body_bytes = body_file.read_bytes()
        repo = _repo(root)
        push = ['git', 'push', 'origin', head + ':refs/heads/' + branch]
        base = authority._personal_base(root, 'git_push', push)
        remote_url = authority.git(root, 'remote', 'get-url', 'origin')
        base_branch = authority._remote_default_branch(root, remote_url)
        remote_head = authority._tip(root, 'origin', 'refs/heads/' + branch)
        if mode == 'high_assurance':
            push.insert(2, '--force-with-lease=refs/heads/' + branch + ':' + (remote_head or ''))
        prs = _prs(root, repo, branch, base_branch)
        merged = [row for row in prs if row['state'] == 'MERGED' and row['headRefOid'] == head]
        if merged:
            # A squash merge need not make the feature HEAD an ancestor of main.
            # Bind the exact PR head and verify its GitHub merge commit in the live base.
            if authority.git(root, 'status', '--porcelain', '--untracked-files=all'):
                raise authority.PublicationError('dirty candidate', 'WORKTREE_DIRTY')
            commit = (merged[-1].get('mergeCommit') or {}).get('oid', '')
            if not re.fullmatch(r'[0-9a-f]{40,64}', commit):
                raise authority.PublicationError('merge commit unavailable', 'PR_STATE_AMBIGUOUS')
            authority.git(root, 'merge-base', '--is-ancestor', commit, base)
            observation = {**authority.identity(root), 'worktree': str(root), 'head': head,
                           'base': base, 'mode': mode, 'prs': prs, 'merge_commit': commit}
            fingerprint = authority.digest(observation)
            if expected_fingerprint and expected_fingerprint != fingerprint:
                raise authority.PublicationError('stale observation', 'CANDIDATE_CHANGED')
            result.update(status='COMPLETE', next_step='POST_MERGE_RECONCILIATION',
                          observation=observation, fingerprint=fingerprint, scan='NOT_REQUIRED_ALREADY_MERGED')
            return result
        # Reuse the exact existing syntax, identity, clean-tree and ancestry checks.
        scope = authority.action(root, 'git_push', push, base, personal=mode == 'personal')
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
            result.update(status='PLANNED', next_step='PUSH')
            result['invocations'] = [_invocation(root, 'git_push', push)]
        elif open_prs:
            row = open_prs[0]
            if row['headRefOid'] != head:
                raise authority.PublicationError('stale PR head', 'PR_STATE_AMBIGUOUS')
            result.update(status='PLANNED', next_step='CHECKS_AND_MERGE_INTENT', pr_number=row['number'])
            if merge_intent and not row['isDraft']:
                # Respect the enabled repository merge methods; no admin/auto merge.
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
                result['next_step'] = 'NATIVE_MERGE_CONFIRMATION' if runtime in {'claude-code', 'gemini-cli'} else 'TASK_AUTHORIZED_MERGE'
        else:
            if any(row['headRefOid'] == head and row['state'] == 'CLOSED' for row in prs):
                raise authority.PublicationError('closed candidate PR requires review', 'PR_STATE_AMBIGUOUS')
            argv = ['gh', 'pr', 'create', '--repo', repo, '--head', branch, '--base', base_branch,
                    '--title', title, '--body-file', str(body_file)]
            authority.action(root, 'gh_pr_create', argv, base, personal=mode == 'personal')
            result.update(status='PLANNED', next_step='CREATE_PR')
            result['invocations'] = [_invocation(root, 'gh_pr_create', argv)]
        if mode == 'high_assurance' and result['status'] != 'COMPLETE':
            result['diagnostics'].append(diagnostic('AUTHORITY_REQUIRED'))
            result['next_step'] = 'EXTERNAL_GRANT_THEN_' + result['next_step']
            result['status'] = 'AWAITING_AUTHORITY'
        return result
    except authority.PublicationError as exc:
        result['diagnostics'].append(exc.diagnostic())
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError, subprocess.TimeoutExpired):
        result['diagnostics'].append(diagnostic('REMOTE_OBSERVATION_FAILED'))
    result.update(status='BLOCKED', invocations=[])
    return result


def diagnose(worktree: Path, command: str) -> dict[str, Any]:
    """Validate a native literal command without execution or grant consumption."""
    from publication_commands import CommandError, shell_commands
    try:
        root = worktree.expanduser().resolve(strict=True)
        if Path(authority.git(root, 'rev-parse', '--show-toplevel')).resolve() != root:
            raise authority.PublicationError('worktree root mismatch', 'CWD_MISMATCH')
        parsed = shell_commands(command)
        if len(parsed) != 1:
            raise authority.PublicationError('standalone command required', 'COMMAND_FORM_UNSUPPORTED')
        argv = parsed[0]
        operation = 'git_push' if argv[:2] == ['git', 'push'] else 'gh_pr_create' if argv[:3] == ['gh', 'pr', 'create'] else None
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
        return {'status': 'VALIDATED' if mode == 'personal' else 'AWAITING_AUTHORITY',
                'authorized': False, 'mode': mode,
                'diagnostics': [] if mode == 'personal' else [diagnostic('AUTHORITY_REQUIRED')]}
    except authority.PublicationError as exc:
        return {'status': 'BLOCKED', 'authorized': False, 'diagnostics': [exc.diagnostic()]}
    except CommandError:
        return {'status': 'BLOCKED', 'authorized': False, 'diagnostics': [diagnostic('COMMAND_FORM_UNSUPPORTED')]}
    except (OSError, ValueError, TypeError, yaml.YAMLError, subprocess.TimeoutExpired):
        return {'status': 'BLOCKED', 'authorized': False, 'diagnostics': [diagnostic('REMOTE_OBSERVATION_FAILED')]}
