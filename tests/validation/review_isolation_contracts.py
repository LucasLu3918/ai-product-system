from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from review_evidence import evaluate_evidence
from review_packet import ReviewPacketError, build_packet


SHA = "a" * 40
HASH = "sha256:" + "b" * 64

active_matrix = yaml.safe_load((ROOT / ".aips/review/CORE_CHANGE_TEST_MATRIX.yaml").read_text(encoding="utf-8"))
assert active_matrix["review_evidence"]["required"] is False, "independent-review enforcement must remain disabled by default"


def report() -> dict:
    return {
        "version": 1,
        "mode": "INDEPENDENT_REVIEW",
        "review_of_task": "implement",
        "candidate": {"base_sha": SHA, "head_sha": "c" * 40, "changed_files_hash": HASH},
        "packet": {"fingerprint": HASH, "source_classes": ["diff"]},
        "context_policy": {
            "inheritance": "none", "allowed_classes": ["diff"], "packet_fingerprint": HASH,
            "denied_classes": ["implementation_transcript", "private_reasoning", "scratchpad", "raw_model_trace"],
        },
        "permissions": {"read_only": True, "write_set": []},
        "implementer_execution_id": "impl-1",
        "reviewer_execution_id": "review-1",
        "runtime_attestation": {
            "execution_identity": "VERIFIED", "context_isolation": "VERIFIED",
            "read_only_authority": "VERIFIED", "runtime": "fixture",
            "receipt_ref": "fixture://receipt", "receipt_sha256": HASH,
            "issuer_key_id": "fixture-key", "signature_algorithm": "ed25519", "signature_b64": "AA==",
            "packet_fingerprint": HASH,
        },
        "unresolved_blocking_findings": 0,
    }


def main() -> None:
    candidate = report()["candidate"]
    assert evaluate_evidence(report(), candidate)["reason_codes"] == ["trusted_runtime_attestation_verifier_unavailable"]
    trusted_fixture_verifier = lambda attestation: attestation.get("receipt_ref") == "fixture://receipt"
    assert evaluate_evidence(report(), candidate, attestation_verifier=trusted_fixture_verifier)["status"] == "VERIFIED"
    assert evaluate_evidence({**report(), "reviewer_execution_id": "impl-1"}, candidate, attestation_verifier=trusted_fixture_verifier)["status"] == "FAILED"
    assert evaluate_evidence({**report(), "permissions": {"read_only": False, "write_set": ["x"]}}, candidate, attestation_verifier=trusted_fixture_verifier)["status"] == "FAILED"
    assert evaluate_evidence({**report(), "runtime_attestation": {"runtime": "unknown"}}, candidate)["status"] == "UNVERIFIED"
    assert evaluate_evidence({**report(), "candidate": {**candidate, "head_sha": "d" * 40}}, candidate)["status"] == "STALE"
    assert evaluate_evidence({**report(), "private_reasoning": "must not be included"}, candidate)["status"] == "FAILED"

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "diff.patch").write_text("diff --git a/a b/a\n", encoding="utf-8")
        manifest = {
            "version": 1,
            "candidate": candidate,
            "sources": [{"class": "diff", "path": "diff.patch"}],
        }
        packet = build_packet(root, manifest)
        assert packet["context_policy"]["inheritance"] == "none"
        assert packet["sources"][0]["class"] == "diff"
        try:
            build_packet(root, {**manifest, "sources": [{"class": "implementation_transcript", "path": "diff.patch"}]})
        except ReviewPacketError:
            pass
        else:
            raise AssertionError("non-allowlisted transcript source was accepted")
        try:
            build_packet(root, {**manifest, "sources": [{"class": "diff", "path": "../outside"}]})
        except ReviewPacketError:
            pass
        else:
            raise AssertionError("path traversal source was accepted")
        (root / "secret.txt").write_text("sk_live_" + "A" * 32, encoding="utf-8")
        try:
            build_packet(root, {**manifest, "sources": [{"class": "diff", "path": "secret.txt"}]})
        except ReviewPacketError:
            pass
        else:
            raise AssertionError("secret-bearing evidence was accepted")
        card_fixture = " ".join(("4111", "1111", "1111", "1111"))
        (root / "pii.txt").write_text(card_fixture, encoding="utf-8")
        try:
            build_packet(root, {**manifest, "sources": [{"class": "diff", "path": "pii.txt"}]})
        except ReviewPacketError:
            pass
        else:
            raise AssertionError("PII-bearing evidence was accepted")


if __name__ == "__main__":
    main()
    print("review isolation contracts: PASS")
