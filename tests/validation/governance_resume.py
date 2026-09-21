from pathlib import Path
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import yaml

from .static_contracts import ROOT, errors, load_yaml, roles, skills, scenarios, version

# v0.11 enforceable governance contract
approval_template = ROOT / "templates/governance/APPROVAL_RECORD.yaml"
if not approval_template.exists():
    errors.append("Missing v0.11 Approval Record template")
else:
    approval_doc = load_yaml(approval_template) or {}
    for key in ("approval", "proposal", "scope", "evidence"):
        if key not in approval_doc:
            errors.append(f"APPROVAL_RECORD.yaml missing top-level key: {key}")

adapter_contract = (ROOT / "harness/ADAPTER_CONTRACT.md").read_text(encoding="utf-8")
for phrase in ("Governance enforcement capability", "ADVISORY", "TOOL_GUARDED", "ENFORCED"):
    if phrase not in adapter_contract:
        errors.append(f"ADAPTER_CONTRACT.md missing governance enforcement contract: {phrase}")

turn_template = load_yaml(ROOT / "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml") or {}
if "governance_enforcement" not in (turn_template.get("runtime") or {}):
    errors.append("TURN_CONTEXT_MANIFEST runtime missing governance_enforcement")
if "resolution" not in turn_template:
    errors.append("TURN_CONTEXT_MANIFEST missing resolution metadata")

guard = ROOT / "scripts/governance_guard.py"
if not guard.exists():
    errors.append("Missing scripts/governance_guard.py")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(guard)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"governance_guard.py syntax failed: {compiled.stderr.strip()}")
    import importlib.util
    spec = importlib.util.spec_from_file_location("aips_governance_guard", guard)
    gg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gg)
    scope_a = {"branch":"release/test","remote":"origin","candidate_commit":"abc123","files":["b.txt","a.txt"],"boundaries":["governance"],"operations":["git_push"]}
    scope_b = {"operations":["git_push"],"boundaries":["governance"],"files":["a.txt","b.txt"],"candidate_commit":"abc123","remote":"origin","branch":"release/test"}
    if gg.fingerprint(scope_a) != gg.fingerprint(scope_b):
        errors.append("Approval fingerprint must be deterministic for set-like ordering")
    with tempfile.TemporaryDirectory() as tmp:
        ap = Path(tmp) / "approval.yaml"
        record = {"version":1,"approval":{"id":"test","type":"git_publish","status":"APPROVED","approved_by":"human","approved_at":"test"},"proposal":{"fingerprint":"sha256:test"},"scope":dict(scope_a),"evidence":{"validation":[],"unresolved":[]}}
        record["scope"]["fingerprint"] = gg.fingerprint(scope_a)
        ap.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        ok, reason, _ = gg.verify_record(ap, "git_push", Path(tmp), check_actual=False)
        if not ok:
            errors.append(f"Approval fingerprint should validate: {reason}")
        record["scope"]["files"].append("drift.txt")
        ap.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        ok, _, _ = gg.verify_record(ap, "git_push", Path(tmp), check_actual=False)
        if ok:
            errors.append("Approval fingerprint did not detect scope drift")

for n in range(96, 101):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")

gemini_hooks = json.loads((ROOT / "harness/adapters/gemini-cli/hooks/hooks.json").read_text(encoding="utf-8"))
if "BeforeTool" not in (gemini_hooks.get("hooks") or {}):
    errors.append("Gemini adapter missing BeforeTool governance guard")

# v0.12 durable run-state contract
run_protocol = ROOT / "orchestration/RUN_RESUME.md"
run_template = ROOT / "templates/workspace/RUN_CHECKPOINT.yaml"
run_helper = ROOT / "scripts/run_state.py"
for required in (run_protocol, run_template, run_helper):
    if not required.exists():
        errors.append(f"Missing v0.12 run-state artifact: {required.relative_to(ROOT)}")

if run_template.exists():
    doc = load_yaml(run_template) or {}
    for key in ("run_id", "protocol", "status", "current_step", "completed_steps", "waiting_for", "project", "updated_at"):
        if key not in doc:
            errors.append(f"RUN_CHECKPOINT.yaml missing key: {key}")

