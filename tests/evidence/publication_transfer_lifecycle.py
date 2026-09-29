from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/publication_transfer.py"
REPOSITORY = "LucasLu3918/ai-product-system"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def git(root: Path, *args: str) -> str:
    result = run("git", *args, cwd=root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def transfer(
    root: Path, action: str, base: str, *extra: str
) -> subprocess.CompletedProcess[str]:
    return run(
        sys.executable,
        str(SCRIPT),
        action,
        "--project-root",
        str(root),
        "--base",
        base,
        "--repository",
        REPOSITORY,
        *extra,
        cwd=root,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.name", "Publication Evidence")
        git(
            root,
            "config",
            "user.email",
            "123+publication" + chr(64) + "users.noreply.github.com",
        )
        git(root, "remote", "add", "origin", f"https://github.com/{REPOSITORY}.git")
        (root / "README.md").write_text("# Base\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        base = git(root, "rev-parse", "HEAD")
        large = root / "large.md"
        large.write_text(
            "# UTF-8 transfer\n" + "繁體中文內容\n" * 9000, encoding="utf-8"
        )
        git(root, "add", ".")
        git(root, "commit", "-qm", "candidate")
        prepared = transfer(root, "prepare", base)
        assert prepared.returncode == 0, prepared.stdout + prepared.stderr
        candidate = json.loads(prepared.stdout)
        expected_blob = git(root, "rev-parse", "HEAD:large.md")
        assert candidate["entries"] == [
            {"path": "large.md", "mode": "100644", "type": "blob", "sha": expected_blob}
        ]
        assert candidate["tree_sha"] == git(root, "rev-parse", "HEAD^{tree}")
        receipt_path = root.parent / f"{root.name}-receipt.json"
        receipt = {
            "repository": REPOSITORY,
            "base_sha": base,
            "tree_sha": candidate["tree_sha"],
            "blobs": {"large.md": expected_blob},
        }
        try:
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            verified = transfer(root, "verify", base, "--receipt", str(receipt_path))
            assert (
                verified.returncode == 0
                and json.loads(verified.stdout)["status"] == "READY_TO_PUBLISH"
            )

            truncated = {**receipt, "blobs": {"large.md": "0" * 40}}
            receipt_path.write_text(json.dumps(truncated), encoding="utf-8")
            rejected = transfer(root, "verify", base, "--receipt", str(receipt_path))
            assert rejected.returncode == 1 and "blob identities" in rejected.stdout
            receipt_path.write_text(
                json.dumps({**receipt, "tree_sha": "0" * 40}), encoding="utf-8"
            )
            rejected = transfer(root, "verify", base, "--receipt", str(receipt_path))
            assert rejected.returncode == 1 and "remote tree" in rejected.stdout
            receipt_path.write_text(
                json.dumps({**receipt, "base_sha": "0" * 40}), encoding="utf-8"
            )
            rejected = transfer(root, "verify", base, "--receipt", str(receipt_path))
            assert rejected.returncode == 1 and "remote base" in rejected.stdout
        finally:
            receipt_path.unlink(missing_ok=True)

        git(root, "remote", "set-url", "origin", "/tmp/wrong-local-origin")
        rejected = transfer(root, "prepare", base)
        assert rejected.returncode == 1 and "does not match expected" in rejected.stdout
        git(
            root,
            "remote",
            "set-url",
            "origin",
            "git" + chr(64) + f"github.com:{REPOSITORY}.git",
        )
        large.write_text(
            large.read_text(encoding="utf-8") + "dirty\n", encoding="utf-8"
        )
        rejected = transfer(root, "prepare", base)
        assert rejected.returncode == 1 and "working tree is dirty" in rejected.stdout
        git(root, "checkout", "--", "large.md")
        (root / "second.md").write_text("second\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "second candidate")
        rejected = transfer(root, "prepare", base)
        assert (
            rejected.returncode == 1
            and "exactly one clean candidate commit" in rejected.stdout
        )
    print("PUBLICATION TRANSFER LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
