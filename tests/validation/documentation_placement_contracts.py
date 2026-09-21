from .static_contracts import ROOT, errors
import subprocess
import sys

required = [
    ROOT / "config/documentation-placement.yaml",
    ROOT / "scripts/documentation_placement.py",
    ROOT / "docs/human/index.md",
    ROOT / "docs/human/.vitepress/config.mts",
    ROOT / "docs/human/TECHNOLOGY_GUIDE.md",
    ROOT / "docs/human/EVOLUTION_RADAR_OVERVIEW.md",
    ROOT / "scripts/install.sh",
    ROOT / "scripts/install.ps1",
    ROOT / ".github/workflows/docs-site.yml",
    ROOT / ".github/workflows/installation-entrypoints.yml",
]
for path in required:
    if not path.exists():
        errors.append(f"Missing documentation/install artifact: {path.relative_to(ROOT)}")

script = ROOT / "scripts/documentation_placement.py"
if script.exists():
    proc = subprocess.run([sys.executable,"-m","py_compile",str(script)],capture_output=True,text=True)
    if proc.returncode != 0:
        errors.append(f"documentation_placement.py syntax failed: {proc.stderr.strip()}")
    proc = subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
    if proc.returncode != 0:
        errors.append(f"documentation placement failed: {proc.stdout.strip()} {proc.stderr.strip()}")

package = (ROOT / "package.json").read_text(encoding="utf-8") if (ROOT / "package.json").exists() else ""
for marker in ('"vitepress": "1.6.4"','"docs:build": "vitepress build docs/human"'):
    if marker not in package:
        errors.append(f"package.json missing docs-site contract: {marker}")

install = (ROOT / "scripts/install.sh").read_text(encoding="utf-8") if (ROOT / "scripts/install.sh").exists() else ""
for marker in ("AIPS_INSTALL_DIR","git clone",'exec "$INSTALL_DIR/bin/aips" install'):
    if marker not in install:
        errors.append(f"install.sh missing managed-install contract: {marker}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "gh repo clone" in readme or "\ncd " in readme:
    errors.append("README public install path must not teach clone/cd preparation")
