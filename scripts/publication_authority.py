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
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import yaml

CONFIG = Path('/etc/aips/publication-authority.yaml')
PUBLICATION_OPERATIONS = {'git_push', 'git_tag', 'gh_pr_create', 'gh_pr_merge', 'gh_release_create'}
PERSONAL_PUBLICATION_OPERATIONS = {'git_push', 'gh_pr_create', 'gh_pr_merge'}
PERSONAL_BRANCH_PREFIXES = ('agent/', 'bugfix/', 'chore/', 'claude/', 'codex/', 'docs/', 'feat/', 'feature/', 'fix/', 'gemini/', 'work/')


class PublicationError(ValueError):
    def __init__(self, message: str, reason_code: str | None = None, *,
                 context: dict[str, Any] | None = None, phase: str | None = None,
                 detail_code: str | None = None):
        super().__init__(message)
        self.context = context or {}
        self.reason_code = (reason_code if reason_code not in {None, 'PUBLICATION_REJECTED'}
                            else _reason_for_message(message))
        self.phase = phase
        self.detail_code = detail_code

    def diagnostic(self) -> dict[str, Any]:
        # Never expose exception text: Git/host errors may contain private data.
        code = self.reason_code if self.reason_code in PUBLICATION_DIAGNOSTICS else 'INTERNAL_DIAGNOSTIC_GAP'
        values = PUBLICATION_DIAGNOSTICS[code]
        detail, next_step = values[:2]
        phase = self.phase or _phase_for_code(code)
        source = _source_for_code(code)
        result: dict[str, Any] = {
            'version': 2,
            'diagnostic_id': str(uuid.uuid4()),
            'timestamp': datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
            'reason_code': code,
            'detail': detail,
            'next_step': next_step,
            'phase': phase,
            'category': values[3] if len(values) > 3 else 'POLICY',
            'source': 'CLAUDE_HOST' if code.startswith('HOST_') else 'AIPS_PUBLICATION',
            'blocking_rule': source,
            'blocking_rule_id': _blocking_rule_id(code),
            'retryable': code in RETRYABLE_REASONS,
            'redacted': True,
            'recovery_mode': 'HUMAN_OR_HOST_REQUIRED' if source in {'HUMAN_AUTHORITY', 'HOST_PERMISSION'} else 'SAFE_OBSERVATION',
        }
        detail_code = self.detail_code or self.context.get('detail_code')
        detail = PUBLICATION_DETAIL_DIAGNOSTICS.get(detail_code) if isinstance(detail_code, str) else None
        if detail:
            result.update(detail_code=detail_code, detail=detail[0], next_step=detail[1])
        detail_zh, next_step_zh = PUBLICATION_DIAGNOSTICS_ZH.get(
            code, ('發布驗證未通過。', '檢查此階段的安全診斷，修正後重新執行唯讀驗證。'))
        if detail:
            detail_zh, next_step_zh = detail[2], detail[3]
        result['detail_zh'] = detail_zh
        result['next_step_zh'] = next_step_zh
        error_class = self.context.get('error_class') or type(self).__name__
        if (code == 'INTERNAL_DIAGNOSTIC_GAP' or code.startswith('SECRET_SCAN_')) and isinstance(error_class, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]{0,79}', error_class):
            result['error_class'] = error_class
        component = self.context.get('component')
        if code.startswith('SECRET_SCAN_') and component == 'check_secret_leakage':
            result['component'] = component
        candidate = self.context.get('candidate_sha')
        if isinstance(candidate, str) and re.fullmatch(r'[0-9a-f]{40,64}', candidate):
            result['candidate_sha'] = candidate
        worktree_id = self.context.get('worktree_id')
        if isinstance(worktree_id, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', worktree_id):
            result['worktree_id'] = worktree_id
        target_ref = self.context.get('target_ref')
        if isinstance(target_ref, str) and re.fullmatch(r'refs/heads/[A-Za-z0-9._/-]{1,200}', target_ref):
            result['target_ref'] = target_ref
        mode = self.context.get('mode')
        if mode in {'personal', 'high_assurance'}:
            result['mode'] = mode
        file_path = self.context.get('file')
        if isinstance(file_path, str) and len(file_path) <= 2048:
            path_fingerprint = 'sha256:' + hashlib.sha256(file_path.encode('utf-8')).hexdigest()
            if re.fullmatch(r'[A-Za-z0-9._/-]{1,200}', file_path):
                relative = PurePosixPath(file_path)
                from content_safety import scan_payload
                if (not relative.is_absolute() and '..' not in relative.parts and not re.match(r'^[A-Za-z]:', file_path)
                        and not any(item.action == 'BLOCK' for item in scan_payload(file_path, sink='git_commit', strict=True))):
                    result['file'] = file_path
                else:
                    result['path_fingerprint'] = path_fingerprint
            else:
                result['path_fingerprint'] = path_fingerprint
        font_format = self.context.get('format')
        if font_format in {'ttf', 'otf', 'woff', 'woff2', 'TrueType', 'OpenType-CFF', 'WOFF', 'WOFF2'}:
            result['format'] = font_format
        error_class = self.context.get('error_class')
        if code.startswith('STAGED_FONT_') and isinstance(error_class, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]{0,79}', error_class):
            result['error_class'] = error_class
        worktree = self.context.get('worktree')
        if code == 'WORKTREE_DIRTY' and isinstance(worktree, Path):
            result['worktree_details'] = worktree_dirty_details(worktree)
        policy_sources = self.context.get('policy_sources')
        if isinstance(policy_sources, dict):
            result['api_sources'] = {name: {key: item.get(key) for key in
                ('status', 'endpoint', 'http_status', 'error_class')}
                for name, item in policy_sources.items() if isinstance(item, dict)}
        return result


PUBLICATION_DIAGNOSTICS = {
    'PUBLICATION_REJECTED': ('Publication binding was rejected.', 'Inspect the candidate with aips publish prepare; retain the current authority boundary.', 'validation', 'POLICY'),
    'INTERNAL_DIAGNOSTIC_GAP': ('AIPS could not safely classify an internal publication failure.', 'Record the Diagnostic ID and error class; repair the local AIPS diagnostic mapping before retrying.', 'internal_diagnostics', 'INTERNAL'),
    'PUSH_TARGET_BRANCH_MISMATCH': ('Push target does not match the current engineering branch.', 'Verify the selected worktree and full target ref, then rerun read-only publication diagnosis.', 'push_validation', 'POLICY'),
    'COMMAND_FORM_UNSUPPORTED': ('The publication command form is unsupported.', 'Use the standalone literal native command emitted by the validated plan; do not change it to bypass the guard.', 'command_validation', 'INVALID_ARGUMENT'),
    'PUBLICATION_INPUT_UNBOUND': ('The publication input cannot be bound to the inspected operation.', 'Supply explicit literal input through a supported option or file, then revalidate.', 'command_validation', 'INVALID_ARGUMENT'),
    'PUBLICATION_OPTION_INVALID': ('A required publication option is missing or unsupported.', 'Provide one explicit supported option value and revalidate.', 'command_validation', 'INVALID_ARGUMENT'),
    'SECRET_SCAN_POLICY_INVALID': ('The required secret-scan policy is invalid.', 'Repair the repository secret-scan policy and rerun publication validation.', 'content_scan.policy_validation', 'POLICY'),
    'SECRET_SCAN_ALLOWLIST_EXPIRED': ('The secret-scan allowlist contains an expired entry.', 'Remove or renew the expired allowlist entry with its approved fingerprint and rerun validation.', 'content_scan.allowlist_check', 'POLICY'),
    'SECRET_SCAN_BASE_INVALID': ('The secret-scan base cannot be verified for this candidate.', 'Refresh the candidate base and rerun exact-candidate publication validation.', 'content_scan.base_validation', 'STALE'),
    'SECRET_SCAN_GIT_OBJECT_MISSING': ('A Git object required by the secret scan is unavailable.', 'Restore or fetch the candidate history in this worktree, then rerun validation.', 'content_scan.git_object_read', 'UNAVAILABLE'),
    'SECRET_SCAN_FILE_UNREADABLE': ('A candidate file could not be completely inspected by the secret scanner.', 'Restore readable UTF-8 candidate content and rerun exact-candidate validation.', 'content_scan.candidate_file_read', 'UNAVAILABLE'),
    'SECRET_SCAN_POLICY_UNAVAILABLE': ('The required secret-scan policy could not be read.', 'Restore access to the repository secret-scan policy and rerun validation.', 'content_scan.policy_load', 'UNAVAILABLE'),
    'SECRET_SCAN_INTERNAL_ERROR': ('The required secret scanner failed safely.', 'Record the Diagnostic ID and error class; repair the local scanner before retrying publication.', 'content_scan.internal', 'INTERNAL'),
    'ISSUER_REQUEST_INVALID': ('The Human issuer rejected an invalid grant request.', 'Review the proposal-bound request fields and submit a new valid request.', 'authority_validation', 'INVALID_ARGUMENT'),
    'ISSUER_PROPOSAL_STATE_INVALID': ('Only a pending publication proposal can be issued.', 'Return the proposal to its valid pending state and obtain Human review.', 'authority_validation', 'POLICY'),
    'ISSUER_PROPOSAL_MISMATCH': ('The grant request does not match the reviewed proposal.', 'Rebuild the request from the exact reviewed proposal and candidate.', 'authority_validation', 'STALE'),
    'ISSUER_EVIDENCE_INCOMPLETE': ('The proposal is missing required validation evidence.', 'Complete the exact-candidate validation and attach its evidence before requesting a grant.', 'authority_validation', 'MISSING'),
    'ISSUER_NONCE_INVALID': ('The grant request nonce is invalid or replayed.', 'Generate a fresh nonce and request a new grant.', 'authority_validation', 'POLICY'),
    'ISSUER_KEY_PERMISSION_INVALID': ('The issuer private key permissions are too broad.', 'Restrict the key to the administrator-owned 0600 permission mode.', 'authority_validation', 'PERMISSION'),
    'ISSUER_KEY_UNAVAILABLE': ('A required issuer signing key is unavailable or invalid.', 'Check the administrator-owned issuer key configuration and retry the grant request.', 'authority_validation', 'UNAVAILABLE'),
    'ISSUER_INVALID_REQUEST': ('The Human issuer request is invalid.', 'Review the proposal-bound request fields and submit a valid request.', 'authority_validation', 'INVALID_ARGUMENT'),
    'ISSUER_PROPOSAL_NOT_PENDING': ('Only a pending publication proposal can be issued.', 'Return the proposal to its valid pending state and obtain Human review.', 'authority_validation', 'POLICY'),
    'ISSUER_KEY_MODE_INVALID': ('The issuer private key permissions are too broad.', 'Restrict the key to administrator-owned 0600 permissions.', 'authority_validation', 'PERMISSION'),
    'ISSUER_KEY_INVALID': ('A required issuer signing key is unavailable or invalid.', 'Check administrator-owned issuer key configuration and retry the grant request.', 'authority_validation', 'UNAVAILABLE'),
    'MERGE_METHOD_REQUIRED': ('Exactly one merge method is required.', 'Use one enabled method: --merge, --squash or --rebase; check repository settings first.', 'command', 'INVALID_ARGUMENT'),
    'MERGE_PR_NUMBER_REQUIRED': ('The merge command must name one PR number.', 'Use a literal gh pr merge <number> command from the validated worktree.', 'command', 'INVALID_ARGUMENT'),
    'MERGE_HEAD_PIN_REQUIRED': ('The merge command lacks --match-head-commit.', 'Re-observe the live PR head and use its full SHA with --match-head-commit.', 'command', 'INVALID_ARGUMENT'),
    'MERGE_HEAD_MISMATCH': ('The supplied --match-head-commit does not equal the candidate HEAD.', 'Re-observe the candidate and PR head; regenerate a bound command without reusing a stale SHA.', 'candidate', 'STALE'),
    'MERGE_OPTION_FORBIDDEN': ('A merge option is prohibited or not supported by the exact-candidate policy.', 'Use the standalone merge invocation emitted by prepare; perform branch cleanup as a separate authorized action.', 'command', 'INVALID_ARGUMENT'),
    'REQUIRED_CHECKS_POLICY_UNVERIFIED': ('Required-check configuration cannot be confirmed from the available evidence.', 'Run publish doctor; ask an administrator to verify branch protection visibility before retrying.', 'checks', 'UNAVAILABLE'),
    'HOST_MERGE_WITHOUT_REVIEW': ('Claude Code Auto Mode classified the request as Merge Without Review.', 'Use the normal interactive Host approval/review flow; do not rewrite commands to bypass the denial.', 'host', 'PERMISSION'),
    'HOST_READ_ONLY_DENIED': ('Claude Code denied a read-only publication diagnostic.', 'Run the same diagnostic in a trusted interactive environment or review exact permission rules; never infer merge approval.', 'host', 'PERMISSION'),
    'PUSH_SOURCE_NOT_EXACT_SHA': ('Push source must equal the full candidate SHA.', 'Resolve HEAD and use its literal full SHA as the refspec source.'),
    'INVALID_TARGET_REF': ('An explicit full target ref is required.', 'Use refs/heads/<current-engineering-branch>.'),
    'WORKTREE_DIRTY': ('The selected worktree has uncommitted content.', 'Preserve development files; review delivery scope or use a separate clean candidate worktree.'),
    'CWD_MISMATCH': ('The current worktree differs from the planned candidate.', 'Set the native tool working directory to the planned worktree and re-observe.'),
    'BASE_NOT_ANCESTOR': ('The live default base is not an ancestor of the candidate.', 'Preserve the candidate; review merge/rebase and conflicts, then revalidate the new SHA.'),
    'BASE_OBJECT_MISSING': ('The live default commit is not available locally.', 'Fetch the remote default branch in the selected worktree, then re-observe.'),
    'AUTHORITY_REQUIRED': ('High-assurance publication requires an external grant.', 'Use the configured Human issuer; a plan does not create or consume a grant.'),
    'AUTHORITY_CONFIG_INVALID': ('The present authority configuration cannot be used.', 'Repair the administrator trust root; do not remove it or fall back to personal mode.'),
    'HOST_PERMISSION_DENIED': ('The host denied the operation.', 'Resolve permissions through the host approval flow; do not retry using another command form.'),
    'CONTENT_SCAN_BLOCKED': ('Mandatory candidate/history content scanning failed.', 'Review the scanner policy and safe finding categories; resolve them and revalidate.'),
    'PR_METADATA_INCOMPLETE': ('Explicit PR metadata is incomplete or ambiguous.', 'Provide unique --repo, --head, --base, --title and exactly one --body or --body-file.'),
    'REMOTE_OBSERVATION_FAILED': ('Required repository or remote evidence is unavailable.', 'Diagnose network, authentication and repository configuration without printing raw errors.'),
    'CANDIDATE_CHANGED': ('Candidate or publication inputs changed after planning.', 'Discard the previous observation and create a fresh plan; reissue grants when required.'),
    'PR_STATE_AMBIGUOUS': ('PR state is ambiguous or stale.', 'Review matching PRs and remote head before continuing; do not create duplicate PRs.'),
    'STAGED_CONTENT_UNAVAILABLE': ('A staged file could not be read for content inspection.', 'Check the staged index and file availability, then restage and retry.'),
    'STAGED_INDEX_UNAVAILABLE': ('The staged index could not be inspected.', 'Repair the local Git index and rerun the read-only commit safety diagnosis.', 'staged_index', 'UNAVAILABLE'),
    'STAGED_BLOB_UNAVAILABLE': ('A staged Git blob could not be inspected.', 'Check the staged file and local Git object database, then rerun the read-only diagnosis.', 'staged_blob', 'UNAVAILABLE'),
    'MESSAGE_FILE_UNAVAILABLE': ('The explicit commit message file could not be read.', 'Check the file encoding and local access, then rerun the commit safety diagnosis.', 'commit_message', 'UNAVAILABLE'),
    'STAGED_CONTENT_TOO_LARGE': ('A staged file exceeds the content inspection limit.', 'Split or remove the oversized staged file, then retry.'),
    'STAGED_CONTENT_UNSUPPORTED_BINARY': ('The staged binary format is unsupported by the safe metadata scanner.', 'Use a supported media format or remove the unsupported binary from the candidate.', 'staged_blob', 'UNSUPPORTED'),
    'STAGED_MEDIA_INVALID': ('A staged media file is malformed or its extension does not match its contents.', 'Repair the media file or use a supported format with matching contents.', 'media_metadata', 'INVALID'),
    'STAGED_MEDIA_SIGNATURE_MISMATCH': ('The media signature does not match its file extension or expected container.', 'Re-export the asset in the declared format; renaming the file alone will not repair its contents.', 'media_metadata', 'SIGNATURE'),
    'STAGED_MEDIA_UNSUPPORTED_FEATURE': ('The media uses a format feature that the bounded inspector does not support.', 'Re-export as a supported static AVIF image or use a format feature supported by the local scanner.', 'media_metadata', 'UNSUPPORTED'),
    'STAGED_MEDIA_METADATA_UNINSPECTABLE': ('Media metadata locations could not be safely inspected.', 'Re-export the file with standard local metadata layout or remove unsupported metadata before retrying.', 'media_metadata', 'UNINSPECTABLE'),
    'STAGED_MEDIA_RESOURCE_LIMIT': ('The media exceeds a bounded file, metadata, or parser resource limit.', 'Reduce the file or metadata below the documented limit; do not raise the shared limit for one asset.', 'media_metadata', 'LIMIT'),
    'STAGED_FONT_INVALID': ('A staged font is malformed or cannot be safely parsed.', 'Repair or replace the font, then rerun the read-only commit safety diagnosis.', 'font_metadata', 'INVALID'),
    'STAGED_FONT_FORMAT_MISMATCH': ('A staged font signature does not match its filename extension.', 'Use the correct font extension or replace the malformed file.', 'font_metadata', 'INVALID'),
    'STAGED_FONT_INSPECTOR_UNAVAILABLE': ('The required font metadata inspector is not installed.', 'Install the declared fontTools dependency and rerun the read-only diagnosis.', 'font_metadata', 'UNAVAILABLE'),
    'STAGED_FONT_BROTLI_UNAVAILABLE': ('The required WOFF2 decompressor is not installed.', 'Install the declared Brotli dependency and rerun the read-only diagnosis.', 'font_metadata', 'UNAVAILABLE'),
    'STAGED_FONT_RESOURCE_LIMIT': ('A staged font exceeds a bounded inspection resource limit.', 'Reduce or replace the font and stay within the documented size limits.', 'font_metadata', 'LIMIT'),
    'CONTENT_SCANNER_FAILED': ('The required commit content scanner could not complete.', 'Resolve the local scanner error and retry without bypassing the safety check.', 'content_scan', 'UNAVAILABLE'),
    'CONTENT_SECRET_BLOCKED': ('A secret detector blocked commit content.', 'Remove or rotate the possible secret, then rerun the read-only commit safety diagnosis.', 'content_scan', 'SECRET'),
    'CONTENT_PII_BLOCKED': ('A personal-information detector blocked commit content.', 'Remove or redact the personal information according to policy, then rerun the diagnosis.', 'content_scan', 'PII'),
    'CONTENT_INJECTION_BLOCKED': ('An instruction-pattern detector blocked commit content.', 'Revise the instruction-like content, then rerun the read-only commit safety diagnosis.', 'content_scan', 'INJECTION_SIGNAL'),
    'CONTENT_SAFETY_BLOCKED': ('The commit content safety policy blocked a candidate.', 'Review the safe finding categories, correct the candidate, then rerun the diagnosis.', 'content_scan', 'POLICY'),
    'CONTENT_INSPECTION_UNAVAILABLE': ('The content inspection step could not complete.', 'Check the local scanner and Git state, then retry without bypassing the guard.'),
    'AUTO_MERGE_REQUIRES_INTENT': ('Automatic merge planning requires explicit merge intent.', 'Re-run prepare with --merge-intent or --auto-merge only after reviewing the exact candidate.', 'authority', 'POLICY'),
    'REQUIRED_CHECKS_UNCONFIGURED': ('No required checks were returned for this PR.', 'Ask a repository administrator to review Required Checks; empty evidence never permits merge.', 'checks', 'POLICY'),
    'REQUIRED_CHECKS_FAILING': ('One or more required checks failed.', 'Resolve the failed checks and rerun the read-only diagnosis.', 'checks', 'FAILING'),
    'REQUIRED_CHECKS_PENDING': ('One or more required checks are still running.', 'Wait for required checks to finish, then rerun the read-only diagnosis.', 'checks', 'PENDING'),
    'REQUIRED_CHECKS_MISSING': ('A required check is missing or skipped.', 'Restore the required check result for this exact SHA, then rerun diagnosis.', 'checks', 'MISSING'),
    'REQUIRED_CHECKS_CANCELLED': ('A required check was cancelled.', 'Rerun the cancelled required check and revalidate the exact SHA.', 'checks', 'CANCELLED'),
    'REQUIRED_CHECKS_PERMISSION': ('GitHub did not allow required-check evidence to be read.', 'Resolve repository access with an administrator; do not treat unavailable checks as passing.', 'checks', 'PERMISSION'),
    'REQUIRED_CHECKS_AUTHENTICATION': ('GitHub authentication is unavailable for required-check inspection.', 'Resolve the existing GitHub CLI login locally, then rerun diagnosis.', 'checks', 'AUTHENTICATION'),
    'REQUIRED_CHECKS_NETWORK': ('GitHub required-check evidence could not be reached.', 'Check connectivity and retry the read-only diagnosis.', 'checks', 'NETWORK'),
    'REQUIRED_CHECKS_POLICY_PERMISSION': ('Required Checks policy is hidden by GitHub permissions.', 'Ask a repository administrator to confirm policy visibility; do not treat hidden policy as unconfigured.', 'checks', 'PERMISSION'),
    'REQUIRED_CHECKS_POLICY_NETWORK': ('Required Checks policy could not be reached because of a network failure.', 'Check connectivity, then retry the read-only diagnosis.', 'checks', 'NETWORK'),
    'REQUIRED_CHECKS_POLICY_RATE_LIMITED': ('GitHub rate limited the Required Checks policy observation.', 'Wait for the rate limit to clear, then retry the read-only diagnosis.', 'checks', 'RATE_LIMITED'),
    'REQUIRED_CHECKS_POLICY_GITHUB_SERVER_ERROR': ('GitHub could not complete the Required Checks policy observation.', 'Retry the read-only diagnosis after GitHub service recovers.', 'checks', 'GITHUB_SERVER_ERROR'),
    'REQUIRED_CHECKS_API_UNAVAILABLE': ('GitHub required-check evidence is unavailable.', 'Check GitHub API availability and repository access, then retry.', 'checks', 'API_UNAVAILABLE'),
    'REQUIRED_CHECKS_INVALID': ('GitHub returned an invalid required-check response.', 'Inspect GitHub CLI compatibility and retry without bypassing the merge guard.', 'checks', 'INVALID_RESPONSE'),

    'REMOTE_CONFIGURATION_INVALID': ('The configured Git remote is ambiguous or does not match the verified origin.', 'Review origin fetch and push URLs locally. Resolve ambiguity only after verifying the destination.'),
    'REMOTE_BRANCH_UNAVAILABLE': ('The remote default branch could not be observed.', 'Check connectivity and repository access, then repeat the read-only observation.'),
    'ALTERNATE_GIT_ENVIRONMENT': ('An alternate Git environment changes the inspected repository context.', 'Remove the injected Git environment and re-run from the selected worktree.'),
    'REMOTE_REF_AMBIGUOUS': ('The requested remote reference is ambiguous.', 'Use one explicit full reference and re-observe its exact target.'),
    'BASE_SHA_INVALID': ('The publication base is missing or is not a full commit SHA.', 'Resolve the live default-branch commit and use its full SHA.'),
    'CANDIDATE_DIFF_UNAVAILABLE': ('The candidate diff could not be verified.', 'Preserve the candidate and inspect local Git object and worktree availability.'),
    'BRANCH_NOT_ALLOWLISTED': ('The current branch is not an allowed engineering branch.', 'Continue on a reviewed feature branch; do not push to a protected branch.'),
    'PUSH_METADATA_INVALID': ('The push target or refspec is missing, ambiguous, or multi-ref.', 'Use a single origin and an explicit exact-SHA to full-ref refspec.'),
    'REMOTE_NOT_ALLOWED': ('The selected remote is not the verified origin.', 'Use the configured origin after verifying its fetch and push URLs.'),
    'TAG_OPERATION_REQUIRES_REVIEW': ('Tag or release publication requires a separate review path.', 'Use the release proposal and tag verification workflow.'),
    'GITHUB_HOST_UNSUPPORTED': ('The GitHub host is not supported by this publication policy.', 'Use a supported host or request a separately reviewed policy change.'),
    'MERGE_METHOD_INVALID': ('The merge method is missing or ambiguous.', 'Select exactly one repository-enabled merge method.'),
    'AUTO_MERGE_INVALID': ('Automatic merge options are duplicated or inconsistent.', 'Use one explicit auto-merge option with exact merge intent.'),
    'RELEASE_TAG_INVALID': ('The release tag is missing, unverified, or does not point to the exact candidate.', 'Verify the remote tag and exact candidate SHA before retrying.'),
    'REPOSITORY_MISMATCH': ('The GitHub repository does not match the selected Git remote.', 'Verify --repo against the selected origin before continuing.'),
    'PR_HEAD_MISMATCH': ('The PR head is not bound to the selected candidate branch and SHA.', 'Re-observe the PR and candidate; do not update or merge a mismatched head.'),
    'CANDIDATE_NOT_PINNED': ('The merge command does not pin the exact candidate SHA.', 'Re-plan against the current PR head and pass its full SHA.'),
    'PR_NOT_MERGEABLE': ('The PR is closed, draft, or not ready to merge.', 'Resolve the PR state through review; do not retry the merge command.'),
    'PR_MERGEABILITY_UNKNOWN': ('GitHub has not confirmed PR mergeability.', 'Re-observe after resolving conflicts or pending repository checks.'),
    'PR_BASE_MISMATCH': ('The PR does not target the live default branch.', 'Re-plan for the verified default branch; do not retarget a stale merge.'),
    'REQUIRED_CHECKS_INCOMPLETE': ('Required PR checks are missing, pending, or failing.', 'Wait for the exact candidate’s required aggregate to pass, then re-observe.'),
    'REQUIRED_CHECKS_UNAVAILABLE': ('Required PR check state could not be observed.', 'Check GitHub access and connectivity, then re-read checks; do not merge on unknown state.'),
    'CREDENTIAL_BEARING_REMOTE': ('The configured remote URL contains credentials.', 'Remove credentials from the URL and use the host credential manager.'),
    'FORCE_WITH_LEASE_REQUIRED': ('The force update does not pin the observed target tip.', 'Use an exact target-and-tip lease only after a fresh candidate plan.'),
    'BASE_CHANGED': ('The live default base changed after the publication observation.', 'Discard the stale plan and revalidate the exact candidate against the new base.'),
    'ASSURANCE_MODE_BLOCKED': ('The selected assurance mode does not permit this operation.', 'Follow the configured approval and external-grant workflow.'),
    'AUTHORITY_TIME_INVALID': ('The authority timestamp is missing or invalid.', 'Request a new Human-issued approval with a valid UTC timestamp.'),
    'AUTHORITY_REDIRECT_BLOCKED': ('The authority endpoint attempted a redirect.', 'Use the configured credential-free HTTPS issuer endpoint.'),
    'AUTHORITY_ENDPOINT_INVALID': ('The configured authority endpoint is invalid.', 'Repair the administrator-owned trust configuration; do not remove the gate.'),
    'AUTHORITY_KEY_MISSING': ('The trusted issuer key is missing.', 'Configure the administrator-owned issuer key before requesting a grant.'),
    'AUTHORITY_SIGNATURE_INVALID': ('The publication grant signature is invalid or untrusted.', 'Obtain a new grant from the configured Human issuer.'),
    'AUTHORITY_RESPONSE_TOO_LARGE': ('The authority response exceeds the safe size limit.', 'Ask the issuer administrator to correct the response; do not retry through another endpoint.'),
    'AUTHORITY_GRANT_DENIED': ('The issuer denied, expired, or already consumed the grant.', 'Request a fresh operation-scoped grant from the Human issuer.'),
    'AUTHORITY_GRANT_EXPIRED': ('The signed authority grant is expired or outside its time window.', 'Request a new time-bounded grant.'),
    'AUTHORITY_CONFIG_WRITABLE': ('The authority trust root is writable by the Agent.', 'Move ownership and permissions to the administrator-controlled trust domain.'),
    'AUTHORITY_LEGACY_GRANT': ('A legacy grant does not satisfy the current signed format.', 'Reissue approval using the current signed grant format.'),
    'AUTHORITY_GRANT_INCOMPLETE': ('The Human-issued grant is incomplete.', 'Request a complete approval for the exact operation and candidate.'),
    'AUTHORITY_SCOPE_MISMATCH': ('The approval does not bind the current publication proposal.', 'Review the exact proposal and request a matching approval.'),
    'PUBLICATION_EVIDENCE_UNRESOLVED': ('Required publication evidence is unresolved.', 'Resolve every blocking evidence item before planning the operation.'),
    'AUTHORITY_VALIDATION_MISSING': ('Candidate-bound validation evidence is missing.', 'Run the exact candidate Gate and attach its verified evidence.'),
    'PUBLICATION_COMMAND_UNBOUND': ('The executed command is not bound to the approved operation.', 'Re-plan and request approval for the literal command that will run.'),
    'AUTHORITY_ACTION_MISMATCH': ('The requested action differs from the approved scope.', 'Stop and request Human approval for the changed action.'),
    'WORKTREE_STATE_UNAVAILABLE': ('The selected worktree status could not be read.', 'Inspect Git availability and repository state locally; do not infer that the worktree is clean.'),
    'PROTECTION_EVIDENCE_UNAVAILABLE': ('The effective branch policy could not be established from complete GitHub evidence.', 'Review HTTP status and endpoint evidence; ask an administrator for missing read permission or verify with the effective-rules API. Never infer that the branch is unprotected.'),
}

PUBLICATION_DETAIL_DIAGNOSTICS = {
    'PIPE_UNSUPPORTED': ('A publication command was combined with a shell pipeline.', 'Run the exact approved publication command by itself; do not pipe it through another command.', '發布指令含有管線。', '單獨執行規劃產生的原生發布指令，不要串接管線。'),
    'MULTI_COMMAND_UNSUPPORTED': ('A publication command was combined with another shell command.', 'Run one exact approved publication command at a time.', '發布指令與其他 Shell 命令組合。', '一次只執行一個經核准的原生發布指令。'),
    'COMMAND_WRAPPER_UNSUPPORTED': ('A publication command uses an unsupported shell wrapper.', 'Use the standalone literal command emitted by the validated plan.', '發布指令使用不支援的 Shell 包裝形式。', '使用驗證計畫輸出的獨立原生指令。'),
    'SHELL_SYNTAX_UNSUPPORTED': ('A publication command uses shell syntax that AIPS cannot safely inspect.', 'Simplify the command to the standalone literal form emitted by the validated plan.', '發布指令使用 AIPS 無法安全檢查的 Shell 語法。', '改用驗證計畫輸出的獨立字面指令。'),
    'UNSUPPORTED_HEREDOC': ('A publication command uses a heredoc form AIPS cannot safely inspect.', 'Use a quoted heredoc or run the validated publication command separately.', '發布指令使用 AIPS 無法安全檢查的 heredoc 格式。', '改用加引號的 heredoc，或另外執行驗證過的發布指令。'),
    'PUSH_UPSTREAM_OPTION_UNSUPPORTED': ('The upstream-setting push option is not supported for guarded publication.', 'Use the exact remote and full target ref from the validated plan without -u or --set-upstream.', '受保護的發布流程不支援設定 upstream 的 push 選項。', '依驗證計畫指定 remote 與完整目標 ref 執行，不要使用 -u 或 --set-upstream。'),
    'PUSH_OPTION_UNSUPPORTED': ('The push command includes an unsupported option.', 'Use only the options emitted by the validated publication plan.', 'Push 指令含有不支援的選項。', '只使用驗證發布計畫輸出的選項。'),
    'DYNAMIC_EXECUTABLE': ('The publication executable is dynamically selected and cannot be verified.', 'Use a literal executable name from a supported publication workflow.', '發布執行程式由動態內容選取，無法驗證。', '使用支援發布流程中的固定執行程式名稱。'),
    'DYNAMIC_SUBCOMMAND': ('The publication subcommand is dynamically selected and cannot be verified.', 'Use a literal Git or GitHub CLI subcommand.', '發布子命令由動態內容選取，無法驗證。', '使用固定的 Git 或 GitHub CLI 子命令。'),
    'DYNAMIC_CLI_OPTION': ('A publication context option is dynamically selected and cannot be bound.', 'Provide a literal repository, branch or worktree option value.', '發布環境選項由動態內容選取，無法綁定。', '提供固定的 repository、branch 或 worktree 選項值。'),
}

PUBLICATION_DIAGNOSTICS_ZH = {
    'SECRET_SCAN_POLICY_INVALID': ('秘密掃描政策格式或欄位無效。', '修復儲存庫的秘密掃描政策後，重新執行發布驗證。'),
    'SECRET_SCAN_ALLOWLIST_EXPIRED': ('秘密掃描允許清單有已過期項目。', '依核准指紋移除或更新過期項目，再重新驗證。'),
    'SECRET_SCAN_BASE_INVALID': ('無法確認秘密掃描使用的候選基底。', '更新候選基底，並重新驗證精確候選。'),
    'SECRET_SCAN_GIT_OBJECT_MISSING': ('秘密掃描需要的 Git 物件目前無法讀取。', '在此工作樹還原或取得候選歷史，再重新驗證。'),
    'SECRET_SCAN_FILE_UNREADABLE': ('秘密掃描器無法完整檢查候選檔案。', '修復候選內容的讀取或 UTF-8 編碼問題，再重新驗證。'),
    'SECRET_SCAN_POLICY_UNAVAILABLE': ('無法讀取必要的秘密掃描政策。', '恢復儲存庫秘密掃描政策的讀取權限，再重新驗證。'),
    'SECRET_SCAN_INTERNAL_ERROR': ('秘密掃描器安全停止，未完成檢查。', '保留診斷 ID 與錯誤類型，修復本機掃描器後再重試。'),
    'INTERNAL_DIAGNOSTIC_GAP': ('AIPS 無法安全分類這項內部發布錯誤。', '保留診斷 ID 與錯誤類型，修正本機 AIPS 診斷映射後再重試。'),
    'PUSH_TARGET_BRANCH_MISMATCH': ('推送目標分支與目前工程分支不一致。', '確認選用的工作樹與完整目標 ref，再重新執行唯讀發布診斷。'),
    'BRANCH_NOT_ALLOWLISTED': ('目前分支不符合允許的工程分支規則。', '在核准的工程分支上重新規劃；不要推送至受保護分支。'),
    'PUSH_SOURCE_NOT_EXACT_SHA': ('推送來源不是目前候選的完整 SHA。', '重新確認候選 HEAD，使用該完整 SHA 與完整 refs/heads 目標重新診斷。'),
    'INVALID_TARGET_REF': ('推送目標 ref 格式不完整或無效。', '使用 refs/heads/<工程分支名稱>，並重新執行唯讀診斷。'),
    'WORKTREE_DIRTY': ('選用的工作樹仍有未提交內容。', '先檢閱並保留工作檔案，確認交付範圍後再建立乾淨候選。'),
    'CWD_MISMATCH': ('目前工作樹與規劃時選用的候選不同。', '切回原候選工作樹並重新確認 HEAD、分支與工作目錄。'),
    'CANDIDATE_CHANGED': ('候選或發布觀測在規劃後已變更。', '捨棄舊觀測，對目前候選重新執行完整規劃與驗證。'),
    'CONTENT_SCAN_BLOCKED': ('必要的候選內容或歷史掃描未通過。', '依安全掃描提供的原因修正內容，重新掃描候選；不可略過掃描。'),
    'AUTHORITY_REQUIRED': ('高保證發布需要外部 Human 授權。', '透過已設定的 Human issuer 為精確操作與候選取得授權。'),
    'HOST_PERMISSION_DENIED': ('Claude Code Host 拒絕了這項操作。', '使用 Host 正常互動授權流程；不要改寫指令以避開拒絕。'),
    'REMOTE_OBSERVATION_FAILED': ('必要的遠端或儲存庫資訊目前無法取得。', '檢查網路、登入與儲存庫設定後重新執行唯讀診斷。'),
    'REQUIRED_CHECKS_PENDING': ('必要檢查仍在執行。', '等待此候選 SHA 的必要檢查完成，再重新讀取狀態。'),
    'REQUIRED_CHECKS_FAILING': ('此候選有必要檢查失敗。', '修正失敗的檢查並確認同一候選 SHA 的必要檢查通過。'),
    'PR_HEAD_MISMATCH': ('PR 頭端與目前候選分支或 SHA 不符。', '重新讀取 PR 與候選資訊；不可更新或合併不相符的頭端。'),
    'PR_BASE_MISMATCH': ('PR 目標分支不是目前遠端預設分支。', '確認預設分支並重新規劃，不要沿用過期目標。'),
    'COMMAND_FORM_UNSUPPORTED': ('發布指令格式不受支援。', '使用規劃輸出的獨立原生指令，不要改寫成繞過保護的形式。'),
    'PUBLICATION_REJECTED': ('發布綁定驗證未通過。', '重新執行 aips publish prepare 與唯讀診斷，檢查候選與授權界線。'),
    'STAGED_INDEX_UNAVAILABLE': ('無法讀取暫存索引。', '修復本機 Git index 後，重新執行唯讀 commit 安全診斷。'),
    'STAGED_BLOB_UNAVAILABLE': ('無法讀取暫存 Git blob。', '檢查暫存檔與本機 Git 物件資料庫後，重新執行唯讀診斷。'),
    'MESSAGE_FILE_UNAVAILABLE': ('無法讀取指定的 commit 訊息檔。', '檢查檔案編碼與存取權限後，重新執行 commit 安全診斷。'),
    'STAGED_CONTENT_UNSUPPORTED_BINARY': ('此二進位格式不受安全 metadata scanner 支援。', '改用受支援的媒體格式，或從候選中移除該二進位檔。'),
    'STAGED_MEDIA_INVALID': ('媒體檔格式錯誤，或副檔名與實際內容不符。', '修復媒體檔，或改用格式與內容一致的受支援檔案。'),
    'STAGED_MEDIA_SIGNATURE_MISMATCH': ('媒體簽章與副檔名或預期容器不符。', '重新以宣告格式匯出；只改副檔名無法修復內容。'),
    'STAGED_MEDIA_UNSUPPORTED_FEATURE': ('媒體使用目前有界檢查器尚不支援的格式特性。', '重新匯出為受支援的靜態 AVIF，或改用掃描器支援的格式特性。'),
    'STAGED_MEDIA_METADATA_UNINSPECTABLE': ('無法安全檢查媒體中繼資料位置。', '使用標準本機中繼資料配置重新匯出，或移除不支援的中繼資料後重試。'),
    'STAGED_MEDIA_RESOURCE_LIMIT': ('媒體超出檔案、中繼資料或解析器的有界資源上限。', '將檔案或中繼資料縮小至文件限制內；不要只為單一素材放寬共用上限。'),
    'STAGED_FONT_INVALID': ('字型檔格式錯誤或無法安全解析。', '修復或替換字型檔後，重新執行唯讀 commit 安全診斷。'),
    'STAGED_FONT_FORMAT_MISMATCH': ('字型簽章與檔名副檔名不一致。', '改用正確副檔名或替換格式錯誤的檔案。'),
    'STAGED_FONT_INSPECTOR_UNAVAILABLE': ('缺少必要的字型 metadata 檢查器。', '安裝已宣告的 fontTools 相依套件後重新執行唯讀診斷。'),
    'STAGED_FONT_BROTLI_UNAVAILABLE': ('缺少必要的 WOFF2 解壓套件。', '安裝已宣告的 Brotli 相依套件後重新執行唯讀診斷。'),
    'STAGED_FONT_RESOURCE_LIMIT': ('字型檔超出有界檢查的資源上限。', '縮小或替換字型檔，並遵守文件中的大小限制。'),
    'CONTENT_SCANNER_FAILED': ('必要的 commit 內容掃描未能完成。', '修復本機 scanner 後重新執行；不可略過安全檢查。'),
    'CONTENT_SECRET_BLOCKED': ('commit 內容觸發可能的密鑰偵測規則。', '移除或輪替可能的密鑰，再重新執行唯讀 commit 安全診斷。'),
    'CONTENT_PII_BLOCKED': ('commit 內容觸發個人資料偵測規則。', '依政策移除或遮蔽個人資料，再重新執行唯讀診斷。'),
    'CONTENT_INJECTION_BLOCKED': ('commit 內容觸發指令樣式偵測規則。', '修改類似指令的內容，再重新執行唯讀 commit 安全診斷。'),
    'CONTENT_SAFETY_BLOCKED': ('commit 內容未通過安全政策。', '查看不含內容的分類摘要、修正候選後重新執行診斷。'),
}


_MESSAGE_REASON_PREFIXES = (
    ('personal publication requires one matching origin', 'REMOTE_CONFIGURATION_INVALID'),
    ('remote default branch tip unavailable', 'REMOTE_BRANCH_UNAVAILABLE'),
    ('remote default branch unavailable', 'REMOTE_BRANCH_UNAVAILABLE'),
    ('alternate Git environment unsupported', 'ALTERNATE_GIT_ENVIRONMENT'),
    ('ambiguous remote ref', 'REMOTE_REF_AMBIGUOUS'),
    ('explicit base commit SHA required', 'BASE_SHA_INVALID'),
    ('candidate diff unavailable', 'CANDIDATE_DIFF_UNAVAILABLE'),
    ('publication requires an explicit feature branch', 'BRANCH_NOT_ALLOWLISTED'),
    ('one named remote and one explicit refspec required', 'PUSH_METADATA_INVALID'),
    ('personal mode permits only the verified single origin remote', 'REMOTE_NOT_ALLOWED'),
    ('personal mode permits only the current engineering branch', 'PUSH_TARGET_BRANCH_MISMATCH'),
    ('personal PRs must target the remote default branch', 'PR_BASE_MISMATCH'),
    ('implicit multi-ref publication configuration forbidden', 'PUSH_METADATA_INVALID'),
    ('supported tag mutation is', 'TAG_OPERATION_REQUIRES_REVIEW'),
    ('unsupported GitHub host', 'GITHUB_HOST_UNSUPPORTED'),
    ('use standalone gh command', 'COMMAND_FORM_UNSUPPORTED'),
    ('exactly one explicit merge method required', 'MERGE_METHOD_INVALID'),
    ('duplicate automatic merge option', 'AUTO_MERGE_INVALID'),
    ('release creation requires an existing verified remote tag', 'RELEASE_TAG_INVALID'),
    ('missing explicit option value', 'PUBLICATION_OPTION_INVALID'),
    ('unsupported or ambiguous GitHub publication option', 'PUBLICATION_OPTION_INVALID'),
    ('explicit GitHub owner/repository required', 'PR_METADATA_INCOMPLETE'),
    ('gh repository does not match Git remote', 'REPOSITORY_MISMATCH'),
    ('PR head must be the bound candidate branch', 'PR_HEAD_MISMATCH'),
    ('remote PR head differs from candidate', 'PR_HEAD_MISMATCH'),
    ('explicit PR number and checked merge required', 'PR_METADATA_INCOMPLETE'),
    ('merge must pin the exact candidate SHA', 'CANDIDATE_NOT_PINNED'),
    ('PR must be open and ready for review', 'PR_NOT_MERGEABLE'),
    ('PR head differs from candidate', 'PR_HEAD_MISMATCH'),
    ('personal PR merge must use the current allowlisted engineering branch', 'BRANCH_NOT_ALLOWLISTED'),
    ('PR mergeability is not confirmed', 'PR_MERGEABILITY_UNKNOWN'),
    ('personal PR merge must target the remote default branch', 'PR_BASE_MISMATCH'),
    ('required PR checks are not all complete and passing', 'REQUIRED_CHECKS_INCOMPLETE'),
    ('required PR check status unavailable', 'REQUIRED_CHECKS_UNAVAILABLE'),
    ('required PR checks are missing or not all passing', 'REQUIRED_CHECKS_INCOMPLETE'),
    ('explicit release tag required', 'RELEASE_TAG_INVALID'),
    ('release tag must point to the exact candidate commit', 'RELEASE_TAG_INVALID'),
    ('stdin publication text cannot be bound', 'PUBLICATION_INPUT_UNBOUND'),
    ('exactly one push URL required', 'REMOTE_CONFIGURATION_INVALID'),
    ('credential-bearing remote URL forbidden', 'CREDENTIAL_BEARING_REMOTE'),
    ('one explicit target/tip force-with-lease required', 'FORCE_WITH_LEASE_REQUIRED'),
    ('PR base differs from current remote tip', 'BASE_CHANGED'),
    ('local and remote release tag differ', 'RELEASE_TAG_INVALID'),
    ('operation is unavailable in personal publication mode', 'ASSURANCE_MODE_BLOCKED'),
    ('UTC timestamp required', 'AUTHORITY_TIME_INVALID'),
    ('invalid UTC timestamp', 'AUTHORITY_TIME_INVALID'),
    ('authority redirects are forbidden', 'AUTHORITY_REDIRECT_BLOCKED'),
    ('invalid authority configuration', 'AUTHORITY_ENDPOINT_INVALID'),
    ('authority requires a credential-free HTTPS endpoint', 'AUTHORITY_ENDPOINT_INVALID'),
    ('trusted issuer keys required', 'AUTHORITY_KEY_MISSING'),
    ('unsupported signature algorithm', 'AUTHORITY_SIGNATURE_INVALID'),
    ('untrusted or invalid publication signature', 'AUTHORITY_SIGNATURE_INVALID'),
    ('oversized authority response', 'AUTHORITY_RESPONSE_TOO_LARGE'),
    ('authority denied, stale or replayed grant', 'AUTHORITY_GRANT_DENIED'),
    ('authority assertion expired or exceeds', 'AUTHORITY_GRANT_EXPIRED'),
    ('authority configuration must be administrator-owned', 'AUTHORITY_CONFIG_WRITABLE'),
    ('authority config/path is writable', 'AUTHORITY_CONFIG_WRITABLE'),
    ('signed v2 publication grant required', 'AUTHORITY_LEGACY_GRANT'),
    ('complete Human-issued approval required', 'AUTHORITY_GRANT_INCOMPLETE'),
    ('approval expired, future-dated', 'AUTHORITY_GRANT_EXPIRED'),
    ('proposal scope fingerprint mismatch', 'AUTHORITY_SCOPE_MISMATCH'),
    ('unresolved publication evidence', 'PUBLICATION_EVIDENCE_UNRESOLVED'),
    ('publication validation evidence required', 'AUTHORITY_VALIDATION_MISSING'),
    ('actual command required', 'PUBLICATION_COMMAND_UNBOUND'),
    ('actual publication action differs', 'AUTHORITY_ACTION_MISMATCH'),
    ('supported credential-free GitHub origin required', 'REMOTE_CONFIGURATION_INVALID'),
    ('literal publication command required', 'COMMAND_FORM_UNSUPPORTED'),
)


def _reason_for_message(message: str) -> str:
    for prefix, code in _MESSAGE_REASON_PREFIXES:
        if message.startswith(prefix):
            return code
    return 'INTERNAL_DIAGNOSTIC_GAP'


RETRYABLE_REASONS = {'REQUIRED_CHECKS_PENDING', 'REQUIRED_CHECKS_POLICY_NETWORK',
                     'REQUIRED_CHECKS_POLICY_RATE_LIMITED',
                     'REQUIRED_CHECKS_POLICY_GITHUB_SERVER_ERROR'}


def _phase_for_code(code: str) -> str:
    if code.startswith(('AUTHORITY_', 'ISSUER_', 'PUBLICATION_EVIDENCE', 'CONTENT_SCAN')):
        return 'authorization_and_content_validation'
    if code.startswith(('PR_', 'REQUIRED_CHECKS_', 'MERGE_', 'AUTO_MERGE')):
        return 'pr_or_merge'
    if code.startswith(('REMOTE_', 'GITHUB_', 'BRANCH_PROTECTION')):
        return 'remote_observation'
    if code.startswith(('PUSH_', 'BASE_', 'BRANCH_', 'FORCE_')):
        return 'push_validation'
    if code.startswith('WORKTREE_'):
        return 'worktree_validation'
    return 'command_validation'


def _source_for_code(code: str) -> str:
    if code in {'HOST_PERMISSION_DENIED'}:
        return 'HOST_PERMISSION'
    if code.startswith('AUTHORITY_'):
        return 'HUMAN_AUTHORITY'
    if code.startswith(('REMOTE_', 'GITHUB_', 'REQUIRED_CHECKS_', 'PR_')):
        return 'GITHUB_OR_REMOTE_OBSERVATION'
    if code == 'PROTECTION_EVIDENCE_UNAVAILABLE':
        return 'GITHUB_API_EVIDENCE'
    if code.startswith('ISSUER_'):
        return 'HUMAN_AUTHORITY'
    return 'AIPS_POLICY'


def _blocking_rule_id(code: str) -> str:
    return code


def runtime_binding(cwd: Path, *, candidate_sha: str, target_ref: str, mode: str) -> dict[str, str]:
    """Safe candidate/runtime observations shared by Prepare and native Hooks."""
    identity_value = identity(cwd)
    module_root = Path(__file__).resolve().parents[1]
    try:
        version = (module_root / 'VERSION').read_text(encoding='utf-8').strip()
        revision = git(module_root, 'rev-parse', 'HEAD^{commit}')
    except (OSError, PublicationError):
        version, revision = 'UNKNOWN', 'UNKNOWN'
    safe = {
        'worktree_id': identity_value['worktree_id'],
        'repository_id': identity_value['repository_id'],
        'candidate_sha': candidate_sha if re.fullmatch(r'[0-9a-f]{40,64}', candidate_sha) else 'UNKNOWN',
        'target_ref': target_ref if re.fullmatch(r'refs/heads/[A-Za-z0-9._/-]{1,200}', target_ref) else 'UNKNOWN',
        'mode': mode if mode in {'personal', 'high_assurance'} else 'UNKNOWN',
        'runtime_version': version if re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version) else 'UNKNOWN',
        'runtime_revision': revision if re.fullmatch(r'[0-9a-f]{40,64}', revision) else 'UNKNOWN',
    }
    safe['binding_fingerprint'] = digest(safe)
    return safe


