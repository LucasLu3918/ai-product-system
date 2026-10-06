#!/usr/bin/env python3
"""Verify explicitly declared Python imports for the shared CI bootstrap."""

from __future__ import annotations

import argparse
import importlib
import re
import sys

MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")


def parse_modules(value: str) -> list[str]:
    modules = [line.strip() for line in value.splitlines() if line.strip()]
    if not modules:
        raise ValueError("at least one verification module must be declared")
    invalid = [module for module in modules if not MODULE_NAME.fullmatch(module)]
    if invalid:
        raise ValueError("verification modules must be dotted Python identifiers")
    return list(dict.fromkeys(modules))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules", required=True, help="newline-separated Python module names")
    args = parser.parse_args()
    try:
        modules = parse_modules(args.modules)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError as exc:
            print(f"ERROR: cannot import declared module {module}: {exc.__class__.__name__}", file=sys.stderr)
            return 1
    print(f"Python bootstrap imports verified: {', '.join(modules)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
