from __future__ import annotations

import json
import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "config/repository-health.yaml",
    ROOT / "scripts/repository_health.py",
    ROOT / "orchestration/REPOSITORY_HEALTH.md",
    ROOT / "tests/evidence/repository_health_lifecycle.py",
    ROOT / "tests/scenarios/147-repository-health-architecture-drift.md",
    ROOT / "tests/scenarios/148-repository-health-evidence-binding.md",
)
for path in required:
    if not path.exists():
        errors.append(
            f"Missing Repository Health artifact: "
            f"{path.relative_to(ROOT)}"
        )

script = ROOT / "scripts/repository_health.py"
if script.exists():
    compiled = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(script),
        ],
        capture_output=True,
        text=True,
    )
    if compiled.returncode:
        errors.append(
            "Repository Health syntax failed: "
            f"{compiled.stderr.strip()}"
        )
    else:
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "audit",
                "--format",
                "json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            errors.append(
                "Repository Health baseline drift detected: "
                f"{result.stdout.strip()} "
                f"{result.stderr.strip()}"
            )
        else:
            report = json.loads(result.stdout)
            if report.get("status") != "PASS":
                errors.append(
                    "Repository Health baseline must PASS"
                )
            for key, findings in (
                report.get("drift") or {}
            ).items():
                if findings:
                    errors.append(
                        f"Repository Health {key} must be "
                        "empty on baseline"
                    )

            manifest = (
                (report.get("inputs") or {})
                .get("manifest")
                or {}
            )
            entries = manifest.get("entries") or []
            if not entries:
                errors.append(
                    "Repository Health input manifest must "
                    "contain bound inputs"
                )
            if manifest.get("count") != len(entries):
                errors.append(
                    "Repository Health input manifest count "
                    "must match entries"
                )
            if not str(
                manifest.get("digest") or ""
            ).startswith("sha256:"):
                errors.append(
                    "Repository Health input manifest must "
                    "have a sha256 digest"
                )
            for item in entries:
                if not item.get("path"):
                    errors.append(
                        "Repository Health manifest entry "
                        "missing path"
                    )
                if not item.get("roles"):
                    errors.append(
                        "Repository Health manifest entry "
                        "missing roles"
                    )
                if item.get("exists") is True and not str(
                    item.get("digest") or ""
                ).startswith("sha256:"):
                    errors.append(
                        "Existing Repository Health manifest "
                        "entry missing digest"
                    )

            workspace = report.get("workspace") or {}
            binding = report.get("evidence_binding") or {}
            expected_reproducible = (
                workspace.get("git_available") is True
                and workspace.get("dirty") is False
            )
            if (
                binding.get("revision_reproducible")
                is not expected_reproducible
            ):
                errors.append(
                    "Repository Health reproducibility truth "
                    "must match Git workspace state"
                )
            expected_status = (
                "NO_GIT"
                if workspace.get("git_available") is not True
                else (
                    "DIRTY_WORKTREE"
                    if workspace.get("dirty")
                    else "EXACT_REVISION"
                )
            )
            if binding.get("status") != expected_status:
                errors.append(
                    "Repository Health binding status must "
                    "match Git workspace state"
                )
            if (
                binding.get("input_manifest_digest")
                != manifest.get("digest")
            ):
                errors.append(
                    "Repository Health binding must use the "
                    "exact manifest digest"
                )
            if not str(
                binding.get("evidence_fingerprint") or ""
            ).startswith("sha256:"):
                errors.append(
                    "Repository Health evidence fingerprint "
                    "must be sha256-bound"
                )
            policy = binding.get("policy") or {}
            if policy.get("manifest") != "complete":
                errors.append(
                    "Repository Health manifest policy must "
                    "remain complete"
                )
            if (
                policy.get("dirty_workspace")
                != "report_non_reproducible"
            ):
                errors.append(
                    "Repository Health dirty-workspace policy "
                    "must remain report_non_reproducible"
                )

            execution = report.get("execution") or {}
            for key in (
                "credential_required",
                "external_network_required",
                "automatic_remediation_performed",
            ):
                if execution.get(key) is not False:
                    errors.append(
                        "Repository Health execution."
                        f"{key} must remain false"
                    )

            authority = report.get("authority") or {}
            for key in (
                "automatic_remediation_authorized",
                "code_change_authorized",
                "branch_or_pr_authorized",
                "merge_authorized",
                "release_authorized",
                "publication_authorized",
            ):
                if authority.get(key) is not False:
                    errors.append(
                        "Repository Health authority."
                        f"{key} must remain false"
                    )

lifecycle = (
    ROOT / "tests/evidence/repository_health_lifecycle.py"
)
if lifecycle.exists():
    compiled = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(lifecycle),
        ],
        capture_output=True,
        text=True,
    )
    if compiled.returncode:
        errors.append(
            "Repository Health lifecycle syntax failed: "
            f"{compiled.stderr.strip()}"
        )
    else:
        result = subprocess.run(
            [sys.executable, str(lifecycle)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            errors.append(
                "Repository Health lifecycle failed: "
                f"{result.stdout.strip()} "
                f"{result.stderr.strip()}"
            )
