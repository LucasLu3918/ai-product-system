from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from scripts.deterministic_scheduler import schedule
from review_packet import build_packet
from tests.validation.review_isolation_contracts import report


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "patch.diff").write_text("diff --git a/x b/x\n", encoding="utf-8")
        candidate = report()["candidate"]
        packet = build_packet(root, {
            "version": 1,
            "candidate": candidate,
            "sources": [{"class": "diff", "path": "patch.diff"}],
        })
        evidence = report()
        evidence["packet"]["fingerprint"] = packet["packet_fingerprint"]
        evidence["packet"]["source_classes"] = packet["context_policy"]["allowed_classes"]
        evidence["context_policy"]["packet_fingerprint"] = packet["packet_fingerprint"]
        evidence["context_policy"]["allowed_classes"] = packet["context_policy"]["allowed_classes"]
        evidence["runtime_attestation"]["packet_fingerprint"] = packet["packet_fingerprint"]

        graph = {
            "version": 1, "plan_id": "fixture", "base_revision": candidate["base_sha"], "max_parallel": 2,
            "tasks": [
                {"id": "implement", "read_only": False, "write_set": ["src"], "change_boundary": ["src"]},
                {"id": "review", "dependencies": ["implement"], "read_only": True, "write_set": [],
                 "review": {"mode": "INDEPENDENT_REVIEW", "review_of_task": "implement",
                            "required": True, "context_inheritance": "none", "allowed_context_classes": ["diff"]}},
            ],
        }
        state = {"plan_id": "fixture", "tasks": {
            "implement": {"status": "COMPLETE", "execution_id": "impl-1", "candidate": candidate},
            "review": {"status": "COMPLETE", "execution_id": "review-1", "review_evidence": evidence},
        }}
        result = schedule(graph, state)
        assert result["review_statuses"]["review"]["status"] == "UNVERIFIED"
        assert "review" in result["failed"]

        state["tasks"]["review"]["review_evidence"] = {**evidence, "runtime_attestation": {"runtime": "unavailable"}}
        blocked = schedule(graph, state)
        assert blocked["review_statuses"]["review"]["status"] == "UNVERIFIED"
        assert "review" in blocked["failed"]


if __name__ == "__main__":
    main()
    print("review isolation lifecycle: PASS")