def worktree_dirty_details(root: Path) -> dict[str, Any]:
    """Return safe repository-relative status paths; never read file contents."""
    proc = subprocess.run(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
                          cwd=root, capture_output=True, timeout=15, check=False)
    if proc.returncode:
        raise PublicationError('worktree state unavailable', 'WORKTREE_STATE_UNAVAILABLE', phase='worktree_validation')
    groups: dict[str, list[str]] = {'staged': [], 'modified': [], 'deleted': [], 'untracked': []}
    entries = proc.stdout.split(b'\0')
    index = 0
    while index < len(entries):
        record = entries[index]
        index += 1
        if not record:
            continue
        xy = record[:2].decode('ascii', errors='replace')
        path = record[3:]
        if 'R' in xy or 'C' in xy:
            index += 1  # The following NUL-delimited field is the old path.
        value = os.fsdecode(path).replace('\r', ' ').replace('\n', ' ')
        value = re.sub(r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b', '[REDACTED]', value)
        value = value[:300]
        if xy == '??':
            groups['untracked'].append(value)
        else:
            if xy[0] != ' ':
                groups['staged'].append(value)
            if 'D' in xy:
                groups['deleted'].append(value)
            elif xy[1] != ' ':
                groups['modified'].append(value)
    for values in groups.values():
        values.sort()
    return {'status': 'DIRTY' if any(groups.values()) else 'CLEAN', 'paths': groups,
            'path_count': sum(map(len, groups.values())),
            'next_step': 'Review the listed paths and decide what belongs to the candidate; preserve unknown files. No files were changed.'}


def publication_mode(config_path: Path | None = None) -> str:
    """Select personal mode only when the fixed administrator trust root is absent."""
    config_path = config_path or CONFIG
    try:
        info = config_path.lstat()
    except FileNotFoundError:
        return 'personal'
    except OSError as exc:
        raise PublicationError('publication mode configuration unavailable', 'AUTHORITY_CONFIG_INVALID') from exc
    if not stat.S_ISREG(info.st_mode):
        raise PublicationError('publication mode configuration must be a regular file', 'AUTHORITY_CONFIG_INVALID')
    return 'high_assurance'


def _personal_base(root: Path, operation: str, argv: list[str]) -> str:
    """Resolve a locally available exact merge base for personal-mode scope checks."""
    remote = 'origin'
    urls = git(root, 'remote', 'get-url', '--all', remote).splitlines()
    push_urls = git(root, 'remote', 'get-url', '--push', '--all', remote).splitlines()
    if len(urls) != 1 or len(push_urls) != 1 or urls[0] != push_urls[0]:
        raise PublicationError('personal publication requires one matching origin fetch and push URL', reason_code='REMOTE_CONFIGURATION_INVALID')
    default_branch = _remote_default_branch(root, urls[0])
    default_tip = _tip(root, urls[0], 'refs/heads/' + default_branch)
    if not default_tip or not re.fullmatch(r'[0-9a-f]{40,64}', default_tip):
        raise PublicationError('remote default branch tip unavailable', reason_code='REMOTE_BRANCH_UNAVAILABLE')
    if operation == 'gh_pr_create' and _option(argv, '--base') != default_branch:
        raise PublicationError('personal PRs must target the remote default branch', reason_code='PR_BASE_MISMATCH')
    try:
        git(root, 'cat-file', '-e', default_tip + '^{commit}')
    except PublicationError as exc:
        raise PublicationError('fetch the current remote default branch before personal publication', 'BASE_OBJECT_MISSING') from exc
    return default_tip


def _remote_default_branch(root: Path, url: str) -> str:
    response = subprocess.run(['git', 'ls-remote', '--symref', '--', url, 'HEAD'],
                              cwd=root, capture_output=True, text=True, timeout=15, check=False)
    match = re.search(r'^ref: refs/heads/([A-Za-z0-9_./-]+)\tHEAD$', response.stdout, re.MULTILINE)
    if response.returncode or not match:
        raise PublicationError('remote default branch unavailable', reason_code='REMOTE_BRANCH_UNAVAILABLE')
    return match.group(1)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(value: Any) -> str:
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def run(cwd: Path, *argv: str) -> str:
    proc = subprocess.run(list(argv), cwd=cwd, capture_output=True, text=True, timeout=15, check=False)
    if proc.returncode:
        raise PublicationError('required repository observation failed', 'REMOTE_OBSERVATION_FAILED')
    return proc.stdout.strip()


def git(cwd: Path, *argv: str) -> str:
    return run(cwd, 'git', *argv)


def identity(cwd: Path) -> dict[str, str]:
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    if any(os.environ.get(key) for key in ['GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS']):
        raise PublicationError('alternate Git environment unsupported', reason_code='ALTERNATE_GIT_ENVIRONMENT')
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
        raise PublicationError('explicit full target ref required', 'INVALID_TARGET_REF')
    try:
        git(cwd, 'check-ref-format', value)
    except PublicationError as exc:
        raise PublicationError('invalid explicit target ref', 'INVALID_TARGET_REF') from exc
    return value


def _tip(cwd: Path, remote: str, ref: str) -> str | None:
    lines = git(cwd, 'ls-remote', '--refs', '--', remote, ref).splitlines()
    matches = [line.split('\t')[0] for line in lines if line.endswith('\t' + ref)]
    if len(matches) > 1:
        raise PublicationError('ambiguous remote ref', reason_code='REMOTE_REF_AMBIGUOUS')
    return matches[0] if matches else None


def _option(argv: list[str], option: str) -> str:
    if argv.count(option) != 1:
        raise PublicationError('explicit unique ' + option + ' required', 'PR_METADATA_INCOMPLETE')
    index = argv.index(option)
    if index + 1 >= len(argv) or argv[index + 1].startswith('-'):
        raise PublicationError('missing ' + option + ' value', 'PR_METADATA_INCOMPLETE')
    return argv[index + 1]


def validate_action_form(operation: str, argv: list[str]) -> None:
    """Reject unsupported executable/subcommand wrappers before candidate inspection."""
    expected = {
        'git_push': ['git', 'push'],
        'git_tag': ['git', 'tag'],
        'gh_pr_create': ['gh', 'pr', 'create'],
        'gh_pr_merge': ['gh', 'pr', 'merge'],
        'gh_release_create': ['gh', 'release', 'create'],
    }
    if (operation not in expected or not argv or argv[:len(expected[operation])] != expected[operation]
            or any('$' in word or '`' in word or '\0' in word for word in argv)):
        raise PublicationError('use a supported standalone literal publication command',
                               'COMMAND_FORM_UNSUPPORTED', phase='command_validation')


def action(cwd: Path, operation: str, argv: list[str], base: str, *, personal: bool = False) -> dict[str, Any]:
    """Observe a supported standalone literal command; implicit/multi-target pushes deny."""
    validate_action_form(operation, argv)
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    head = git(root, 'rev-parse', 'HEAD^{commit}')
    if not re.fullmatch(r'[0-9a-f]{40,64}', base):
        raise PublicationError('explicit base commit SHA required', reason_code='BASE_SHA_INVALID')
    try:
        git(root, 'merge-base', '--is-ancestor', base, head)
    except PublicationError as exc:
        raise PublicationError('base is not a candidate ancestor', 'BASE_NOT_ANCESTOR') from exc
    if git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise PublicationError('publication requires a clean worktree', 'WORKTREE_DIRTY',
                               context={'worktree': root, 'candidate_sha': head}, phase='candidate_validation')
    diff = subprocess.run(['git', 'diff', '--binary', base, head, '--'], cwd=root, capture_output=True, timeout=15, check=False)
    files = subprocess.run(['git', 'diff', '--name-only', '-z', base, head, '--'], cwd=root, capture_output=True, timeout=15, check=False)
    if diff.returncode or files.returncode:
        raise PublicationError('candidate diff unavailable', reason_code='CANDIDATE_DIFF_UNAVAILABLE')
    result: dict[str, Any] = {
        **identity(root), 'branch': git(root, 'branch', '--show-current'),
        'candidate_commit': head, 'base_commit': base,
        'files': sorted(os.fsdecode(item) for item in files.stdout.split(b'\0') if item),
        'diff_digest': 'sha256:' + hashlib.sha256(diff.stdout).hexdigest(),
        'operations': [operation], 'argv': argv,
    }
    if not result['branch']:
        raise PublicationError('publication requires an explicit feature branch', reason_code='BRANCH_NOT_ALLOWLISTED')
    remote = 'origin'
    force = False
    delete = False
    if operation == 'git_push':
        if argv[:2] != ['git', 'push']:
            raise PublicationError('use a standalone git push without wrappers/global options', 'COMMAND_FORM_UNSUPPORTED')
        args = argv[2:]
        flags = []
        while args and args[0].startswith('-'):
            flag, args = args[0], args[1:]
            if flag not in {'--force', '-f', '--delete'} and not flag.startswith('--force-with-lease='):
                detail_code = ('PUSH_UPSTREAM_OPTION_UNSUPPORTED'
                               if flag in {'-u', '--set-upstream'} else 'PUSH_OPTION_UNSUPPORTED')
                raise PublicationError('unsupported push option', 'COMMAND_FORM_UNSUPPORTED',
                                       detail_code=detail_code)
            flags.append(flag)
        if len(args) != 2 or not re.fullmatch(r'[A-Za-z0-9_.-]+', args[0]):
            raise PublicationError('one named remote and one explicit refspec required', reason_code='PUSH_METADATA_INVALID')
        remote, spec = args
        if personal:
            fetch_urls = git(root, 'remote', 'get-url', '--all', 'origin').splitlines()
            push_urls = git(root, 'remote', 'get-url', '--push', '--all', 'origin').splitlines()
            if remote != 'origin' or len(fetch_urls) != 1 or len(push_urls) != 1 or fetch_urls[0] != push_urls[0]:
                raise PublicationError('personal mode permits only the verified single origin remote', reason_code='REMOTE_NOT_ALLOWED')
        delete = '--delete' in flags or spec.startswith(':')
        if '--delete' in flags:
            source, target = None, _ref(root, spec)
        else:
            if spec.count(':') != 1:
                raise PublicationError('explicit source SHA:full-ref required', 'PUSH_SOURCE_NOT_EXACT_SHA')
            source, target = spec.split(':')
            target = _ref(root, target)
            if source and source != head:
                raise PublicationError('push source must be exact current candidate SHA', 'PUSH_SOURCE_NOT_EXACT_SHA')
            source = source or None
        force = any(flag in {'-f', '--force'} or flag.startswith('--force-with-lease=') for flag in flags)
        result.update(source_commit=source, refspec=spec)
        if personal:
            branch = result['branch']
            if (delete or target != 'refs/heads/' + branch or
                    branch in {'main', 'master', 'trunk', 'develop', 'production', 'release'} or
                    not branch.startswith(PERSONAL_BRANCH_PREFIXES)):
                raise PublicationError('personal mode permits only the current engineering branch', reason_code='PUSH_TARGET_BRANCH_MISMATCH',
                    context={'candidate_sha': head, 'worktree_id': result['worktree_id'],
                             'target_ref': target, 'mode': 'personal'}, phase='push_validation')
        for key in ['push.followTags', 'remote.' + remote + '.mirror']:
            proc = subprocess.run(['git', 'config', '--bool', '--get', key], cwd=root, capture_output=True, text=True, timeout=5, check=False)
            if proc.returncode not in {0, 1} or proc.stdout.strip() == 'true':
                raise PublicationError('implicit multi-ref publication configuration forbidden', reason_code='PUSH_METADATA_INVALID')
    elif operation == 'git_tag':
        # Local mutations still require exact authorization; read-only forms are classified elsewhere.
        if argv[:2] != ['git', 'tag'] or len(argv) != 3 or argv[2].startswith('-'):
            raise PublicationError('supported tag mutation is git tag <name>; other forms require separate review', reason_code='TAG_OPERATION_REQUIRES_REVIEW')
        target = _ref(root, 'refs/tags/' + argv[2])
        result['local_tag_oid'] = git(root, 'tag', '--list', argv[2]) or None
    else:
        if os.environ.get('GH_HOST', 'github.com') != 'github.com':
            raise PublicationError('unsupported GitHub host', reason_code='GITHUB_HOST_UNSUPPORTED')
        expected = {'gh_pr_create': ['gh', 'pr', 'create'], 'gh_pr_merge': ['gh', 'pr', 'merge'],
                    'gh_release_create': ['gh', 'release', 'create']}[operation]
        if argv[:3] != expected:
            raise PublicationError('use standalone gh command with explicit --repo', reason_code='COMMAND_FORM_UNSUPPORTED')
        # A second spelling such as -R/--repo= or -B may override inspected fields.
        valued = {'--repo', '--body', '--body-file'}
        switches = set()
        position = 3
        if operation == 'gh_pr_create':
            _option(argv, '--title')
            if ('--body' in argv) == ('--body-file' in argv):
                raise PublicationError('exactly one explicit PR body or body file required', 'PR_METADATA_INCOMPLETE')
            valued |= {'--head', '--base', '--title', '--label', '--assignee', '--reviewer', '--milestone', '--project'}
            switches = {'--draft'}
        elif operation == 'gh_pr_merge':
            valued |= {'--match-head-commit', '--subject'}
            switches = {'--merge', '--squash', '--rebase'}
            position = 4
            if len(argv) < 4 or not argv[3].isdigit():
                raise PublicationError('merge PR number missing', 'MERGE_PR_NUMBER_REQUIRED')
            if any(flag in argv for flag in ('--admin', '--delete-branch')):
                raise PublicationError('prohibited merge option', 'MERGE_OPTION_FORBIDDEN')
            if '--match-head-commit' not in argv:
                raise PublicationError('exact candidate SHA required', 'MERGE_HEAD_PIN_REQUIRED')
            if sum(flag in argv for flag in switches) != 1:
                raise PublicationError('exactly one explicit merge method required', 'MERGE_METHOD_REQUIRED')
            if argv.count('--auto') > 1:
                raise PublicationError('duplicate automatic merge option is unsupported', reason_code='AUTO_MERGE_INVALID')
        else:
            valued = {'--repo', '--title', '--notes', '--notes-file'}
            switches = {'--verify-tag', '--draft', '--prerelease'}
            position = 4
            if '--verify-tag' not in argv:
                raise PublicationError('release creation requires an existing verified remote tag', reason_code='RELEASE_TAG_INVALID')
        while position < len(argv):
            flag = argv[position]
            if flag in valued:
                if position + 1 >= len(argv) or argv[position + 1].startswith('-'):
                    raise PublicationError('missing explicit option value', reason_code='PUBLICATION_OPTION_INVALID')
                position += 2
            elif flag in switches or operation == 'gh_pr_merge' and flag == '--auto':
                position += 1
            else:
                raise PublicationError('unsupported or ambiguous GitHub publication option',
                                       'MERGE_OPTION_FORBIDDEN' if operation == 'gh_pr_merge' else 'COMMAND_FORM_UNSUPPORTED')
        repo = _option(argv, '--repo')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise PublicationError('explicit GitHub owner/repository required', reason_code='PR_METADATA_INCOMPLETE')
        url = git(root, 'remote', 'get-url', '--push', remote)
        ssh_prefix = 'git' + '@' + 'github.com:'
        if url.removesuffix('.git') not in {'https://github.com/' + repo, ssh_prefix + repo}:
            raise PublicationError('gh repository does not match Git remote', reason_code='REPOSITORY_MISMATCH')
        result['github_repo'] = repo
        if operation == 'gh_pr_create':
            if (_option(argv, '--head') != result['branch'] or
                    personal and not result['branch'].startswith(PERSONAL_BRANCH_PREFIXES)):
                raise PublicationError('PR head must be the bound candidate branch', reason_code='PR_HEAD_MISMATCH')
            target = _ref(root, 'refs/heads/' + _option(argv, '--base'))
            if _tip(root, remote, 'refs/heads/' + result['branch']) != head:
                raise PublicationError('remote PR head differs from candidate', reason_code='PR_HEAD_MISMATCH')
        elif operation == 'gh_pr_merge':
            if len(argv) < 4 or not argv[3].isdigit() or any(flag in argv for flag in ['--admin', '--delete-branch']):
                raise PublicationError('explicit PR number and checked merge required', 'MERGE_OPTION_FORBIDDEN')
            if _option(argv, '--match-head-commit') != head:
                raise PublicationError('merge must pin the exact candidate SHA', 'MERGE_HEAD_MISMATCH')
            pr = json.loads(run(root, 'gh', 'pr', 'view', argv[3], '--repo', repo, '--json',
                                'url,state,isDraft,mergeable,headRefOid,headRefName,baseRefOid,baseRefName'))
            if pr.get('state') != 'OPEN' or pr.get('isDraft') is True:
                raise PublicationError('PR must be open and ready for review', reason_code='PR_NOT_MERGEABLE')
            if pr['headRefOid'] != head:
                raise PublicationError('PR head differs from candidate', reason_code='PR_HEAD_MISMATCH')
            if personal and (pr.get('headRefName') != result['branch'] or
                             not result['branch'].startswith(PERSONAL_BRANCH_PREFIXES)):
                raise PublicationError('personal PR merge must use the current allowlisted engineering branch', reason_code='BRANCH_NOT_ALLOWLISTED')
            if pr.get('mergeable') != 'MERGEABLE':
                raise PublicationError('PR mergeability is not confirmed', reason_code='PR_MERGEABILITY_UNKNOWN')
            result['pr_base_commit'] = pr['baseRefOid']
            target = _ref(root, 'refs/heads/' + pr['baseRefName'])
            if pr['baseRefName'] != _remote_default_branch(root, url):
                raise PublicationError('personal PR merge must target the remote default branch', reason_code='PR_BASE_MISMATCH')
            from publication_diagnostics import (
                classify_required_checks,
                required_checks_policy,
            )
            from repository_governance_snapshot import build_snapshot, query_github_api

            def read_policy_api(endpoint: str) -> dict[str, Any]:
                try:
                    return query_github_api(root, endpoint)
                except subprocess.TimeoutExpired:
                    return {'returncode': 1, 'http_status': None, 'payload': None,
                            'endpoint': endpoint, 'error_class': 'NETWORK', 'error_message': None}
            policy_snapshot = build_snapshot(repo, pr['baseRefName'], read_policy_api)
            policy_observation = required_checks_policy(policy_snapshot)
            if policy_observation['status'] != 'CONFIGURED':
                reason_code = policy_observation['reason_code'] or 'REQUIRED_CHECKS_POLICY_UNVERIFIED'
                error = PublicationError('Required Checks policy is not verifiably configured', reason_code,
                                         phase='protection_policy_evidence')
                error.context.update({'policy_sources': policy_observation.get('sources', {})})
                raise error
            checks = subprocess.run(
                ['gh', 'pr', 'checks', argv[3], '--repo', repo, '--required', '--json', 'bucket,name'],
                cwd=root, capture_output=True, text=True, timeout=30, check=False,
            )
            try:
                required_checks = json.loads(checks.stdout) if checks.returncode in {0, 8} else None
            except json.JSONDecodeError:
                required_checks = None
            check_observation = classify_required_checks(required_checks, returncode=checks.returncode,
                                                          stderr=checks.stderr,
                                                          required_policy=policy_observation['checks'])
            if check_observation['status'] != 'PASS':
                raise PublicationError('required PR checks are missing or not all passing',
                                        check_observation['reason_code'] or 'REQUIRED_CHECKS_INVALID')
            result['merge_confirmation'] = {
                'pr_number': int(argv[3]),
                'pr_url': pr['url'],
                'head_sha': pr['headRefOid'],
                'base_branch': pr['baseRefName'],
                'base_sha': pr['baseRefOid'],
                'required_checks': check_observation['checks'],
                'auto_merge': '--auto' in argv,
            }
        else:
            if len(argv) < 4 or argv[3].startswith('-'):
                raise PublicationError('explicit release tag required', reason_code='RELEASE_TAG_INVALID')
            target = _ref(root, 'refs/tags/' + argv[3])
            if git(root, 'rev-parse', target + '^{commit}') != head:
                raise PublicationError('release tag must point to the exact candidate commit', reason_code='RELEASE_TAG_INVALID')
            result['tag_oid'] = git(root, 'rev-parse', target)
        inputs = {}
        for opt in ['--body-file', '--notes-file']:
            if opt in argv:
                path = Path(_option(argv, opt))
                if str(path) == '-':
                    raise PublicationError('stdin publication text cannot be bound', reason_code='PUBLICATION_INPUT_UNBOUND')
                path = (path if path.is_absolute() else cwd / path).resolve(strict=True)
                inputs[opt] = {'path': str(path), 'digest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}
        result['file_inputs'] = inputs
    url = git(root, 'remote', 'get-url', '--push', remote)
    # Several push URLs cause several publications, which this single-target contract rejects.
    if len(git(root, 'remote', 'get-url', '--push', '--all', remote).splitlines()) != 1:
        raise PublicationError('exactly one push URL required', reason_code='REMOTE_CONFIGURATION_INVALID')
    parsed = urlparse(url)
    if parsed.password or (parsed.scheme in {'http', 'https'} and parsed.username):
        raise PublicationError('credential-bearing remote URL forbidden', reason_code='CREDENTIAL_BEARING_REMOTE')
    result.update(remote=remote, remote_url=url, target_ref=target,
                  expected_remote_oid=_tip(root, url, target), force=force, delete=delete)
    result['remote_state_enforcement'] = 'server_lease' if operation == 'git_push' else 'preexecution_observation'
    if operation == 'git_push':
        expected_lease = '--force-with-lease=' + target + ':' + (result['expected_remote_oid'] or '')
        allowed_flags = ([], [expected_lease]) if personal else ([expected_lease], [expected_lease, '--delete'])
        if flags not in allowed_flags:
            raise PublicationError('one explicit target/tip force-with-lease required; unconditional force forbidden', reason_code='FORCE_WITH_LEASE_REQUIRED')
    if operation == 'gh_pr_merge' and result['pr_base_commit'] != result['expected_remote_oid']:
        raise PublicationError('PR base differs from current remote tip', reason_code='BASE_CHANGED')
    if operation == 'gh_release_create' and result['tag_oid'] != result['expected_remote_oid']:
        raise PublicationError('local and remote release tag differ', reason_code='RELEASE_TAG_INVALID')
    return result


def validate_personal_action(cwd: Path, operation: str, argv: list[str]) -> dict[str, Any]:
    """Validate personal publication; PR merge returns an exact per-call confirmation binding."""
    validate_action_form(operation, argv)
    if operation not in PERSONAL_PUBLICATION_OPERATIONS:
        raise PublicationError('operation is unavailable in personal publication mode', reason_code='ASSURANCE_MODE_BLOCKED')
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    base = _personal_base(root, operation, argv)
    from check_secret_leakage import DEFAULT_POLICY, load_policy, scan_candidate
    try:
        policy, _ = load_policy(DEFAULT_POLICY)
    except OSError as exc:
        raise PublicationError('mandatory candidate secret-scan policy is unavailable',
            'SECRET_SCAN_POLICY_UNAVAILABLE', phase='content_scan.policy_load',
            context={'error_class': type(exc).__name__, 'component': 'check_secret_leakage'}) from exc
    except Exception as exc:
        from check_secret_leakage import ScanError
        safe = exc.safe_diagnostic() if isinstance(exc, ScanError) else {
            'reason_code': 'SECRET_SCAN_INTERNAL_ERROR', 'phase': 'content_scan.policy_load',
            'component': 'check_secret_leakage', 'error_class': type(exc).__name__}
        raise PublicationError('mandatory candidate secret-scan policy is invalid',
            safe['reason_code'], phase=safe['phase'],
            context={'error_class': safe['error_class'], 'component': safe['component']}) from exc
    try:
        scan_diagnostics: list[dict[str, Any]] = []
        findings, blockers, _, _ = scan_candidate(root, base, 'HEAD', policy, diagnostics=scan_diagnostics)
    except Exception as exc:
        from check_secret_leakage import ScanError
        if isinstance(exc, ScanError):
            safe = exc.safe_diagnostic()
        else:
            safe = {'reason_code': 'SECRET_SCAN_INTERNAL_ERROR', 'phase': 'content_scan.internal',
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
    return action(root, operation, argv, base, personal=True)


def proposal(cwd: Path, operation: str, argv: list[str], base: str) -> dict[str, Any]:
    scope = action(cwd, operation, argv, base)
    return {'version': 2, 'approval': {'status': 'PENDING'}, 'scope': scope,
            'proposal': {'fingerprint': digest(scope)},
            'evidence': {'validation': [], 'unresolved': []}}


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise PublicationError('UTC timestamp required', reason_code='AUTHORITY_TIME_INVALID')
    try:
        date = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PublicationError('invalid UTC timestamp', reason_code='AUTHORITY_TIME_INVALID') from exc
    if date.tzinfo is None or date.utcoffset().total_seconds() != 0:
        raise PublicationError('UTC timestamp required', reason_code='AUTHORITY_TIME_INVALID')
    return date


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublicationError('authority redirects are forbidden', reason_code='AUTHORITY_REDIRECT_BLOCKED')


class Authority:
    def __init__(self, config: dict[str, Any]):
        if config.get('version') != 1:
            raise PublicationError('invalid authority configuration', reason_code='AUTHORITY_ENDPOINT_INVALID')
        self.config = config
        parsed = urlparse(config.get('endpoint', ''))
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise PublicationError('authority requires a credential-free HTTPS endpoint', reason_code='AUTHORITY_ENDPOINT_INVALID')
        self.issuers = config.get('issuers') or {}
        if not isinstance(self.issuers, dict) or not self.issuers:
            raise PublicationError('trusted issuer keys required', reason_code='AUTHORITY_KEY_MISSING')

    def verify_signature(self, doc: dict[str, Any]) -> None:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        try:
            signature = doc['signature']
            if signature['algorithm'] != 'ed25519':
                raise PublicationError('unsupported signature algorithm', reason_code='AUTHORITY_SIGNATURE_INVALID')
            public = base64.b64decode(self.issuers[signature['issuer_key_id']], validate=True)
            raw = base64.b64decode(signature['value_b64'], validate=True)
            message = {key: value for key, value in doc.items() if key != 'signature'}
            Ed25519PublicKey.from_public_bytes(public).verify(raw, canonical(message))
        except (KeyError, ValueError, TypeError, InvalidSignature) as exc:
            raise PublicationError('untrusted or invalid publication signature', reason_code='AUTHORITY_SIGNATURE_INVALID') from exc

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
            raise PublicationError('oversized authority response', reason_code='AUTHORITY_RESPONSE_TOO_LARGE')
        assertion = json.loads(raw)
        self.verify_signature(assertion)
        expected = {'version': 1, 'nonce': nonce, 'grant_id': record['approval']['id'],
                    'record_digest': request['record_digest'], 'action_digest': request['action_digest'],
                    'result': 'CONSUMED' if consume else 'AVAILABLE'}
        if any(assertion.get(key) != value for key, value in expected.items()):
            raise PublicationError('authority denied, stale or replayed grant', reason_code='AUTHORITY_GRANT_DENIED')
        expires = _timestamp(assertion.get('expires_at'))
        now = datetime.now(UTC)
        if not 0 < (expires - now).total_seconds() <= 60:
            raise PublicationError('authority assertion expired or exceeds 60 seconds', reason_code='AUTHORITY_GRANT_EXPIRED')


def protected_file(value: Path) -> Path:
    path = value.resolve(strict=True)
    for item in [path, *path.parents]:
        info = item.stat()
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
            raise PublicationError('authority configuration must be administrator-owned and not Agent-writable', reason_code='AUTHORITY_CONFIG_WRITABLE')
    return path


def configured_authority() -> Authority:
    # Fixed administrator-owned path; an Agent-owned external YAML is not a trust root.
    path = protected_file(CONFIG)
    if any(os.access(item, os.W_OK) for item in [path, *path.parents]):
        raise PublicationError('authority config/path is writable by this Agent, including ACL or privileged access', reason_code='AUTHORITY_CONFIG_WRITABLE')
    return Authority(yaml.safe_load(path.read_text()))


def verify(record: dict[str, Any], operation: str, cwd: Path, argv: list[str] | None,
           *, consume: bool = False, authority: Authority | None = None) -> None:
    if record.get('version') != 2 or operation not in PUBLICATION_OPERATIONS:
        raise PublicationError('signed v2 publication grant required; reissue legacy approvals', reason_code='AUTHORITY_LEGACY_GRANT')
    authority = authority or configured_authority()
    authority.verify_signature(record)
    approval = record.get('approval') or {}
    scope = record.get('scope') or {}
    if approval.get('status') != 'APPROVED' or not all(approval.get(key) for key in ['id', 'approved_by', 'approved_at', 'expires_at']):
        raise PublicationError('complete Human-issued approval required', reason_code='AUTHORITY_GRANT_INCOMPLETE')
    now = datetime.now(UTC)
    issued, expires = _timestamp(approval['approved_at']), _timestamp(approval['expires_at'])
    if issued > now or expires <= now or not 0 < (expires - issued).total_seconds() <= 3600:
        raise PublicationError('approval expired, future-dated or exceeds one hour', reason_code='AUTHORITY_GRANT_EXPIRED')
    if record.get('proposal', {}).get('fingerprint') != digest(scope):
        raise PublicationError('proposal scope fingerprint mismatch', reason_code='AUTHORITY_SCOPE_MISMATCH')
    if (record.get('evidence') or {}).get('unresolved'):
        raise PublicationError('unresolved publication evidence', reason_code='PUBLICATION_EVIDENCE_UNRESOLVED')
    if not (record.get('evidence') or {}).get('validation'):
        raise PublicationError('publication validation evidence required', reason_code='AUTHORITY_VALIDATION_MISSING')
    if not argv:
        raise PublicationError('actual command required; stored command cannot supply execution scope', reason_code='PUBLICATION_COMMAND_UNBOUND')
    actual = action(cwd, operation, argv, scope.get('base_commit', ''))
    if actual != scope:
        raise PublicationError('actual publication action differs from approved scope', reason_code='AUTHORITY_ACTION_MISMATCH')
    authority.check(record, consume)
