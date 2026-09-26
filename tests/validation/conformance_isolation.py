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

# v0.13 scenario conformance contract
conformance_protocol = ROOT / "orchestration/CONFORMANCE.md"
conformance_registry = ROOT / "tests/scenario_coverage.yaml"
conformance_helper = ROOT / "scripts/scenario_conformance.py"
for required in (conformance_protocol, conformance_registry, conformance_helper):
    if not required.exists():
        errors.append(f"Missing v0.13 conformance artifact: {required.relative_to(ROOT)}")

if conformance_helper.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(conformance_helper)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"scenario_conformance.py syntax failed: {compiled.stderr.strip()}")
    check = subprocess.run([sys.executable, str(conformance_helper), "check", "--format", "json"], capture_output=True, text=True)
    if check.returncode != 0:
        errors.append(f"Scenario conformance check failed: {check.stdout.strip()} {check.stderr.strip()}")
    else:
        check_doc = json.loads(check.stdout)
        cov = check_doc.get("coverage") or {}
        if cov.get("total") != len(scenarios) or cov.get("registered") != len(scenarios):
            errors.append("Scenario conformance total/registered count must match scenario inventory")
        if cov.get("uncovered") != 0:
            errors.append("Released scenario conformance registry must have no uncovered entries")
        if cov.get("manual") != 0 or cov.get("agent_eval") != 54 or cov.get("lifecycle") != 98 or cov.get("deterministic") != 27 or cov.get("automated") != 179:
            errors.append("current baseline must report manual=0, deterministic=27, lifecycle=98, agent_eval=54 and automated=179")

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        scenario_dir = temp / "scenarios"
        scenario_dir.mkdir()
        (scenario_dir / "001-test.md").write_text("# test\n", encoding="utf-8")
        bad_registry = temp / "coverage.yaml"
        bad_registry.write_text(yaml.safe_dump({
            "version": 1,
            "policy": {"release_requires": {"no_uncovered": True}},
            "scenarios": [],
        }, sort_keys=False), encoding="utf-8")
        missing = subprocess.run([
            sys.executable, str(conformance_helper), "check",
            "--registry", str(bad_registry),
            "--scenario-dir", str(scenario_dir),
            "--format", "json",
        ], capture_output=True, text=True)
        if missing.returncode == 0:
            errors.append("Conformance checker must fail when a Scenario has no registry entry")

for n in range(106, 111):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")

# v0.16 provider-neutral Agent Eval conformance
agent_eval_helper = ROOT / "scripts/agent_eval.py"
agent_eval_evidence = ROOT / "tests/evidence/agent_eval_framework.py"
for required in (agent_eval_helper, agent_eval_evidence):
    if not required.exists():
        errors.append(f"Missing v0.16 Agent Eval artifact: {required.relative_to(ROOT)}")
    else:
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(required)], capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"Agent Eval artifact syntax failed: {required.relative_to(ROOT)}: {compiled.stderr.strip()}")

if agent_eval_evidence.exists():
    framework = subprocess.run([sys.executable, str(agent_eval_evidence)], capture_output=True, text=True)
    if framework.returncode != 0:
        errors.append(f"Agent Eval framework evidence failed: {framework.stdout.strip()} {framework.stderr.strip()}")

if agent_eval_helper.exists():
    eval_check = subprocess.run([sys.executable, str(agent_eval_helper), "check", "--format", "json"], capture_output=True, text=True)
    if eval_check.returncode != 0:
        errors.append(f"Committed Agent Eval evidence failed: {eval_check.stdout.strip()} {eval_check.stderr.strip()}")
    else:
        eval_doc = json.loads(eval_check.stdout)
        summary = eval_doc.get("summary") or {}
        if summary.get("cases") != 54 or summary.get("results") != 54 or summary.get("passed") != 54 or summary.get("failed") != 0:
            errors.append("v0.18.3 committed Agent Eval baseline must contain 54 passing case/result pairs")

    cli_eval = subprocess.run(
        ["bash", str(ROOT / "bin/aips"), "conformance", "agent-eval", "check", "--format", "json"],
        capture_output=True,
        text=True,
    )
    if cli_eval.returncode != 0:
        errors.append(f"aips conformance agent-eval CLI failed: {cli_eval.stdout.strip()} {cli_eval.stderr.strip()}")

