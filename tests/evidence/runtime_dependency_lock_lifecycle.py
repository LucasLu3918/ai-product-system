from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-runtime-lock-") as tmp:
        base = Path(tmp)
        capture = base / "args.json"
        fake_python = base / "fake-python"
        fake_python.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "pathlib.Path(os.environ['AIPS_CAPTURE_ARGS']).write_text(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        requirements = base / "requirements.txt"
        constraints = base / "constraints.txt"
        requirements.write_text("example>=1\n", encoding="utf-8")
        constraints.write_text("example==1.2.3\n", encoding="utf-8")
        env = dict(os.environ, AIPS_CAPTURE_ARGS=str(capture))
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/package_install.py"), "--python", str(fake_python),
             "--requirements", str(requirements), "--constraints", str(constraints)],
            env=env, capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout) == {"status": "PASS"}
        args = json.loads(capture.read_text(encoding="utf-8"))
        assert args[args.index("-c") + 1] == str(constraints)
        assert args[args.index("-r") + 1] == str(requirements)

        cli = "\n".join(path.read_text(encoding="utf-8") for path in [ROOT / "scripts/aips_cli.sh", *sorted((ROOT / "scripts/aips_cli").glob("*.sh"))])
        assert '--constraints "$SYSTEM_DIR/constraints/tested.txt"' in cli
    print("RUNTIME DEPENDENCY LOCK LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
