"""Generate the one-page human Skill Explorer from canonical Skill frontmatter."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = "docs/human/assets/skill-explorer.template.html"
OUTPUT = "docs/human/public/skill-explorer.html"

def records(root: Path) -> list[dict]:
    index = yaml.safe_load((root / "skills/INDEX.yaml").read_text(encoding="utf-8"))
    localization = yaml.safe_load((root / "docs/human/skill-examples.yaml").read_text(encoding="utf-8"))
    if index["version"] != 1 or localization["version"] != 1:
        raise ValueError("unsupported catalog registry version")
    source, labels = index["skills"], localization["skills"]
    if set(source) != set(labels):
        raise ValueError("Human skill examples must match canonical registry exactly")
    result = []
    integrated = {"rapid-prototyping", "technical-research", "human-guided-wizard", "technical-teaching", "creative-writing-workflow"}
    for sid, item in sorted(source.items()):
        detail = labels[sid]
        if not all(isinstance(detail.get(k), str) and detail[k].strip() for k in ("name_zh", "example")):
            raise ValueError("missing localization for " + sid)
        if not (root / "skills" / item["path"]).is_file():
            raise ValueError("missing canonical skill file " + sid)
        result.append({
            "id": sid, "description": item["description"], "capability": item["capability"],
            "path": item["path"], "cost": item["cost"], "triggers": item["triggers"],
            "name_zh": detail["name_zh"], "example": detail["example"],
            "origin": "integrated" if sid in integrated else "existing",
            "optional": sid == "creative-writing-workflow",
        })
    return result

def render(root: Path) -> str:
    data = records(root)
    markup = (root / TEMPLATE).read_text(encoding="utf-8")
    if markup.count("__AIPS_SKILL_DATA__") != 1 or markup.count("__AIPS_SKILL_COUNT__") != 1:
        raise ValueError("template placeholders must each occur exactly once")
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return markup.replace("__AIPS_SKILL_DATA__", encoded).replace("__AIPS_SKILL_COUNT__", str(len(data)))

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="Regenerate one-page HTML")
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    root = args.root.resolve()
    try:
        expected = render(root)
        target = root / OUTPUT
        if target.is_symlink():
            raise ValueError("output cannot be symlink")
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
        elif not target.exists() or target.read_text(encoding="utf-8") != expected:
            raise ValueError("Skill Explorer drift; run python scripts/skill_catalog.py --write")
    except (OSError, KeyError, ValueError, TypeError, yaml.YAMLError) as exc:
        print("FAIL:", exc)
        return 1
    print("Skill Explorer PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