for n in range(121, 144):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")

# v0.22 Retrieval Quality Evaluation lifecycle
retrieval_quality_evaluation_evidence = ROOT / "tests/evidence/retrieval_quality_evaluation_lifecycle.py"
if not retrieval_quality_evaluation_evidence.exists():
    errors.append("Missing v0.22 Retrieval Quality Evaluation lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(retrieval_quality_evaluation_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Retrieval Quality Evaluation evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(retrieval_quality_evaluation_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Retrieval Quality Evaluation lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.21 Retrieval Intelligence lifecycle
git_path_integrity_evidence = ROOT / "tests/evidence/git_path_integrity_lifecycle.py"
if not git_path_integrity_evidence.exists():
    errors.append("Missing Git path integrity lifecycle evidence")
else:
    result = subprocess.run([sys.executable, str(git_path_integrity_evidence)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"Git path integrity lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

retrieval_intelligence_evidence = ROOT / "tests/evidence/retrieval_intelligence_lifecycle.py"
if not retrieval_intelligence_evidence.exists():
    errors.append("Missing v0.21 Retrieval Intelligence lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(retrieval_intelligence_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Retrieval Intelligence evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(retrieval_intelligence_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Retrieval Intelligence lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.18.3 Project Intelligence promotion lifecycle
project_intelligence_promotion_evidence = ROOT / "tests/evidence/project_intelligence_promotion_lifecycle.py"
if not project_intelligence_promotion_evidence.exists():
    errors.append("Missing v0.18.3 Project Intelligence promotion lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_intelligence_promotion_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Project Intelligence promotion evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(project_intelligence_promotion_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Project Intelligence promotion lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.18.2 monorepo lazy component Intelligence lifecycle
monorepo_lazy_evidence = ROOT / "tests/evidence/monorepo_lazy_intelligence_lifecycle.py"
if not monorepo_lazy_evidence.exists():
    errors.append("Missing v0.18.2 monorepo lazy Intelligence lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(monorepo_lazy_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Monorepo lazy Intelligence evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(monorepo_lazy_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Monorepo lazy Intelligence lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.18.1 runtime/project instruction composition lifecycle
instruction_context_evidence = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
if not instruction_context_evidence.exists():
    errors.append("Missing v0.18.1 instruction composition lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(instruction_context_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Instruction context evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(instruction_context_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Instruction context lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.18 Project Authority reconciliation lifecycle
project_authority_evidence = ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py"
if not project_authority_evidence.exists():
    errors.append("Missing v0.18 Project Authority reconciliation lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_authority_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Project Authority reconciliation evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(project_authority_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Project Authority reconciliation lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.15 canonical identity / resume integrity
identity_helper = ROOT / "scripts/aips_identity.py"
identity_evidence = ROOT / "tests/evidence/identity_resume_isolation.py"
for required in (identity_helper, identity_evidence):
    if not required.exists():
        errors.append(f"Missing v0.15 identity artifact: {required.relative_to(ROOT)}")
    else:
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(required)], capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"v0.15 identity artifact syntax failed: {required.relative_to(ROOT)}: {compiled.stderr.strip()}")
if identity_evidence.exists():
    result = subprocess.run([sys.executable, str(identity_evidence)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"Identity/resume/isolation evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

for n in range(116, 121):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")

run_checkpoint_template = load_yaml(ROOT / "templates/workspace/RUN_CHECKPOINT.yaml") or {}
workspace_contract = run_checkpoint_template.get("workspace") or {}
for key in ("repository_id", "workspace_id", "revision", "dirty_fingerprint", "fingerprint"):
    if key not in workspace_contract:
        errors.append(f"RUN_CHECKPOINT.yaml workspace missing v0.15 key: {key}")

# v0.14 execution isolation contract
isolation_protocol = ROOT / "orchestration/EXECUTION_ISOLATION.md"
isolation_helper = ROOT / "scripts/execution_isolation.py"
for required in (isolation_protocol, isolation_helper):
    if not required.exists():
        errors.append(f"Missing v0.14 execution-isolation artifact: {required.relative_to(ROOT)}")

if isolation_helper.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(isolation_helper)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"execution_isolation.py syntax failed: {compiled.stderr.strip()}")

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

        shared = subprocess.run([
            sys.executable, str(isolation_helper), "resolve",
            "--project", str(project), "--mode", "shared", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if shared.returncode != 0:
            errors.append(f"Shared isolation resolution failed: {shared.stdout.strip()} {shared.stderr.strip()}")
        else:
            shared_doc = json.loads(shared.stdout)
            if shared_doc.get("status") != "AVAILABLE" or shared_doc.get("isolated") is not False:
                errors.append("Shared mode must be AVAILABLE but must not claim isolation")

        sandbox = subprocess.run([
            sys.executable, str(isolation_helper), "resolve",
            "--project", str(project), "--mode", "sandbox", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if sandbox.returncode != 0:
            errors.append(f"Sandbox capability resolution should report state without failing: {sandbox.stdout.strip()} {sandbox.stderr.strip()}")
        else:
            sandbox_doc = json.loads(sandbox.stdout)
            if sandbox_doc.get("status") != "UNSUPPORTED" or sandbox_doc.get("isolated") is not False:
                errors.append("Sandbox must report UNSUPPORTED without a verified provider")
            if sandbox_doc.get("provider") is not None:
                errors.append("Sandbox must not select a provider without external verification")

        auto_normal = subprocess.run([
            sys.executable, str(isolation_helper), "resolve",
            "--project", str(project), "--mode", "auto", "--risk", "normal", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if auto_normal.returncode != 0 or json.loads(auto_normal.stdout).get("mode") != "worktree":
            errors.append(f"Auto isolation should choose worktree for normal risk: {auto_normal.stdout.strip()} {auto_normal.stderr.strip()}")
        auto_high = subprocess.run([
            sys.executable, str(isolation_helper), "resolve",
            "--project", str(project), "--mode", "auto", "--risk", "high", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if auto_high.returncode != 0:
            errors.append(f"High-risk auto isolation resolution should report its state: {auto_high.stdout.strip()} {auto_high.stderr.strip()}")
        else:
            auto_high_doc = json.loads(auto_high.stdout)
            if auto_high_doc.get("mode") != "sandbox" or auto_high_doc.get("status") != "UNSUPPORTED":
                errors.append("High-risk auto isolation must require sandbox and never downgrade")

        # Provider selection requires a current registry-bound record with every observed control.
        sys.path.insert(0, str(ROOT / "scripts"))
        import sandbox_providers  # noqa: E402
        # verification_path() reads the current process environment rather than the
        # child-process env above, so keep its fixture inside this temporary root.
        os.environ["XDG_CONFIG_HOME"] = str(config)
        original_registry = sandbox_providers.REGISTRY
        registry = base / "sandbox-providers.yaml"
        registry.write_text(yaml.safe_dump({
            "providers": {
                "test-provider": {
                    "enabled": True,
                    "integration_status": "AVAILABLE",
                    "runtime_class": "microvm",
                    "assurance": {"isolation_class": "microvm"},
                    "data_classes": ["public"],
                    "verification": {"max_age_hours": 24},
                },
            },
        }), encoding="utf-8")
        sandbox_providers.REGISTRY = registry
        verification = sandbox_providers.verification_path(project)
        verification.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "status": "VERIFIED",
            "provider": "test-provider",
            "verified_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
            "registry_digest": sandbox_providers.registry_digest(),
            "observed_controls": {name: True for name in ("create", "execute", "network_deny", "ephemeral", "destroy", "host_fixture_unchanged")},
        }
        verification.write_text(json.dumps(record), encoding="utf-8")
        verified = sandbox_providers.resolve(project)
        if verified.get("status") != "AVAILABLE" or verified.get("provider") != "test-provider":
            errors.append(f"Current complete provider verification should resolve AVAILABLE: {verified}")
        record["verified_at"] = "2000-01-01T00:00:00Z"
        verification.write_text(json.dumps(record), encoding="utf-8")
        stale = sandbox_providers.resolve(project)
        if stale.get("status") != "BLOCKED":
            errors.append("Expired provider verification must be BLOCKED")
        record["verified_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z")
        record["registry_digest"] = "sha256:stale-registry"
        verification.write_text(json.dumps(record), encoding="utf-8")
        mismatched = sandbox_providers.resolve(project)
        if mismatched.get("status") != "BLOCKED":
            errors.append("Verification from a different provider registry digest must be BLOCKED")
        record["registry_digest"] = sandbox_providers.registry_digest()
        restricted = sandbox_providers.resolve(project, data_class="restricted")
        if restricted.get("status") != "BLOCKED":
            errors.append("Provider must block data classes outside its registry policy")
        record["observed_controls"]["network_deny"] = False
        verification.write_text(json.dumps(record), encoding="utf-8")
        unsafe = sandbox_providers.resolve(project)
        if unsafe.get("status") != "BLOCKED":
            errors.append("Provider must fail closed when an observed security control fails")
        sandbox_providers.REGISTRY = original_registry
        verification_script = ROOT / "scripts/e2b_sandbox_verification.py"
        verification_receipt = base / "e2b-verification.json"
        skip_env = dict(env)
        skip_env.pop("E2B_API_KEY", None)
        skipped = subprocess.run([
            sys.executable, str(verification_script), "--output", str(verification_receipt),
            "--check-artifact-path", "results/output.txt",
        ], env=skip_env, capture_output=True, text=True)
        if skipped.returncode != 0 or not verification_receipt.exists():
            errors.append(f"E2B verifier without credentials must emit a skip receipt: {skipped.stdout.strip()} {skipped.stderr.strip()}")
        else:
            skip_doc = json.loads(verification_receipt.read_text(encoding="utf-8"))
            if skip_doc.get("status") != "SKIPPED_NOT_CONFIGURED" or skip_doc.get("live_provider_verified") is not False:
                errors.append("E2B missing-credential receipt must not claim live verification")
        unsafe_artifact_path = subprocess.run([
            sys.executable, str(verification_script), "--output", str(verification_receipt),
            "--check-artifact-path", "../outside.txt",
        ], env=skip_env, capture_output=True, text=True)
        if unsafe_artifact_path.returncode == 0:
            errors.append("E2B verifier must reject artifact paths that escape their collection root")
        if (config / "aips" / "worktrees").exists():
            errors.append("Isolation resolve must not create a fake sandbox/worktree directory")

        created = subprocess.run([
            sys.executable, str(isolation_helper), "create",
            "--project", str(project), "--mode", "worktree",
            "--id", "iso1", "--boundary", "orders", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if created.returncode != 0:
            errors.append(f"Worktree isolation creation failed: {created.stdout.strip()} {created.stderr.strip()}")
        else:
            created_doc = json.loads(created.stdout)
            worktree = Path(created_doc.get("path") or "")
            if not worktree.is_dir():
                errors.append("Worktree isolation did not create the managed path")
            else:
                inside = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
                if inside.returncode != 0 or inside.stdout.strip() != "true":
                    errors.append("Worktree isolation path must be a real Git worktree")

                status = subprocess.run([
                    sys.executable, str(isolation_helper), "status",
                    "--project", str(project), "--id", "iso1", "--format", "json",
                ], env=env, capture_output=True, text=True)
                if status.returncode != 0:
                    errors.append(f"Worktree isolation status failed: {status.stdout.strip()} {status.stderr.strip()}")
                else:
                    status_doc = json.loads(status.stdout)
                    if status_doc.get("status") != "ACTIVE" or status_doc.get("clean") is not True:
                        errors.append("New AIPS worktree must report ACTIVE and clean")

                duplicate = subprocess.run([
                    sys.executable, str(isolation_helper), "create",
                    "--project", str(project), "--mode", "worktree",
                    "--id", "iso2", "--boundary", "orders", "--format", "json",
                ], env=env, capture_output=True, text=True)
                if duplicate.returncode == 0:
                    errors.append("A second active writer for the same Change Boundary must be blocked")

                dirty_file = worktree / "dirty.txt"
                dirty_file.write_text("preserve me\n", encoding="utf-8")
                dirty_remove = subprocess.run([
                    sys.executable, str(isolation_helper), "remove",
                    "--project", str(project), "--id", "iso1", "--format", "json",
                ], env=env, capture_output=True, text=True)
                if dirty_remove.returncode == 0 or not worktree.exists() or not dirty_file.exists():
                    errors.append("Dirty AIPS worktree cleanup must block and preserve user changes")

                dirty_file.unlink()
                clean_remove = subprocess.run([
                    sys.executable, str(isolation_helper), "remove",
                    "--project", str(project), "--id", "iso1", "--format", "json",
                ], env=env, capture_output=True, text=True)
                if clean_remove.returncode != 0 or worktree.exists():
                    errors.append(f"Clean AIPS worktree cleanup failed: {clean_remove.stdout.strip()} {clean_remove.stderr.strip()}")
                branch = subprocess.run([
                    "git", "-C", str(project), "show-ref", "--verify", "--quiet",
                    "refs/heads/aips/isolation/iso1",
                ])
                if branch.returncode != 0:
                    errors.append("AIPS worktree cleanup must preserve the managed branch")

        sandbox_create = subprocess.run([
            sys.executable, str(isolation_helper), "create",
            "--project", str(project), "--mode", "sandbox",
            "--id", "sandbox1", "--boundary", "sandbox-boundary", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if sandbox_create.returncode == 0:
            errors.append("Sandbox creation without a verified provider must be BLOCKED")
        else:
            try:
                sandbox_create_doc = json.loads(sandbox_create.stdout)
                if sandbox_create_doc.get("status") != "BLOCKED":
                    errors.append("Blocked sandbox creation must emit structured BLOCKED state")
            except Exception:
                errors.append("Blocked sandbox creation must emit structured JSON evidence")

        cli_isolation = subprocess.run([
            "bash", str(ROOT / "bin/aips"), "isolation", "resolve",
            "--project", str(project), "--mode", "shared", "--format", "json",
        ], env=env, capture_output=True, text=True)
        if cli_isolation.returncode != 0 or json.loads(cli_isolation.stdout).get("mode") != "shared":
            errors.append(f"aips isolation CLI routing failed: {cli_isolation.stdout.strip()} {cli_isolation.stderr.strip()}")

for n in range(111, 116):
    matches = list((ROOT / "tests/scenarios").glob(f"{n:03d}-*.md"))
    if len(matches) != 1:
        errors.append(f"Expected exactly one Scenario {n:03d}, found {len(matches)}")

# v0.14.2 governance publication command normalization
guard_evidence = ROOT / "tests/evidence/governance_command_guard.py"
if guard_evidence.exists():
    result = subprocess.run([sys.executable, str(guard_evidence)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"Governance command guard evidence failed: {result.stdout.strip()} {result.stderr.strip()}")
else:
    errors.append("Missing governance command guard evidence")

# v0.14.1 legacy Scenario reconciliation and direct evidence
legacy_evidence = (
    "tests/evidence/adapter_composition.py",
    "tests/evidence/project_intelligence_lifecycle.py",
    "tests/evidence/secret_safety.py",
)
for rel in legacy_evidence:
    evidence_path = ROOT / rel
    if not evidence_path.exists():
        errors.append(f"Missing v0.14.1 legacy evidence: {rel}")
        continue
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(evidence_path)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Legacy evidence syntax failed: {rel}: {compiled.stderr.strip()}")
        continue
    result = subprocess.run([sys.executable, str(evidence_path)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"Legacy evidence failed: {rel}: {result.stdout.strip()} {result.stderr.strip()}")

# v0.17 legacy Project Knowledge migration lifecycle
project_knowledge_migration_evidence = ROOT / "tests/evidence/project_knowledge_migration_lifecycle.py"
if not project_knowledge_migration_evidence.exists():
    errors.append("Missing v0.17 Project Knowledge migration lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_knowledge_migration_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Project Knowledge migration evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(project_knowledge_migration_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Project Knowledge migration lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

# v0.17.1 legacy installation -> managed Harness migration lifecycle
legacy_harness_migration_evidence = ROOT / "tests/evidence/legacy_harness_migration_lifecycle.py"
if not legacy_harness_migration_evidence.exists():
    errors.append("Missing v0.17.1 legacy Harness migration lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(legacy_harness_migration_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Legacy Harness migration evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(legacy_harness_migration_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Legacy Harness migration lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")


# v0.51 parallel runtime port isolation
runtime_port_evidence = ROOT / "tests/evidence/runtime_port_isolation_lifecycle.py"
runtime_port_scenario = ROOT / "tests/scenarios/161-parallel-runtime-port-isolation.md"
for required in (runtime_port_evidence, runtime_port_scenario):
    if not required.exists():
        errors.append(f"Missing v0.51 runtime-port isolation artifact: {required.relative_to(ROOT)}")
if runtime_port_evidence.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(runtime_port_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Runtime-port isolation lifecycle syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(runtime_port_evidence)], capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            errors.append(f"Runtime-port isolation lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
if isolation_helper.exists():
    isolation_text = isolation_helper.read_text(encoding="utf-8")
    for required_text in (
        "runtime-lease",
        "runtime-reallocate",
        "runtime-release",
        "runtime-reconcile",
        "AIPS_PORT",
        "runtime port registry lock timeout",
    ):
        if required_text not in isolation_text:
            errors.append(f"execution_isolation.py missing v0.51 runtime-port contract: {required_text}")

reconciled_contracts = {
    "011": (
        "keep it EPHEMERAL",
        "do not auto-attach",
    ),
    "044": (
        "preflight keeps a project without `.ai/` EPHEMERAL",
        "External Project Intelligence",
    ),
    "051": (
        "SOURCE_REGISTRY.yaml",
        "Project Intelligence",
    ),
    "053": (
        "Targeted Project Intelligence Refresh",
        "STALE",
    ),
    "058": (
        "managed block",
        "unrelated Claude settings/hooks remain intact",
    ),
    "059": (
        "managed runtime instruction block",
        "pre-existing user content",
    ),
    "060": (
        "CONFLICT",
        "preserves the live integration",
    ),
    "062": (
        "Project Intelligence",
        ".ai/intelligence/",
    ),
    "064": (
        "SOURCE_REGISTRY.yaml",
        "derived Project Intelligence remains non-governing",
    ),
    "068": (
        "managed composition",
        "MANUAL/CONFLICT",
    ),
    "073": (
        "governance enforcement",
        "TOOL_GUARDED",
    ),
}
for scenario_id, phrases in reconciled_contracts.items():
    matches = list((ROOT / "tests/scenarios").glob(f"{scenario_id}-*.md"))
    if len(matches) != 1:
        errors.append(f"Reconciled Scenario {scenario_id} missing or ambiguous")
        continue
    body = matches[0].read_text(encoding="utf-8")
    for phrase in phrases:
        normalized = phrase.replace("\\", "")
        if normalized not in body:
            errors.append(f"Reconciled Scenario {scenario_id} missing canonical contract: {normalized}")

scenario_058 = next(iter((ROOT / "tests/scenarios").glob("058-*.md")), None)
if scenario_058 and "AIPS does not edit, append, import into or replace the file" in scenario_058.read_text(encoding="utf-8"):
    errors.append("Scenario 058 regressed to obsolete no-composition behavior")

scenario_011 = next(iter((ROOT / "tests/scenarios").glob("011-*.md")), None)
if scenario_011 and "initialize the target project's minimal `.ai/` workspace if missing" in scenario_011.read_text(encoding="utf-8"):
    errors.append("Scenario 011 regressed to obsolete auto-attach preflight behavior")

repo_scan = subprocess.run([sys.executable, str(ROOT / "scripts/check_secret_leakage.py"), "--root", str(ROOT), "--json"], capture_output=True, text=True)
if repo_scan.returncode != 0:
    errors.append("Repository secret leakage scan found high-confidence findings: " + repo_scan.stdout[:1200])
