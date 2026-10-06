"""Shared source loader for contracts that inspect the AIPS shell CLI."""
from __future__ import annotations

from pathlib import Path


def cli_implementation(root: Path) -> str:
    """Return the facade and all source modules in deterministic order."""
    facade = root / "scripts" / "aips_cli.sh"
    modules = sorted((root / "scripts" / "aips_cli").glob("*.sh"))
    return "\n".join(path.read_text(encoding="utf-8") for path in [facade, *modules])
