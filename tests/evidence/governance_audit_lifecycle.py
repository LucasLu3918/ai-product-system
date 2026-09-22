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

def openssl_supports_ed25519() -> bool:
    binary = shutil.which("openssl")
    if not binary:
        return False
    try:
        result = subprocess.run([binary, "list", "-public-key-algorithms"], capture_output=True,
                                text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and "ED25519" in result.stdout.upper()

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
        evidence=root/"validation-report.json"; evidence.write_text('{"status":"PASS","run":1187}\n',encoding="utf-8")
        bundle=root/"bundle"; external_anchor=root/"retained-anchor.json"
        made=run("bundle-create","--ledger",str(ledger),"--output",str(bundle),
                 "--repository-revision","b"*40,"--evidence",f"validation={evidence}",
                 "--anchor-output",str(external_anchor))
        require(made.returncode==0,f"bundle create failed: {made.stdout} {made.stderr}")
        checked=run("bundle-verify","--bundle",str(bundle),"--anchor",str(external_anchor))
        require(checked.returncode==0,"external-anchor bundle verify failed")
        manifest_text=(bundle/"MANIFEST.json").read_text(encoding="utf-8")
        require(str(root) not in manifest_text,"bundle manifest leaked source absolute path")
        require("local-test-secret-do-not-persist" not in manifest_text,"bundle manifest leaked HMAC material")
        bundled_evidence=bundle/"evidence"/"validation"
        original_evidence=bundled_evidence.read_bytes(); bundled_evidence.write_text("tampered\n",encoding="utf-8")
        require(run("bundle-verify","--bundle",str(bundle),"--anchor",str(external_anchor)).returncode!=0,
                "tampered bundle evidence must fail")
        bundled_evidence.write_bytes(original_evidence)
        bundled_ledger=bundle/"AUDIT.jsonl"; original_ledger=bundled_ledger.read_bytes()
        bundled_ledger.write_text(bundled_ledger.read_text(encoding="utf-8").splitlines()[0]+"\n",encoding="utf-8")
        require(run("bundle-verify","--bundle",str(bundle),"--anchor",str(external_anchor)).returncode!=0,
                "bundled tail truncation must fail against retained anchor/manifest")
        bundled_ledger.write_bytes(original_ledger)
        original_anchor=external_anchor.read_bytes(); anchor_doc=json.loads(original_anchor.decode("utf-8")); anchor_doc["events"]=999
        external_anchor.write_text(json.dumps(anchor_doc),encoding="utf-8")
        require(run("bundle-verify","--bundle",str(bundle),"--anchor",str(external_anchor)).returncode!=0,
                "tampered external anchor must fail")
        external_anchor.write_bytes(original_anchor)
        if openssl_supports_ed25519():
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
            signed_bundle=root/"signed-bundle"; signed_anchor=root/"signed-anchor.json"
            require(run("bundle-create","--ledger",str(signed),"--output",str(signed_bundle),
                        "--repository-revision","c"*40,"--checkpoint-public-key",f"checkpoint-q3={public}",
                        "--anchor-output",str(signed_anchor)).returncode==0,"signed bundle create failed")
            require(run("bundle-verify","--bundle",str(signed_bundle),"--anchor",str(signed_anchor)).returncode==0,
                    "signed bundle offline verify failed")
            require(not any(p.name=="private.pem" for p in signed_bundle.rglob("*")),"private signing key must not be bundled")
            bundled_pub=signed_bundle/"public-keys"/"checkpoint-q3.pem"; bundled_pub.write_bytes(otherpub.read_bytes())
            require(run("bundle-verify","--bundle",str(signed_bundle),"--anchor",str(signed_anchor)).returncode!=0,
                    "tampered bundled public key must fail")
    print("governance audit lifecycle PASS"); return 0

if __name__ == "__main__": raise SystemExit(main())
