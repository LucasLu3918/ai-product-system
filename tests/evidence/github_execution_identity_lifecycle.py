"""Signed fixtures test trust checks; no fixture authorizes real cleanup."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from branch_hygiene import BranchHygieneError, download_proposal, manifest_from_proposal
from github_execution_identity import (
    ISSUER,
    IdentityError,
    cleanup_identity,
    verify_token,
)


def main() -> int:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_numbers()

    def encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode().rstrip("=")

    keys = {"keys": [{"kid": "fixture", "kty": "RSA", "n": encode(public.n.to_bytes(256, "big")), "e": encode(public.e.to_bytes(3, "big"))}]}
    claims = {"iss": ISSUER, "aud": "bound-proposal", "repository": "owner/repo", "ref": "refs/heads/main",
              "sha": "a" * 40, "workflow_sha": "a" * 40, "event_name": "workflow_dispatch", "ref_protected": "true",
              "workflow_ref": "owner/repo/.github/workflows/branch-hygiene.yml@refs/heads/main",
              "nbf": 990, "iat": 990, "exp": 1200, "actor": "maintainer", "run_id": "123"}

    def sign(body: dict, algorithm: str = "RS256") -> str:
        value = encode(json.dumps({"alg": algorithm, "kid": "fixture"}).encode()) + "." + encode(json.dumps(body).encode())
        return value + "." + encode(private.sign(value.encode(), padding.PKCS1v15(), hashes.SHA256()))

    assert verify_token(sign(claims), keys, repository="owner/repo", baseline="a" * 40, audience="bound-proposal", now=1000)["actor"] == "maintainer"
    for altered in ({"aud": "other-proposal"}, {"ref_protected": False}, {"event_name": "push"}, {"ref": "refs/heads/feature"},
                    {"sha": "b" * 40}, {"workflow_sha": "b" * 40}, {"exp": 999}, {"iss": "https://untrusted.invalid"},
                    {"repository": "other/repo"}, {"workflow_ref": "owner/repo/.github/workflows/other.yml@refs/heads/main"}):
        try:
            verify_token(sign({**claims, **altered}), keys, repository="owner/repo", baseline="a" * 40, audience="bound-proposal", now=1000)
        except IdentityError:
            pass
        else:
            raise AssertionError(f"identity mismatch must fail: {list(altered)}")
    for token in (sign(claims, "none"), sign(claims)[:-20] + "broken", "not-a-jwt"):
        try:
            verify_token(token, keys, repository="owner/repo", baseline="a" * 40, audience="bound-proposal", now=1000)
        except IdentityError:
            pass
        else:
            raise AssertionError("invalid signature/algorithm must fail")
    with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "ACTIONS_ID_TOKEN_REQUEST_URL": "https://untrusted.invalid/token", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture"}):
        try:
            cleanup_identity("owner/repo", "a" * 40, "bound-proposal")
        except IdentityError:
            pass
        else:
            raise AssertionError("spoofed runner flags must not establish trusted identity")
    proposal = {"version": 1, "status": "PROPOSED", "target": "main", "generated_against_main_sha": "a" * 40,
                "authorization": {"authorized": False, "scope": "proposal_only", "requires_explicit_human_approval": True},
                "branches": [{"branch": "codex/merged", "expected_sha": "b" * 40, "merged_pr": 1,
                              "merged_at": "2026-10-07T00:00:00Z", "integrated_into_main": True}]}
    proposal["proposal_fingerprint"] = "sha256:" + hashlib.sha256(json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    fingerprint = proposal["proposal_fingerprint"]
    manifest = manifest_from_proposal(proposal, fingerprint, "maintainer")
    assert manifest["baseline_main_sha"] == "a" * 40 and manifest["authorization"]["one_time"]
    import yaml

    def archive(name: str) -> bytes:
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as output:
            output.writestr(name, yaml.safe_dump({"cleanup_proposal": proposal}))
        return data.getvalue()

    def evidence(_repository: str, endpoint: str) -> dict:
        if endpoint.endswith("/artifacts?per_page=100"):
            return {"artifacts": [{"id": 1, "name": "branch-cleanup-proposal-123", "expired": False, "size_in_bytes": 500}]}
        return {"status": "completed", "conclusion": "success", "head_branch": "main", "head_sha": "a" * 40,
                "path": ".github/workflows/branch-hygiene.yml", "event": "workflow_dispatch"}

    with patch("branch_hygiene.github_json", side_effect=evidence), patch("branch_hygiene.subprocess.run", return_value=subprocess.CompletedProcess([], 0, archive("branch-hygiene.yaml"))):
        assert download_proposal("owner/repo", "123", fingerprint) == proposal
    with patch("branch_hygiene.github_json", side_effect=evidence), patch("branch_hygiene.subprocess.run", return_value=subprocess.CompletedProcess([], 0, archive("../escape.yaml"))):
        try:
            download_proposal("owner/repo", "123", fingerprint)
        except BranchHygieneError:
            pass
        else:
            raise AssertionError("unexpected archive paths must fail before extraction")
    try:
        manifest_from_proposal(proposal, "sha256:" + "0" * 64, "maintainer")
    except BranchHygieneError:
        pass
    else:
        raise AssertionError("dispatch must bind the exact human-approved fingerprint")
    print("GITHUB EXECUTION IDENTITY LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
