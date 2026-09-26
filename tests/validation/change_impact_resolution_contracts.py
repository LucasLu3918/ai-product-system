from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from project_intelligence import _impact_evidence_digest, validate_impact_document


def _closed_unknown(evidence: list[dict[str, str]]) -> dict:
    return {
        "id": "impact-coverage-boundary",
        "description": "The repository-wide graph is incomplete outside the reviewed Change Impact subsystem.",
        "disposition": "ACCEPTED_LIMITATION",
        "resolution": "Use the reviewed seed-scoped traversal evidence and keep global graph coverage partial.",
        "evidence": evidence,
        "review": {
            "status": "APPROVED",
            "reviewer": "human",
            "approval_reference": "user-approved-impact-review-2026-09-26",
            "reviewed_at": "2026-09-26T04:06:50Z",
        },
    }


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="aips-impact-resolution-contract-") as temp:
        root = Path(temp)
        evidence_path = root / "reviewed.md"
        evidence_path.write_text("The bounded subsystem is covered.\n", encoding="utf-8")
        digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        file_evidence = [{"kind": "repository_file", "path": "reviewed.md", "sha256": digest}]
        approved = {
            "status": "IMPLEMENTATION_APPROVED",
            "change": {},
            "scope_review": {"status": "APPROVED", "approval_reference": "scope-approval", "approved_at": "2026-09-26"},
            "unknowns": [_closed_unknown(file_evidence)],
        }
        if not validate_impact_document(approved, root)["valid"]:
            errors.append("current in-root evidence and explicit Human review should pass")
        for disposition in ("RESOLVED", "MITIGATED"):
            candidate = {**approved, "unknowns": [{**_closed_unknown(file_evidence), "disposition": disposition}]}
            if not validate_impact_document(candidate, root)["valid"]:
                errors.append(f"{disposition} with current evidence and Human review should pass")

        unsupported = {**approved, "unknowns": [{**_closed_unknown(file_evidence), "disposition": "WAIVED"}]}
        if not any("unsupported disposition" in error for error in validate_impact_document(unsupported, root)["errors"]):
            errors.append("unknown dispositions outside the bounded enum must fail")

        invalid_timestamp = {**approved, "unknowns": [{**_closed_unknown(file_evidence), "review": {
            "status": "APPROVED", "reviewer": "human", "approval_reference": "review", "reviewed_at": "yesterday",
        }}]}
        if not any("ISO-8601 timestamp with timezone" in error for error in validate_impact_document(invalid_timestamp, root)["errors"]):
            errors.append("Human review timestamps must be timezone-qualified ISO-8601")

        duplicate_ids = {**approved, "unknowns": [_closed_unknown(file_evidence), _closed_unknown(file_evidence)]}
        if not any("duplicates an existing unknown id" in error for error in validate_impact_document(duplicate_ids, root)["errors"]):
            errors.append("structured unknown IDs must be unique")

        legacy = {**approved, "unknowns": ["legacy unknown"]}
        if not any("legacy string unknown remains unresolved" in error for error in validate_impact_document(legacy, root)["errors"]):
            errors.append("legacy strings must continue to fail closed")

        opened = {**approved, "unknowns": [{**_closed_unknown(file_evidence), "disposition": "OPEN"}]}
        if not any("remains open" in error for error in validate_impact_document(opened, root)["errors"]):
            errors.append("OPEN dispositions must block implementation approval")

        stale = {**approved, "unknowns": [_closed_unknown([{**file_evidence[0], "sha256": "0" * 64}])]}
        if not any("SHA-256 does not match" in error for error in validate_impact_document(stale, root)["errors"]):
            errors.append("stale file evidence must be rejected")

        escaped = {**approved, "unknowns": [_closed_unknown([{"kind": "repository_file", "path": "../outside.md", "sha256": digest}])]}
        if not any("repository-relative" in error for error in validate_impact_document(escaped, root)["errors"]):
            errors.append("parent-directory evidence paths must be rejected")

        symlink = root / "escape.md"
        outside = Path(tempfile.gettempdir()) / "aips-impact-resolution-outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        try:
            symlink.symlink_to(outside)
            linked = {**approved, "unknowns": [_closed_unknown([{"kind": "repository_file", "path": "escape.md", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}])]}
            if not any("outside the project root" in error for error in validate_impact_document(linked, root)["errors"]):
                errors.append("symlink evidence escaping the project root must be rejected")
        finally:
            outside.unlink(missing_ok=True)

        traversal = {
            "status": "COMPLETE",
            "truncated": False,
            "unresolved": [],
            "architecture_graph": {
                "status": "COMPLETE",
                "coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
                "coverage_scope_ids": ["bounded-impact-scope"],
            },
        }
        approved_with_traversal = {**approved, "traversal": traversal, "unknowns": [_closed_unknown([{
            "kind": "traversal", "scope_id": "bounded-impact-scope", "sha256": _impact_evidence_digest(traversal),
        }])]}
        if not validate_impact_document(approved_with_traversal, root)["valid"]:
            errors.append("matching complete seed-scoped traversal evidence should pass")

        incomplete_traversal = {
            **traversal, "architecture_graph": {**traversal["architecture_graph"], "status": "BOUNDED_WITH_UNKNOWNS"},
        }
        incomplete_scope = {**approved, "traversal": incomplete_traversal, "unknowns": [_closed_unknown([{
            "kind": "traversal", "scope_id": "bounded-impact-scope", "sha256": _impact_evidence_digest(incomplete_traversal),
        }])]}
        if not any("scoped traversal graph must be complete" in error for error in validate_impact_document(incomplete_scope, root)["errors"]):
            errors.append("seed-scoped traversal evidence must have a complete graph status")

        mismatch = {**approved_with_traversal, "unknowns": [_closed_unknown([{
            "kind": "traversal", "scope_id": "other-scope", "sha256": _impact_evidence_digest(traversal),
        }])]}
        if not any("scope_id is not present" in error for error in validate_impact_document(mismatch, root)["errors"]):
            errors.append("traversal evidence for a different scope must be rejected")

        stale_traversal = {**approved_with_traversal, "unknowns": [_closed_unknown([{
            "kind": "traversal", "scope_id": "bounded-impact-scope", "sha256": "sha256:" + "0" * 64,
        }])]}
        if not any("does not match the recorded traversal" in error for error in validate_impact_document(stale_traversal, root)["errors"]):
            errors.append("stale traversal evidence digest must be rejected")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: Change Impact disposition contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
