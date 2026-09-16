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

intelligence_context_evidence = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
if not intelligence_context_evidence.exists():
    errors.append("Missing Intelligence context lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(intelligence_context_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Intelligence context lifecycle evidence syntax failed: {compiled.stderr.strip()}")
    else:
        focused = subprocess.run([sys.executable, str(intelligence_context_evidence)], capture_output=True, text=True)
        if focused.returncode != 0:
            errors.append(f"Intelligence context lifecycle evidence failed: {focused.stdout.strip()} {focused.stderr.strip()}")

install_preflight_evidence = ROOT / "tests/evidence/install_preflight_lifecycle.py"
if not install_preflight_evidence.exists():
    errors.append("Missing install/preflight lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(install_preflight_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Install/preflight lifecycle evidence syntax failed: {compiled.stderr.strip()}")
    else:
        focused = subprocess.run([sys.executable, str(install_preflight_evidence)], capture_output=True, text=True)
        if focused.returncode != 0:
            errors.append(f"Install/preflight lifecycle evidence failed: {focused.stdout.strip()} {focused.stderr.strip()}")

harness_evidence = ROOT / "tests/evidence/harness_runtime_lifecycle.py"
if not harness_evidence.exists():
    errors.append("Missing focused Harness runtime lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(harness_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Harness runtime lifecycle evidence syntax failed: {compiled.stderr.strip()}")
    else:
        focused = subprocess.run([sys.executable, str(harness_evidence)], capture_output=True, text=True)
        if focused.returncode != 0:
            errors.append(f"Harness runtime lifecycle evidence failed: {focused.stdout.strip()} {focused.stderr.strip()}")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    home = tmp_path / "home"
    fake_bin = tmp_path / "fake-bin"
    config = tmp_path / "config"
    bin_home = tmp_path / "bin-home"
    home.mkdir()
    fake_bin.mkdir()
    (home / ".claude").mkdir()
    custom_claude = home / ".claude" / "CLAUDE.md"
    custom_claude.write_text("# user-owned claude instructions\n", encoding="utf-8")

    for name in ("codex", "claude"):
        p = fake_bin / name
        p.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        p.chmod(0o755)

    gemini = fake_bin / "gemini"
    gemini_script = "\n".join([
        "#!/usr/bin/env bash",
        "state=\"$HOME/.fake-gemini-extension\"",
        "if [ \"${1:-}\" = extensions ]; then",
        "  case \"${2:-}\" in",
        "    list) [ -f \"$state\" ] && echo aips-global-harness; exit 0 ;;",
        "    link) touch \"$state\"; exit 0 ;;",
        "    uninstall) rm -f \"$state\"; exit 0 ;;",
        "  esac",
        "fi",
        "exit 0",
        ""
    ])
    gemini.write_text(gemini_script, encoding="utf-8")
    gemini.chmod(0o755)

    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "AIPS_BIN_HOME": str(bin_home),
        "PATH": f"{fake_bin}:{env.get('PATH', '')}",
    })
    cli = ROOT / "bin/aips"

    install_harness = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
    if install_harness.returncode != 0:
        errors.append(f"harness install test failed: {install_harness.stdout.strip()} {install_harness.stderr.strip()}")
    else:
        codex_bootstrap = home / ".codex" / "AGENTS.md"
        if not codex_bootstrap.exists():
            errors.append("Harness install did not create AIPS-owned Codex bootstrap")
        claude_after_install = custom_claude.read_text(encoding="utf-8")
        if "# user-owned claude instructions" not in claude_after_install or "AIPS-MANAGED-BEGIN" not in claude_after_install:
            errors.append("Harness install must preserve Claude user content while composing AIPS managed block")
        claude_state = config / "aips" / "harness" / "adapters" / "claude-code.yaml"
        claude_state_text = claude_state.read_text(encoding="utf-8") if claude_state.exists() else ""
        if 'status: "AUTOMATIC"' not in claude_state_text or 'capability: "TURN_NATIVE"' not in claude_state_text:
            errors.append("Claude test adapter should install TURN_NATIVE hook plus managed memory block")
        ownership_file = config / "aips" / "harness" / "installation.yaml"
        if not ownership_file.exists():
            errors.append("Harness install did not create ownership manifest")
        else:
            ownership_text = ownership_file.read_text(encoding="utf-8")
            if "runtime_managed_block" not in ownership_text or str(codex_bootstrap) not in ownership_text:
                errors.append("Ownership manifest does not record AIPS Codex managed block resource")
            if "runtime_registration" not in ownership_text or "aips-global-harness" not in ownership_text:
                errors.append("Ownership manifest does not record AIPS-owned Gemini registration")
        if not (home / ".fake-gemini-extension").exists():
            errors.append("Harness install did not register fake Gemini extension")

        project = tmp_path / "project"
        project.mkdir()
        resolved = subprocess.run(
            ["bash", str(cli), "harness", "resolve", "--runtime", "codex", "--project", str(project), "--format", "json"],
            env=env, capture_output=True, text=True,
        )
        if resolved.returncode != 0:
            errors.append(f"harness resolve test failed: {resolved.stdout.strip()} {resolved.stderr.strip()}")
        else:
            try:
                data = json.loads(resolved.stdout)
                if data.get("project", {}).get("mode") != "EPHEMERAL":
                    errors.append("Harness resolver should report EPHEMERAL without .ai")
                if data.get("runtime", {}).get("id") != "codex":
                    errors.append("Harness resolver runtime mismatch")
            except Exception as exc:
                errors.append(f"Harness resolver JSON invalid: {exc}")

        uninstall_harness = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        if uninstall_harness.returncode != 0:
            errors.append(f"harness uninstall test failed: {uninstall_harness.stdout.strip()} {uninstall_harness.stderr.strip()}")
        if codex_bootstrap.exists():
            errors.append("Uninstall should remove unchanged AIPS-owned Codex bootstrap")
        if custom_claude.read_text(encoding="utf-8") != "# user-owned claude instructions\n":
            errors.append("Harness uninstall modified user-owned CLAUDE.md")
        if (home / ".fake-gemini-extension").exists():
            errors.append("Harness uninstall did not unregister fake Gemini extension")

        reinstall = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
        if reinstall.returncode == 0 and codex_bootstrap.exists():
            with codex_bootstrap.open("a", encoding="utf-8") as fh:
                fh.write("\n# user edit\n")
            preserve = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
            if preserve.returncode != 0:
                errors.append("Second harness uninstall failed")
            if not codex_bootstrap.exists() or "# user edit" not in codex_bootstrap.read_text(encoding="utf-8"):
                errors.append("Modified AIPS-owned bootstrap should be preserved on uninstall")


