"""Focused unit contracts for the shared deterministic primitives."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from aips_common.canonical import canonical_digest, canonical_hash, canonical_json_bytes
from aips_common.paths import relative_path
from aips_common.patterns import glob_matches


def test_canonical_json_and_hash_facades() -> None:
    value = {"unicode": "繁體", "nested": {"b": 2, "a": 1}}
    expected = b'{"nested":{"a":1,"b":2},"unicode":"\xe7\xb9\x81\xe9\xab\x94"}'
    assert canonical_json_bytes(value) == expected
    raw = canonical_hash(value)
    assert len(raw) == 64 and all(char in "0123456789abcdef" for char in raw)
    assert canonical_digest(value) == f"sha256:{raw}"


def test_relative_paths_inside_and_outside_root() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "repo"
        root.mkdir()
        inside = root / "scripts" / "entry.py"
        inside.parent.mkdir()
        inside.touch()
        outside = Path(temporary) / "external.txt"
        outside.touch()
        assert relative_path(root, inside) == "scripts/entry.py"
        assert relative_path(root, outside) == str(outside.resolve())


def test_glob_compatibility_modes() -> None:
    assert glob_matches(
        ".\\cache\\state.json",
        "./cache/*.json",
        path_mode="slash_prefix",
        pattern_mode="slash_prefix",
    )
    assert glob_matches("scripts/a.py", "**/*.py", globstar_zero_directory=True)
    assert glob_matches("scripts/a.py", "scripts/**/*.py", globstar_as_star=True)
    assert not glob_matches("Scripts/a.py", "scripts/*.py", case_sensitive=True)


def run_focused_tests() -> None:
    test_canonical_json_and_hash_facades()
    test_relative_paths_inside_and_outside_root()
    test_glob_compatibility_modes()


if __name__ == "__main__":
    run_focused_tests()
