# System Maintenance

## Documentation Impact Gate

Every system change must assess downstream documentation and behavior before completion.

| Area | Update when affected |
|---|---|
| `AGENTS.md` | bootloader behavior or mandatory entry steps change |
| `SYSTEM.md` | routing, planning gates, precedence, context or completion behavior changes |
| `orchestration/*` | detailed execution/model/instruction/planning behavior changes |
| `docs/ARCHITECTURE.md` | runtime flow, planning flow, boundaries or update lifecycle changes |
| `README.md` | installation, structure or headline behavior changes |
| `USER_GUIDE.md` | user-facing commands/behavior changes |
| `examples/*` | a new behavior needs a practical example |
| `tests/scenarios/*` | routing/gate behavior changes or regressions need coverage |
| templates/schemas | persisted contract/state/planning-package shape changes |
| `VERSION` | release version changes |
| `CHANGELOG.md` | every released behavioral change |

If an item is not affected, mark it N/A during change review rather than editing it unnecessarily.

## Self-improvement / Constitution / publish approval

Changes to this system first pass `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

If Constitution semantics are affected, the Constitutional Change Gate must complete before implementation. Material system changes also require Core Change Approval.

Before remote publication, present the Git Publish Proposal. A material difference from the approved implementation/publication plan requires re-approval.

## Release checklist

1. Confirm System Improvement Review and applicable Constitutional/Core Change approvals.
2. Run `aips validate`.
3. Review the Documentation Impact Gate.
4. Confirm Mermaid diagrams match actual runtime/planning flow.
5. Confirm changed routing/gate behavior has scenario coverage.
6. Confirm planning templates match the Planning Package protocol if planning behavior changed.
6. Update `VERSION` using SemVer.
7. Update `CHANGELOG.md`.
8. Ensure the system working tree is clean before publishing.
9. Prefer independent review/PR for material system changes.

## Versioning

- MAJOR: incompatible governance/protocol/contract changes.
- MINOR: backward-compatible new behavior, role, skill, work mode, CLI capability or schema/planning extension.
- PATCH: clarification, typo or non-behavioral documentation fix.

Major updates are not auto-applied by `aips preflight` without explicit `--allow-major`.