with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    home = tmp_path / "home"
    fake_bin = tmp_path / "fake-bin"
    config = tmp_path / "config"
    bin_home = tmp_path / "bin-home"
    home.mkdir()
    fake_bin.mkdir()
    gemini = fake_bin / "gemini"
    gemini_script = "\n".join([
        "#!/usr/bin/env bash",
        "state=\"$HOME/.fake-gemini-extension\"",
        "fail=\"$HOME/.fake-gemini-fail-uninstall\"",
        "if [ \"${1:-}\" = extensions ]; then",
        "  case \"${2:-}\" in",
        "    list) [ -f \"$state\" ] && echo aips-global-harness; exit 0 ;;",
        "    link) touch \"$state\"; exit 0 ;;",
        "    uninstall) [ -f \"$fail\" ] && exit 9; rm -f \"$state\"; exit 0 ;;",
        "  esac",
        "fi",
        "exit 0",
        ""
    ])
    gemini.write_text(gemini_script, encoding="utf-8")
    gemini.chmod(0o755)
    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "AIPS_BIN_HOME": str(bin_home),
        "PATH": f"{fake_bin}:{env.get('PATH', '')}",
    })
    cli = ROOT / "bin/aips"
    first = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
    if first.returncode != 0:
        errors.append("Gemini recovery setup install failed")
    else:
        (home / ".fake-gemini-fail-uninstall").touch()
        failed_uninstall = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        harness_home = config / "aips" / "harness"
        if failed_uninstall.returncode == 0:
            errors.append("Harness uninstall should fail when an AIPS-owned Gemini registration cannot be removed")
        if not harness_home.exists():
            errors.append("Failed harness uninstall must preserve ownership state for retry")
        (home / ".fake-gemini-fail-uninstall").unlink()
        retry = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        if retry.returncode != 0 or harness_home.exists():
            errors.append("Harness uninstall retry should succeed after Gemini unregister recovers")


