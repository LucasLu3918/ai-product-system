# PII Email Rule: Git Remote Grammar (pii.email.v2)

## System Improvement Review

- **Appropriateness:** Appropriate. `pii.email.v1` classifies the SSH/scp Git remote userinfo `git` + `@host:` as an email. Since Plan47 scans complete staged blobs for PII, any edit to a file that already contains a Git remote literal is blocked with `CONTENT_PII_BLOCKED`, even when the edited lines are unrelated.
- **User problem:** Contributors work around the detector by obfuscating the literal (`"git" + chr(64) + "github.com:"`). This is the second occurrence (`scripts/publication_transfer.py`, and now `scripts/publish_preflight.py` on the `deps-docs-impact` branch). Obfuscation makes the code harder to read and teaches agents to evade the scanner.
- **Proposed solution:** Fix the rule itself. A regex match is excluded from email findings only when it is exactly the Git SSH service userinfo of a Git remote in Git's own remote grammar. No exception record, path allowlist, configuration switch or approval bypass is added.
- **Existing coverage:** `scripts/content_safety.py` (`EMAIL_RE`, `scan_payload`, `_redact_text`) is the only email detector. Secret and history scanning (`check_secret_leakage`) do not use it and are untouched.
- **Reuse / lower-layer alternative:** Same module, same detector name, same deterministic regex approach. No parser or dependency. Git's documented remote syntax is the authority for the grammar.
- **Context / token cost:** None at runtime.
- **Security / reliability:** Secret detection is unchanged. PII exceptions remain impossible. The exclusion is narrow: local part exactly ASCII `git`, followed by Git remote grammar. Each regex match is evaluated independently, so a remote cannot hide an adjacent address. Fail-closed behavior is unchanged.
- **Backward compatibility:** `safe_emit`, finding shape, reason codes and CLI are unchanged. Email findings move from `pii.email.v1` to `pii.email.v2`. Redaction sinks will keep Git remotes in their output instead of redacting them.
- **Constitution impact:** NO.
- **Recommendation:** Proceed with Option A (below).
- **Additional optimization candidates (not in scope):** see "Observed but excluded".

## Purpose

Remove a deterministic false positive in a protected detector without weakening true-positive email detection and without adding a PII exception mechanism.

## Why this is a core change

`pii.email` blocks `git_commit`, `github_pr`, `release_notes` and `source_artifact` sinks. Plan47 explicitly placed "changing secret/PII detector semantics" out of its scope, so changing them needs its own approval.

## Root cause

```python
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
```

`\b` after the TLD is satisfied by `:`. The scp-like remote `git` + `@github.com:owner/repo.git` contains the substring `git` + `@github.com`, which is syntactically an address. Before Plan47 only added lines were relevant in practice. Plan47 rescans the full blob, so old literals block unrelated edits.

## Design

### Option A (recommended): Git remote grammar, `git` service user only

A match of `EMAIL_RE` is **not** reported as an email when its local part is exactly the ASCII string `git` (case-sensitive) **and** one of the following holds:

1. **scp-like remote (Git URL syntax `[user@]host:path`).**
   - The character before the match is the start of text, whitespace, a quote, a backtick, `(`, `[`, `=`, `<` or `,`.
   - The match is immediately followed by `:`. No whitespace is allowed.
   - After the colon, either:
     - a repository path: optional leading `~` or `/`, then segments made of `[A-Za-z0-9._~-]` plus template characters `{ } $ < >`, separated by `/`, ending at whitespace, a quote, a backtick, `)`, `]`, `,`, `;`, `>` or end of text; or
     - an empty path (a prefix literal such as `removeprefix("git` + `@github.com:")`), followed only by a quote, a backtick, a newline or end of text.
2. **SSH URL userinfo.** The text before the match ends with `ssh://`, `git+ssh://` or `ssh+git://`, and the match is followed by `/` or `:<port>/`.

Each `finditer` match is decided independently. Detection and redaction share one predicate.

