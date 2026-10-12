#!/usr/bin/env python3
"""List canonical AIPS Skills and optionally the reviewed upstream inventory."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from skill_index import generate

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "skills" / "integrations" / "matt-pocock-skills.json"
LOCALIZATION = ROOT / "skills" / "locale" / "zh-TW.json"

DISPOSITION_ZH = {
    "merged": "已合併",
    "adopted": "已採納",
    "adopted_optional": "選用",
    "workflow": "流程整合",
    "deferred": "延後",
    "excluded_beta": "排除 Beta",
    "reference_only": "僅供參考",
    "not_adopted": "不導入",
}
CATEGORY_ZH = {
    "database": "資料庫",
    "delivery-planning": "交付規劃",
    "design": "設計",
    "engineering": "工程",
    "infrastructure": "基礎設施",
    "operations": "營運",
    "performance": "效能",
    "product": "產品",
    "quality": "品質",
    "security": "安全",
    "software-architecture": "軟體架構",
    "testing": "測試",
    "productivity": "生產力",
    "in-progress": "進行中",
    "misc": "其他",
}


def collect(
    *,
    locale: str,
    include_upstream: bool,
    capability: str | None,
    trigger: str | None,
) -> list[dict[str, Any]]:
    localized = json.loads(LOCALIZATION.read_text(encoding="utf-8"))
    active = generate(ROOT).get("skills", {})
    items: list[dict[str, Any]] = []
    for identifier, skill in active.items():
        if capability and skill["capability"] != capability:
            continue
        if trigger and trigger not in skill.get("triggers", []):
            continue
        items.append(
            {
                "id": identifier,
                "description": localized.get(identifier, skill["description"])
                if locale == "zh-TW"
                else skill["description"],
                "capability": skill["capability"],
                "path": skill["path"],
                "triggers": skill["triggers"],
                "source": "aips",
                "status": "enabled",
                "category": skill["capability"],
                "aips_targets": [identifier],
                "locale": locale,
            }
        )

    if include_upstream:
        upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        for record in upstream["skills"]:
            if capability and record["category"] != capability:
                continue
            # Upstream rows have no AIPS trigger metadata.
            if trigger:
                continue
            items.append(
                {
                    "id": record["id"],
                    "description": localized.get(record["id"], record["description"])
                    if locale == "zh-TW"
                    else record["description"],
                    "capability": record["category"],
                    "path": record["path"],
                    "triggers": [],
                    "source": "upstream",
                    "status": record["disposition"],
                    "category": record["category"],
                    "aips_targets": record.get("aips_targets", []),
                    "reason": record.get("reason", ""),
                    "locale": locale,
                }
            )
    return sorted(items, key=lambda item: (item["category"], item["source"], item["id"]))


def _label(item: dict[str, Any], locale: str) -> str:
    if item["source"] == "aips":
        return "啟用" if locale == "zh-TW" else "enabled"
    return DISPOSITION_ZH.get(item["status"], item["status"]) if locale == "zh-TW" else item["status"]


def render_table(items: list[dict[str, Any]], locale: str, group_by: str) -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        key = (
            item["category"]
            if group_by == "category"
            else item["source"]
            if group_by == "source"
            else item["status"]
        )
        groups[key].append(item)

    lines: list[str] = []
    for group in sorted(groups):
        heading = CATEGORY_ZH.get(group, group) if locale == "zh-TW" and group_by == "category" else group
        lines.extend([f"## {heading}", ""])
        if locale == "zh-TW":
            lines.extend(["| 技能 | 來源 / 狀態 | 用途 | AIPS 對應 |", "|---|---|---|---|"])
        else:
            lines.extend(["| Skill | Source / status | Description | AIPS mapping |", "|---|---|---|---|"])
        for item in groups[group]:
            source = "AIPS" if item["source"] == "aips" else "上游" if locale == "zh-TW" else "upstream"
            description = item["description"].replace("|", "\\|").replace("\n", " ")
            targets = "、".join(item["aips_targets"]) if item["aips_targets"] else "—"
            lines.append(f"| `{item['id']}` | {source} · {_label(item, locale)} | {description} | {targets} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aips skills list",
        description="List canonical AIPS Skills and their short descriptions.",
    )
    parser.add_argument("command", nargs="?", choices=("list",), help=argparse.SUPPRESS)
    parser.add_argument("--capability", help="Filter by exact AIPS capability/category.")
    parser.add_argument("--trigger", help="Filter by exact Skill trigger.")
    parser.add_argument("--include-upstream", action="store_true", help="Include the reviewed 38-item upstream inventory.")
    parser.add_argument("--locale", choices=("zh-TW", "en"), default="zh-TW")
    parser.add_argument("--format", choices=("table", "text", "json"), default="table")
    parser.add_argument("--group-by", choices=("category", "status", "source"), default="category")
    args = parser.parse_args(argv)

    try:
        items = collect(
            locale=args.locale,
            include_upstream=args.include_upstream,
            capability=args.capability,
            trigger=args.trigger,
        )
        if args.format == "json":
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            print(render_table(items, args.locale, args.group_by), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