# v0.9 deterministic Project Intelligence lifecycle.
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    project = base / "project"
    config = base / "config"
    project.mkdir()
    (project / "internal" / "domain").mkdir(parents=True)
    (project / "AGENTS.md").write_text("# Project Rules\nUse existing architecture.\n", encoding="utf-8")
    (project / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
    (project / "internal" / "domain" / "order.go").write_text("package domain\ntype Order struct{}\n", encoding="utf-8")
    (project / ".env").write_text("PASSWORD=fixture-placeholder\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "aips@example.invalid"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "AIPS Test"], cwd=project, check=True)
    subprocess.run(["git", "add", "AGENTS.md", "main.go", "internal/domain/order.go"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=project, check=True)

    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(config)
    pi = ROOT / "scripts/project_intelligence.py"

    boot = subprocess.run([sys.executable, str(pi), "bootstrap", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
    if boot.returncode != 0:
        errors.append(f"Project Intelligence bootstrap failed: {boot.stdout.strip()} {boot.stderr.strip()}")
    else:
        boot_data = json.loads(boot.stdout)
        store = Path(boot_data["store"])
        if (project / ".ai").exists():
            errors.append("EPHEMERAL Intelligence bootstrap must not create project .ai")
        if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
            errors.append("External Project Intelligence was not created")
        registry = load_yaml(store / "SOURCE_REGISTRY.yaml") or {}
        agents_source = [s for s in (registry.get("sources") or []) if s.get("path") == "AGENTS.md"]
        if not agents_source or agents_source[0].get("content_duplicated") is not False:
            errors.append("SOURCE_REGISTRY must point to AGENTS.md without duplicating content")
        if "codex" not in (agents_source[0].get("auto_loaded_by") or []):
            errors.append("SOURCE_REGISTRY must record Codex native AGENTS visibility")

        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        intel = load_yaml(intel_path) or {}
        intel.setdefault("architecture", {}).update({
            "summary": "Layered test architecture",
            "confidence": "high",
            "source": "topics/architecture.md",
        })
        intel["unknowns"] = []
        topics = intel.setdefault("topics", {})
        for name in ("architecture", "data-flow", "modules", "conventions", "testing", "security"):
            topic_file = store / "topics" / f"{name}.md"
            topic_file.parent.mkdir(parents=True, exist_ok=True)
            topic_file.write_text(
                f"# {name}\n\nEvidence-grounded test topic with enough content for deterministic readiness validation.\n",
                encoding="utf-8",
            )
            topics[name] = {
                "path": f"topics/{name}.md",
                "type": "INTERPRETATION",
                "confidence": "high",
                "evidence": ["AGENTS.md", "main.go"],
                "watch": ["internal/domain/**"] if name == "architecture" else [],
            }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        final = subprocess.run([sys.executable, str(pi), "finalize", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
        if final.returncode != 0 or json.loads(final.stdout).get("readiness") != "READY":
            errors.append(f"Project Intelligence finalize did not reach READY: {final.stdout.strip()} {final.stderr.strip()}")

        review = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"
        review_text = review.read_text(encoding="utf-8") if review.exists() else ""
        if not review.exists() or "Project Intelligence Review" not in review_text:
            errors.append("Deterministic Project Intelligence Review HTML missing")
        if "fixture-placeholder" in review_text or "cdn." in review_text.lower() or "<script src=" in review_text.lower():
            errors.append("Review HTML must be self-contained and must not expose secret values")

        # Unrelated commit must not stale Intelligence.
        (project / "NOTES.txt").write_text("unrelated\n", encoding="utf-8")
        subprocess.run(["git", "add", "NOTES.txt"], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "unrelated"], cwd=project, check=True)
        stat1 = subprocess.run([sys.executable, str(pi), "status", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
        stat1_data = json.loads(stat1.stdout)
        if (stat1_data.get("freshness") or {}).get("status") != "CURRENT":
            errors.append("Unrelated commit should not stale Project Intelligence")

        # Watched committed path must stale affected topic.
        (project / "internal" / "domain" / "order.go").write_text("package domain\ntype Order struct{ ID string }\n", encoding="utf-8")
        subprocess.run(["git", "add", "internal/domain/order.go"], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "domain change"], cwd=project, check=True)
        stat2 = subprocess.run([sys.executable, str(pi), "status", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
        stat2_data = json.loads(stat2.stdout)
        if (stat2_data.get("freshness") or {}).get("status") != "STALE" or "architecture" not in ((stat2_data.get("freshness") or {}).get("affected_topics") or []):
            errors.append("Watched architecture change must stale architecture Intelligence")

        # Dirty watched path is also relevant.
        with (project / "internal" / "domain" / "order.go").open("a", encoding="utf-8") as fh:
            fh.write("// dirty\n")
        stat3 = subprocess.run([sys.executable, str(pi), "status", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
        dirty_reasons = (json.loads(stat3.stdout).get("freshness") or {}).get("reasons") or []
        if not any(str(x).startswith("dirty_watched_path:") for x in dirty_reasons):
            errors.append("Dirty watched path must be reported by Intelligence freshness")

        # Change impact draft must live outside the repo in EPHEMERAL mode.
        impact = subprocess.run([sys.executable, str(pi), "impact-init", "--project", str(project), "--prompt", "modify order api", "--format", "json"], env=env, capture_output=True, text=True)
        impact_data = json.loads(impact.stdout)
        impact_path = Path(impact_data["path"])
        if impact_data.get("status") != "DRAFT" or str(impact_path).startswith(str(project / ".ai")):
            errors.append("EPHEMERAL Change Impact must persist in external AIPS cache")

        # Writer lock prevents concurrent Intelligence writers.
        lock = store / ".writer.lock"
        lock.write_text("test", encoding="utf-8")
        locked = subprocess.run([sys.executable, str(pi), "bootstrap", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
        if locked.returncode == 0:
            errors.append("Project Intelligence writer lock must block a second writer")
        lock.unlink()

        # Attach migrates External -> local, Detach syncs local -> External.
        cli = ROOT / "bin/aips"
        attach = subprocess.run(["bash", str(cli), "attach", str(project)], env=env, capture_output=True, text=True)
        if attach.returncode != 0 or not (project / ".ai" / "intelligence" / "PROJECT_INTELLIGENCE.yaml").exists():
            errors.append(f"Attach did not migrate External Intelligence: {attach.stdout.strip()} {attach.stderr.strip()}")
        else:
            detach = subprocess.run(["bash", str(cli), "detach", str(project)], env=env, capture_output=True, text=True)
            status_after_detach = subprocess.run([sys.executable, str(pi), "status", "--project", str(project), "--format", "json"], env=env, capture_output=True, text=True)
            detached_data = json.loads(status_after_detach.stdout)
            if detach.returncode != 0 or detached_data.get("mode") != "EPHEMERAL" or not detached_data.get("exists"):
                errors.append("Detach must sync local Intelligence back to External Cache")

# Managed composition must preserve user-owned content and unrelated Claude settings.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    manager = ROOT / "scripts/manage_runtime_adapter.py"
    target = root / "AGENTS.md"
    source = root / "aips.md"
    snapshot = root / "snapshot"
    target.write_text("# user rule\n", encoding="utf-8")
    source.write_text("# aips rule\n", encoding="utf-8")

    added = subprocess.run([sys.executable, str(manager), "install-block", "--target", str(target), "--source", str(source), "--snapshot", str(snapshot)], capture_output=True, text=True)
    managed_text = target.read_text(encoding="utf-8")
    if added.returncode != 0 or "# user rule" not in managed_text or "AIPS-MANAGED-BEGIN" not in managed_text:
        errors.append("Managed block install must preserve existing user instruction content")

    removed = subprocess.run([sys.executable, str(manager), "uninstall-block", "--target", str(target), "--snapshot", str(snapshot)], capture_output=True, text=True)
    if removed.returncode != 0 or target.read_text(encoding="utf-8") != "# user rule\n":
        errors.append("Managed block uninstall must remove only AIPS content")

    settings = root / "settings.json"
    settings.write_text(json.dumps({"permissions": {"allow": ["Read"]}, "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "user-hook"}]}]}}), encoding="utf-8")
    install_hook = subprocess.run([sys.executable, str(manager), "install-claude-hook", "--settings", str(settings), "--command", "AIPS_MANAGED_HOOK=1 echo aips"], capture_output=True, text=True)
    settings_doc = json.loads(settings.read_text(encoding="utf-8"))
    if install_hook.returncode != 0 or "PreToolUse" not in settings_doc.get("hooks", {}) or "UserPromptSubmit" not in settings_doc.get("hooks", {}):
        errors.append("Claude hook composition must preserve unrelated settings/hooks")
    remove_hook = subprocess.run([sys.executable, str(manager), "uninstall-claude-hook", "--settings", str(settings)], capture_output=True, text=True)
    settings_doc = json.loads(settings.read_text(encoding="utf-8"))
    if remove_hook.returncode != 0 or "PreToolUse" not in settings_doc.get("hooks", {}) or "UserPromptSubmit" in settings_doc.get("hooks", {}):
        errors.append("Claude hook uninstall must remove only AIPS UserPromptSubmit hook")



# Secret scanner must detect high-confidence credentials without echoing the value.
with tempfile.TemporaryDirectory() as tmp:
    secret_root = Path(tmp)
    secret_file = secret_root / "config.txt"
    fake_token = "ghp_" + ("A" * 40)
    secret_file.write_text("TOKEN=" + fake_token + "\\n", encoding="utf-8")
    scanner = ROOT / "scripts/check_secret_leakage.py"
    result = subprocess.run([sys.executable, str(scanner), "--root", str(secret_root), "--json"], capture_output=True, text=True)
    if result.returncode == 0:
        errors.append("Secret checker failed to detect a high-confidence token")
    if fake_token in result.stdout or fake_token in result.stderr:
        errors.append("Secret checker leaked the detected secret value in output")
    try:
        scan_doc = json.loads(result.stdout)
        if not scan_doc.get("findings") or scan_doc["findings"][0].get("detector") != "github-token":
            errors.append("Secret checker output missing expected redacted finding metadata")
    except Exception:
        errors.append("Secret checker did not emit valid JSON evidence")