if run_helper.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(run_helper)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"run_state.py syntax failed: {compiled.stderr.strip()}")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        config = base / "config"
        project.mkdir()
        (project / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.email", "aips@example.invalid"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.name", "AIPS Test"], cwd=project, check=True)
        subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=project, check=True)
        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)

        cp = subprocess.run([sys.executable, str(run_helper), "checkpoint", "--project", str(project), "--run-id", "r1", "--protocol", "test", "--step", "implementation", "--completed-step", "planning", "--format", "json"], env=env, capture_output=True, text=True)
        if cp.returncode != 0:
            errors.append(f"Run checkpoint failed: {cp.stdout.strip()} {cp.stderr.strip()}")
        else:
            cp_doc = json.loads(cp.stdout)
            if cp_doc.get("mode") != "EPHEMERAL" or (project / ".ai").exists():
                errors.append("EPHEMERAL run checkpoint must not create project .ai")

        ev = subprocess.run([sys.executable, str(run_helper), "event", "--project", str(project), "--run-id", "r1", "--event", "validation_completed", "--status", "PASS", "--evidence", "TOKEN=supersecret", "--format", "json"], env=env, capture_output=True, text=True)
        if ev.returncode != 0:
            errors.append(f"Run event failed: {ev.stdout.strip()} {ev.stderr.strip()}")
        else:
            ev_doc = json.loads(ev.stdout)
            event_text = Path(ev_doc["events"]).read_text(encoding="utf-8")
            if "supersecret" in event_text or "[REDACTED]" not in event_text:
                errors.append("Run EVENTS.jsonl must redact obvious secret-like evidence")

        current = subprocess.run([sys.executable, str(run_helper), "resume", "--project", str(project), "--run-id", "r1", "--format", "json"], env=env, capture_output=True, text=True)
        if current.returncode != 0 or json.loads(current.stdout).get("status") != "CURRENT":
            errors.append(f"Run resume should be CURRENT before revision drift: {current.stdout.strip()} {current.stderr.strip()}")

        (project / "README.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "change"], cwd=project, check=True)
        stale = subprocess.run([sys.executable, str(run_helper), "resume", "--project", str(project), "--run-id", "r1", "--format", "json"], env=env, capture_output=True, text=True)
        if stale.returncode != 0:
            errors.append(f"Run resume after drift failed: {stale.stdout.strip()} {stale.stderr.strip()}")
        else:
            stale_doc = json.loads(stale.stdout)
            if stale_doc.get("status") != "STALE" or stale_doc.get("requires_freshness_check") is not True:
                errors.append("Run resume must report STALE and require freshness check after revision drift")

for n in range(101, 106):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")



# v0.48 verifiable governance audit-chain contract
audit_protocol = ROOT / "orchestration/GOVERNANCE_AUDIT.md"
audit_template = ROOT / "templates/governance/AUDIT_EVENT.yaml"
audit_helper = ROOT / "scripts/governance_audit.py"
audit_evidence = ROOT / "tests/evidence/governance_audit_lifecycle.py"
for required in (audit_protocol, audit_template, audit_helper, audit_evidence):
    if not required.exists():
        errors.append(f"Missing v0.48 governance audit artifact: {required.relative_to(ROOT)}")
if audit_helper.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(audit_helper)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"governance_audit.py syntax failed: {compiled.stderr.strip()}")
if audit_evidence.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(audit_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"governance audit lifecycle syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(audit_evidence)], capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            errors.append(f"Governance audit lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")


# v0.49 portable governance audit bundle contract
audit_bundle_scenario = ROOT / "tests/scenarios/159-portable-governance-audit-bundle.md"
if not audit_bundle_scenario.exists():
    errors.append("Missing v0.49 portable governance audit bundle scenario")
if audit_helper.exists():
    audit_text = audit_helper.read_text(encoding="utf-8")
    for required_text in (
        "bundle-create",
        "bundle-verify",
        "MANIFEST.json",
        "ANCHOR.json",
        "repository_revision",
        "manifest_sha256",
        "require_checkpoint_verification=True",
    ):
        if required_text not in audit_text:
            errors.append(f"governance_audit.py missing portable bundle contract: {required_text}")
if audit_evidence.exists():
    evidence_text = audit_evidence.read_text(encoding="utf-8")
    for required_text in (
        "bundle-create",
        "bundle-verify",
        "tampered bundle evidence must fail",
        "bundled tail truncation must fail",
        "tampered bundled public key must fail",
    ):
        if required_text not in evidence_text:
            errors.append(f"governance audit lifecycle missing bundle evidence: {required_text}")
