"""Read and filter the canonical AIPS Skill catalog from Skill frontmatter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from skill_index import generate

ROOT = Path(__file__).resolve().parents[1]


def list_skills(
    *, capability: str | None = None, trigger: str | None = None
) -> list[dict[str, Any]]:
    catalog = generate(ROOT).get("skills", {})
    return [
        {
            "id": identifier,
            "description": metadata["description"],
            "capability": metadata["capability"],
            "path": metadata["path"],
            "triggers": metadata["triggers"],
        }
        for identifier, metadata in sorted(catalog.items())
        if (capability is None or metadata["capability"] == capability)
        and (trigger is None or trigger in metadata["triggers"])
    ]


def render_text(skills: list[dict[str, Any]]) -> str:
    rows = ["ID\tCAPABILITY\tDESCRIPTION"]
    rows.extend(
        f"{skill['id']}\t{skill['capability']}\t{skill['description']}"
        for skill in skills
    )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aips skills list",
        description="List canonical AIPS Skills and their short descriptions.",
    )
    parser.add_argument("--capability", help="Keep Skills in this exact capability.")
    parser.add_argument("--trigger", help="Keep Skills with this exact trigger.")
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format."
    )
    args = parser.parse_args()

    try:
        skills = list_skills(capability=args.capability, trigger=args.trigger)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(skills, ensure_ascii=False, indent=2))
    else:
        print(render_text(skills))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
