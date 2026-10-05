"""Deterministic property checks for SemVer release selection."""
from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import release_channel


@settings(max_examples=200, derandomize=True, database=None)
@given(st.lists(st.tuples(st.integers(0, 20), st.integers(0, 50), st.integers(0, 100)), unique=True, max_size=30))
def test_release_tags_are_sorted_numerically(versions: list[tuple[int, int, int]]) -> None:
    lines = [
        f"{index + 1:040x}\trefs/tags/v{major}.{minor}.{patch}"
        for index, (major, minor, patch) in enumerate(versions)
    ]
    parsed = release_channel.parse_remote_tags("\n".join(lines))
    assert [item["version"] for item in parsed] == sorted(versions)


if __name__ == "__main__":
    test_release_tags_are_sorted_numerically()
    print("RELEASE CHANNEL PROPERTY CHECKS PASSED")
