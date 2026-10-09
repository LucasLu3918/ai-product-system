# Plan25 System Improvement Review

## Appropriateness

Appropriate as a staged, evidence-led program. The current `main` already contains much of the proposed machinery. The remaining work is primarily to close measured runtime, user-outcome and operational-evidence gaps. Reuse the existing capability owners and do not create parallel governance systems.

## User problem

The plan identifies gaps between configured capability and verified results: stable installation has no published stable tag; runtime protection is not proven across all named hosts; local image output has not been shown to meet real-use quality; Evolution signals may not reach useful decisions; and latency, cost, quality and maintenance outcomes need evidence.

## Proposed solution

Address all twelve areas in six ordered, independently reviewable PRs. First establish a current baseline in PR 0. Then close only the remaining evidence-backed gaps in release/runtime/diagnostics, creative acceptance, CI/quality, Evolution/performance/telemetry, and branch/dependency governance. Preserve existing full validation, report-only modes and Human decision boundaries.

## Existing coverage

1. **Stable Release:** readiness workflow and verified-tag installation policy exist; no stable tag or Release has been published. Readiness and installation recovery can be improved or verified without creating a tag.
2. **Runtime acceptance:** OpenCode has a version-bound native acceptance scenario; Governance remains `ADVISORY`. This does not establish equivalent behavior for every host/version or for Shell/MCP/out-of-process writes.
3. **Creative acceptance:** MFLUX/ComfyUI discovery, preflight, execution, provenance and recovery exist. Synthetic lifecycle evidence is not real inference, visual quality or human acceptance.
4. **Project Intelligence UX:** `aips project diagnose` and `scripts/project_diagnostics.py` already expose reason codes and safe next actions. Test first-use and recovery journeys; add no second Intelligence path.
5. **Evolution Radar:** collection, pre-analysis, effectiveness and provider-neutral handoff exist. Open monthly/quarterly Issues (#203, #199) need evidence review; analysis remains distinct from Human adoption.
6. **Selective CI:** full-run shadow and graduation evaluator exist. The policy requires at least 30 days, 30 unique PRs and zero false negatives; skipping remains disabled. Preserve full runs for Core, release and unknown changes.
7. **Quality / modules:** Plan21 and Plan24 already add modularization and quality ratchets. Ruff baseline is 758 historical findings; touched code must add none. Coverage is report-only. Refactor only measured hot spots.
8. **Runtime performance:** telemetry and runtime timing hooks exist, but no verified cross-host P50/P95 or comparable token measurements are established by this baseline.
9. **Observability:** privacy-limited telemetry projection exists, export is disabled, and cost stays `unknown`; no prices or usage should be inferred.
10. **Branch lifecycle:** branch-hygiene workflow and exact-SHA cleanup manifest exist in report-only mode. There are 113 remote branches; deletion remains separately approved.
11. **Diagnostics:** `aips doctor` and `aips project diagnose` exist. Improve evidence consistency or host-specific guidance only when tests show a real gap.
12. **Dependencies:** dependency policy exists and automatic merge is disabled. Seven open dependency PRs currently include behind/blocked candidates and failed repository checks; this review does not authorize merging them.

## Reuse / extension candidates

Use the existing release-readiness and version-tag policy; Runtime adapters and native acceptance scenarios; Creative Execution; Project Diagnostics; Evolution Radar and Effectiveness; Validation Shadow / Graduation; Quality Ratchet; Telemetry Export; Branch Hygiene; and Dependency Policy. Preserve existing CLI facades, report schemas, required checks and compatibility claims.

## Lower-layer alternative

Prefer deterministic lifecycle evidence, current reports and focused fixes in existing modules. Treat missing model, host, token or price evidence as `NOT_VERIFIED` / `unknown`; do not solve measurement gaps by adding a provider, telemetry vendor, global threshold, autonomous cleanup or new gate.

## Context / token cost

Keep new evidence bounded and on-demand. Persist aggregate counts, hashes, durations and stable reason codes only. Never store prompts, image payloads, secrets or chain-of-thought in reports or telemetry.

## Security / reliability

Keep runtime governance `ADVISORY` wherever interception is unverified. Do not weaken full validation or enable selective execution. Keep telemetry export opt-in and local by default. Do not download models, call paid providers, delete branches, merge unrelated dependency PRs, create tags/releases or alter protected repository settings as part of this program.

## Backward compatibility

Preserve CLI arguments and output shapes, existing bundle/profile schemas, Runtime action boundaries, required CI context `repository`, module facades and report-only behavior. Any additive schema change must be versioned. Unknown host/model combinations remain unverified.

## Scenario / test impact

Use the existing release, runtime, creative, diagnostic, Evolution, shadow-graduation, quality, telemetry, branch-hygiene and dependency lifecycles. Derive the exact test matrix from each PR's final Change Boundary. Synthetic tests must not be reported as real inference, visual acceptance, host interception or cost evidence. Every final PR requires documentation closure, secret scan and exact-candidate Integration Gate.

## Human docs impact

Update only the canonical installation, Harness, creative, Project Intelligence, Evolution, maintenance, telemetry, quality and dependency sections affected by verified behavior.

## Agent docs impact

Update only owning orchestration protocols, scenarios, schemas, inventories and projections. Generated capability/architecture projections remain derived from their canonical registry.

## Architecture diagram impact

- `docs/ARCHITECTURE.md`: likely N/A unless a verified flow or component boundary changes; justify per final PR.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: likely N/A for evidence-only work; review per final PR.
- Human SVG architecture/lifecycle diagrams: likely N/A unless a new flow is approved; verify against documentation impact output.

## Constitution impact

**NO.** The proposal preserves Human authority, truthfulness, scope integrity, protected safety boundaries and the separate Constitutional Change Gate.

## Additional optimization candidates

None included. New provider/framework work, model downloads, broad coverage thresholds, selective CI activation, automatic branch cleanup, dependency auto-merge and stable tag publication are deferred or excluded.

## Expected scope

All twelve plan25 areas, split into six PRs: PR 0 baseline, PR 1 release/runtime/diagnostics, PR 2 creative acceptance, PR 3 CI/quality, PR 4 Evolution/performance/telemetry, and PR 5 branch/dependency governance. An item already satisfied by current code may close with current evidence and no duplicate implementation. A real external action or human acceptance remains pending until its own exact candidate and approval are available.

## Risks

- A broad program can drift into duplicate features; each PR must show the remaining gap and preserve canonical owners.
- Local models or supported runtime binaries may be unavailable, leaving real-world evidence unverified.
- Selective CI, release publication, dependency merges and branch deletion have independent authority boundaries and remain outside this implementation scope.
- The complete Python 3.12 validation environment is now prepared and its runtime probe is ready; the exact-candidate Integration Gate remains pending.
