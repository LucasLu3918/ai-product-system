#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "governance_audit.py"

def run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = dict(os.environ)
    if env: merged.update(env)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=merged, timeout=30)

def event(path: Path, event_type: str, occurred_at: str, result: str) -> None:
    path.write_text(json.dumps({
        "version": 1, "event_type": event_type, "occurred_at": occurred_at,
        "actor": {"type": "human_or_system", "id": "test-actor"},
        "authority": {"source": "test", "approval_id": "approval-1"},
        "binding": {"approval_scope_fingerprint": "sha256:" + ("1" * 64), "candidate_commit": "a" * 40,
                    "branch": "feature/test", "operation": event_type.lower(), "result": result,
                    "evidence_digests": ["sha256:" + ("2" * 64)]}
    }), encoding="utf-8")

def require(condition: bool, message: str) -> None:
    if not condition: raise AssertionError(message)

def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); first = root/"first.json"; second = root/"second.json"; third = root/"third.json"
        event(first, "HUMAN_APPROVAL_GRANTED", "2026-09-21T00:00:00Z", "APPROVED")
        event(second, "SECURITY_REVIEW_COMPLETED", "2026-09-21T00:01:00Z", "PASS")
        event(third, "PRODUCTION_VERIFIED", "2026-09-21T00:02:00Z", "PASS")
        ledger = root/"AUDIT.jsonl"
        require(run("append","--ledger",str(ledger),"--event",str(first)).returncode == 0, "first append failed")
        require(run("append","--ledger",str(ledger),"--event",str(second)).returncode == 0, "second append failed")
        verify = run("verify","--ledger",str(ledger))
        verify_doc = json.loads(verify.stdout)
        require(verify.returncode == 0 and verify_doc["events"] == 2, "plain verify failed")
        expected_head = verify_doc["chain_head"]
        truncated = root/"truncated.jsonl"
        truncated.write_text(ledger.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
        require(run("verify","--ledger",str(truncated),"--expected-chain-head",expected_head,
                    "--expected-events","2").returncode != 0, "anchored tail truncation must fail")
        rows = ledger.read_text(encoding="utf-8").splitlines(); changed=json.loads(rows[0]); changed["binding"]["result"]="MUTATED"
        rows[0]=json.dumps(changed,separators=(",",":"),sort_keys=True); tampered=root/"tampered.jsonl"
        tampered.write_text("\n".join(rows)+"\n",encoding="utf-8")
        require(run("verify","--ledger",str(tampered)).returncode != 0, "tampering must fail")
        reordered=root/"reordered.jsonl"; reordered.write_text("\n".join(reversed(ledger.read_text().splitlines()))+"\n")
        require(run("verify","--ledger",str(reordered)).returncode != 0, "reordering must fail")
        env={"TEST_AUDIT_KEY":"local-test-secret-do-not-persist"}; hledger=root/"HMAC.jsonl"
        require(run("append","--ledger",str(hledger),"--event",str(first),"--hmac-key-env","TEST_AUDIT_KEY","--hmac-key-id","key-q3",env=env).returncode==0,"HMAC append1 failed")
        require(run("append","--ledger",str(hledger),"--event",str(second),"--hmac-key-env","TEST_AUDIT_KEY","--hmac-key-id","key-q3",env=env).returncode==0,"HMAC append2 failed")
        require(run("verify","--ledger",str(hledger),"--hmac","key-q3=TEST_AUDIT_KEY","--require-auth-verification",env=env).returncode==0,"HMAC verify failed")
        require("local-test-secret-do-not-persist" not in hledger.read_text(), "secret leaked")
        require(run("verify","--ledger",str(hledger),"--hmac","key-q3=WRONG",env={"WRONG":"wrong"}).returncode!=0,"wrong HMAC must fail")
        if shutil.which("openssl"):
            private=root/"private.pem"; public=root/"public.pem"
            subprocess.run(["openssl","genpkey","-algorithm","ED25519","-out",str(private)],check=True,timeout=15)
            subprocess.run(["openssl","pkey","-in",str(private),"-pubout","-out",str(public)],check=True,timeout=15)
            signed=root/"SIGNED.jsonl"
            require(run("append","--ledger",str(signed),"--event",str(third),"--checkpoint-private-key",str(private),
                        "--checkpoint-public-key",str(public),"--checkpoint-key-id","checkpoint-q3").returncode==0,"signed append failed")
            require(run("verify","--ledger",str(signed),"--checkpoint-public-key",f"checkpoint-q3={public}",
                        "--require-checkpoint-verification").returncode==0,"signed verify failed")
            other=root/"other.pem"; otherpub=root/"other.pub.pem"
            subprocess.run(["openssl","genpkey","-algorithm","ED25519","-out",str(other)],check=True,timeout=15)
            subprocess.run(["openssl","pkey","-in",str(other),"-pubout","-out",str(otherpub)],check=True,timeout=15)
            require(run("verify","--ledger",str(signed),"--checkpoint-public-key",f"checkpoint-q3={otherpub}").returncode!=0,"wrong public key must fail")
    print("governance audit lifecycle PASS"); return 0

if __name__ == "__main__": raise SystemExit(main())