Detector name stays `email`. The finding `rule_id` becomes `pii.email.v2`, so audit trails can tell the semantics changed.

### Option B (rejected): POSIX username grammar instead of literal `git`

Accept any lowercase POSIX username before `@` when the path is present. This would also exclude `alice` + `@corp.com:team/repo.git`. A personal login is personal data, and `alice` + `@corp.com:` is indistinguishable from a real address followed by a colon. Rejected as smuggling-prone.

### Option C (rejected): any address followed by a non-space after `:`

This would miss combolist leaks (`address:password`). Rejected.

### Option D (rejected): reserved/test-domain or path allowlist

This is an exemption mechanism, which is prohibited for PII. Rejected.

### Why the literal `git` is a grammar constraint, not an allowlist

`git` is the documented SSH service account of GitHub, GitLab, Bitbucket, Azure DevOps (`ssh.dev.azure.com`), Gitea/Forgejo/Codeberg, Sourcehut and Heroku. It is part of the remote syntax, not a person. A mailbox `git` + `@company.com` is a role address, not personal data. There is no configuration, path or fingerprint involved, and the constant cannot be extended without another reviewed rule version.

## False-positive / false-negative trade-off

| Case | v1 | v2 | Note |
|---|---|---|---|
| Git remote with service user `git` | FP | clean | Target fix |
| Remote with personal user (`alice` + `@host:repo`) | flagged | flagged | Kept on purpose (Option B rejected) |
| `git` + `@host: prose` (space after colon) | flagged | flagged | Prose, not remote grammar |
| `ssh://alice` + `@host/repo` | flagged | flagged | Only `git` userinfo excluded |
| `https://git` + `@github.com/...` | flagged | flagged | Not an SSH scheme |
| Real role mailbox `git` + `@corp.com:` in a quoted prefix | flagged | clean | **Accepted residual FN**: role address, not personal |

### Abuse analysis (can the exclusion smuggle an address?)

- Only the local part `git` can be excluded. Any other local part, including case variants (`Git`), prefixes (`xgit`), and confusables (`g` + U+0131 + `t`) is still reported, because the comparison is exact ASCII.
- An address placed after a remote (`git` + `@github.com:alice` + `@corp.com`) is a separate regex match and is still reported. Path characters exclude `@`, so the remote itself is not excluded in that case either.
- A remote followed by an address on the same line (`...:repo alice` + `@corp.com`) still reports the address.
- A determined author can always obfuscate an address (`chr(64)`, " at "). This scanner targets accidental disclosure, which v2 does not weaken for any local part other than `git`.

## Fixed corpus before / after (evaluated during proposal, read-only)

Experiment script kept outside the repository (scratchpad). It uses the exact v1 regex and a prototype of the v2 predicate.

**Positive (must be clean in v2):** prefix literal in `removeprefix`, `owner/repo.git`, nested GitLab groups, Bitbucket, Azure DevOps `v3/...`, Sourcehut `~user/repo`, Heroku `app.git`, f-string `{REPOSITORY}.git`, doc placeholder `<owner>/<repo>.git`, `ssh://` with and without port, `url = ...` config line, parenthesised remote. v1: 13/13 flagged. v2: 0/13 flagged.

**Negative (must stay flagged in v2):** prose address, address followed by `: ` in a sentence, combolist `address:password`, personal user in scp form, trailing-colon address, `git` remote followed by prose space, remote with an address in its path, remote followed by an address, `mailto:` role address, `Git` / `xgit` / dotless-i confusable, `ssh://` with personal user, `https://` userinfo, bare `git` address, comma-joined remote and address, `a` + `@b.com:`, `user.email=` config. v1: 19/19 flagged. v2: 19/19 flagged (the number of matches is unchanged except where the extra match was the excluded remote).

**Repository-wide comparison (1451 tracked files):** v1 = 25 matches, v2 = 24 matches. The only removed match is `scripts/publish_preflight.py:477`. All 24 remaining matches are fixture addresses on reserved test domains (RFC 2606 / RFC 6761) in `tests/`; they are unaffected (see "Observed but excluded").

