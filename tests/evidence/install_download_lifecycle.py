#!/usr/bin/env python3
"""Verify documented and WSL downloaders do not turn failures into success."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def bash_install_snippet(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"~~~bash\n(.*?)\n~~~", text, re.S)
    assert match, f"missing install snippet: {path}"
    return match.group(1)


def exercise(snippet: str, base: Path) -> None:
    fake_bin = base / "bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    fake_curl = fake_bin / "curl"
    fake_curl.write_text("""#!/usr/bin/env bash
set -eu
out=''
while [ "$#" -gt 0 ]; do
  if [ "$1" = --output ]; then out="$2"; shift 2; else shift; fi
done
test -n "$out"
case "$FAKE_CURL_MODE" in
  fail) exit 22 ;;
  empty) : > "$out" ;;
  child_fail) printf 'exit 7\\n' > "$out" ;;
  success) printf 'exit 0\\n' > "$out" ;;
esac
""", encoding="utf-8")
    fake_curl.chmod(0o755)
    temp_dir = base / "tmp"
    temp_dir.mkdir()
    for mode, expected in (("fail", False), ("empty", False), ("child_fail", False), ("success", True)):
        env = dict(os.environ)
        env.update({
            "PATH": f"{fake_bin}:{env.get('PATH', '')}",
            "TMPDIR": str(temp_dir),
            "FAKE_CURL_MODE": mode,
        })
        result = subprocess.run(["bash", "-c", snippet], env=env, text=True, capture_output=True)
        assert (result.returncode == 0) is expected, f"{mode}: {result.stdout} {result.stderr}"
        assert not list(temp_dir.iterdir()), f"temporary installer remained after {mode}"


def main() -> int:
    readme = bash_install_snippet(ROOT / "README.md")
    assert readme == bash_install_snippet(ROOT / "docs/human/INSTALLATION.md")
    assert readme == bash_install_snippet(ROOT / "docs/human/GETTING_STARTED.md")
    ps = (ROOT / "scripts/install.ps1").read_text(encoding="utf-8")
    wsl_match = re.search(r"\$installerScript = @'\n(.*?)\n'@", ps, re.S)
    assert wsl_match, "missing WSL download script"
    wsl_script = wsl_match.group(1).replace("__INSTALLER_URL__", "'https://example.invalid/install.sh'")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        exercise(readme, base / "unix")
        exercise(wsl_script, base / "wsl")
    print("install_download_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