The committed corpus must encode every address-shaped string in hex (as the Plan47 corpus does for malicious samples). Otherwise the corpus file blocks its own commit while the installed AIPS runtime still runs v1.

## Proposed Scope

### In scope

- `scripts/content_safety.py`: add a single `_is_git_remote_userinfo(text, match)` predicate and an `email_matches(text)` helper. Use it in `scan_payload` and `_redact_text`. Set `rule_id="pii.email.v2"` for email findings.
- `tests/test_content_safety.py`: positive and negative matrix, redaction parity, and a v1/v2 corpus comparison that fails if any negative sample becomes unflagged.
- `tests/fixtures/content-safety/corpus.json`: add `pii_email_git_remote_hex` and `pii_email_true_hex` lists (hex-encoded).
- `tests/scenarios/266-content-safety-injection-context.md` or a new focused scenario `267-pii-email-git-remote.md`, plus `tests/scenario_coverage.yaml`.
- Docs: `orchestration/CONTENT_SAFETY_BOUNDARY.md` (Detection boundaries: one sentence on Git remote grammar and "no PII exceptions"), `docs/human/SECURITY_ASSURANCE.md`, `CHANGELOG.md`, `VERSION` (0.83.0 → 0.83.1, or as version policy requires), and documentation sync/placement maps if the gate requires it.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` bound to the exact candidate.
- Revert existing workarounds, after the fix is in the same candidate:
  - `scripts/publication_transfer.py:33` `"git" + chr(64) + "github.com:"` → plain literal.
  - `tests/evidence/publication_transfer_lifecycle.py:111` `"git" + chr(64) + f"github.com:{REPOSITORY}.git"` → plain f-string.
  - The `scripts/publish_preflight.py:477` rewrite planned on `claude/deps-docs-impact-1d4bcd` (not yet present in that worktree): revert in whichever PR merges second.

### Out of scope

- Secret detection (`check_secret_leakage.py`), history scanning, sink policies in `config/content-safety.yaml`, exception schema (still injection-only).
- Any PII exemption mechanism, path or domain allowlist.
- The other `chr(64)` usages in tests. They build real address-shaped fixtures (`aips` + `@example.invalid`, `user.email` values, URL userinfo `user:secret` + `@...`), which v2 still flags. They stay.

### Observed but excluded (follow-up candidates, need separate decisions)

1. **Pre-existing Unicode false negative in v1:** an address whose local part is preceded by a non-ASCII letter (`é` + `alice` + `@example.com`) or starts with a confusable such as U+0261 is not detected at all, because `\b` does not fall between two word characters. v2 does not change this. Fixing it changes detection breadth and belongs in its own proposal.
2. **Latent full-blob blockers:** 24 test files contain reserved-test-domain fixture addresses. The next edit to any of them will be blocked by Plan47 full-blob scanning, which invites more `chr(64)` workarounds. Resolving this needs a policy decision (reserved-domain handling would be an exemption semantic), so it is not proposed here.

## Affected boundaries

| Boundary | Callers | Effect |
|---|---|---|
| Commit staged blob and message | `governance_guard.commit_safety`, `_commit_block` path checks | Git remote literals no longer block |
| Publication preview and plan | `publish_preflight.preview_content_safety`, `content_safety_plan` | Same |
| Publication authority diagnostics | `publication_authority` path filter | Same |
| Review packet, runtime policy | `review_packet`, `runtime_policy` (`source_artifact`) | Same |
| Redacting sinks | `governance_audit`, `gemini_observable_event_capture`, `project_intelligence` | Git remotes no longer redacted; real addresses still redacted |
| Candidate/history secret scan | `publication_authority` → `check_secret_leakage` | Unchanged (does not use email rule) |

### Secret / Credential Impact

Secrets required: NO. Secret scanning strength: unchanged. Leakage review: corpus and tests must use hex or `chr(64)`-built addresses only on reserved domains; findings never contain values (unchanged).

### Documentation / Diagrams

- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, SVG diagrams: N/A — no component, trust boundary or flow change.
- Content Safety Boundary and Security Assurance text: AFFECTED (detector semantics sentence).

## Test matrix

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Email detection rule | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | No UI |
| Redaction parity | YES | YES | YES | YES | N/A | YES | N/A | N/A | N/A | Library only |
| Commit Hook / diagnose | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Existing lifecycle |
| Publication preview/plan | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | — |
| Workaround reversal | YES | YES | YES | N/A | N/A | YES | N/A | N/A | N/A | Literal-only edits |
| Repository delivery | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Full Gate + exact-candidate scan |

Required cases:

- **Positive (clean):** every positive corpus row above, including the empty-path prefix in single, double and backtick quotes and at end of line.
- **Negative (flagged):** every negative corpus row above, plus: an address immediately followed by `:` in a sentence; an address embedded with a remote in one string; Unicode confusables of `git` (U+0131, U+0261, Cyrillic `і`, fullwidth `ｇ`); `Git`/`GIT`; percent-encoded `git%40host:`; `git` + `@host:` followed by `@` in the path.
- **Regression:** existing `test_content_safety`, `test_safety_diagnostics`, Plan47 corpus comparison, `publish_preflight_lifecycle`, `publication_transfer_lifecycle`.
- **Self-hosting check:** after reverting the workarounds, `aips safety diagnose commit` from the worktree runtime reports no PII for `scripts/publication_transfer.py` and `scripts/publish_preflight.py`.
- **Invariants:** a fixture secret in the same file still blocks; `config/content-safety-exceptions.yaml` still rejects any `pii.*` rule ID.

## Delivery note: installed runtime

The live Hook runs the installed copy at `~/.local/share/aips/system`, which keeps v1 until it is updated. The candidate commit that reverts the workarounds will be blocked by the installed v1 Hook. Implementation order therefore is:

1. Commit A: v2 rule, tests, hex corpus, docs (no plain remote literals added).
2. Update the installed runtime from the worktree only if the user approves (or keep the workarounds in this PR and revert them in a follow-up PR after release).
3. Commit B: revert workarounds.

Recommended: keep commit B in the same PR only if the user approves a local runtime update; otherwise defer commit B to a follow-up PR after merge and release.

## Rollback

Revert the PR. No persistent state, configuration or migration. If the workaround reversal already merged, the revert restores the `chr(64)` forms in the same commit.

## Risks

- Grammar too wide: mitigated by literal `git` local part, terminator rules and the negative corpus gate.
- Grammar too narrow: unusual remotes (for example a different service user) remain blocked. This is the conservative failure direction.
- Redaction behavior change in audit sinks: Git remote slugs become visible. Repository slugs are not personal data.

## Proposed Implementation Order

1. Add hex corpus and failing tests reproducing the false positive.
2. Implement the shared predicate; switch detection and redaction to it; bump the rule ID.
3. Run the corpus comparison, focused suites, docs closure.
4. Decide on runtime update and revert workarounds (commit B) as approved.
5. Bind the Core Change Test Matrix, run the full Integration Gate and exact-candidate scan.
6. Git Publish Approval Gate, then ask the user before any push or PR.

## Approval

Status: APPROVED (Option A; Commit A only)
Approved by: User
Approved at: 2026-10-20 (Asia/Taipei)
Approval record: User approved Option A directly in this session and asked to implement Commit A and run the full local Gate. Commit B (reverting the chr(64) workarounds) is excluded and deferred to a follow-up PR after merge and release, because no installed-runtime update was approved. Push and PR require the Git Publish Approval Gate and a fresh user confirmation.
Proposal fingerprint: sha256:978ea0c757eea78470d2a1112319130a7ca032d35f46ff7cf265e47735c113f4 (bytes before this section)
Scope fingerprint: sha256:93adab92aaf7cc81c7cd5b6fb5356b1e62a3d37de03e441ac0c94e0066cd3b88 (In scope section bytes)
