from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    import project_intelligence as facade
    import project_intelligence_impact_graph as implementation

    with tempfile.TemporaryDirectory(prefix="aips-impact-candidates-") as temp:
        root = Path(temp)
        for relative, content in {
            "src/feature.py": "def run():\n    return __import__('src.feature')\n",
            "src/consumer.py": "from src.feature import run\nrun()\n",
            "tests/test_feature.py": "from src.feature import run\n",
            "scripts/cli.py": (
                "def command_action():\n    return True\n"
                "def dispatch(args):\n"
                "    if args.command == 'compile':\n        command_action()\n"
            ),
            "config/documentation-placement.yaml": (
                "version: 2\nplacement_rules:\n"
                "  - id: feature\n"
                "    triggers: [src/feature.py]\n"
                "    placements:\n"
                "      docs/human/ARCHITECTURE_OVERVIEW.md: [Project Intelligence]\n"
            ),
            ".ai/intelligence/IMPACT_GRAPH.yaml": "edges: []\ncoverage:\n  consumers: unknown\n",
        }.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        graph_path = root / ".ai/intelligence/IMPACT_GRAPH.yaml"
        graph_before = graph_path.read_bytes()
        result = facade.impact_candidates(root, ["src/feature.py"])
        assert result["canonical_graph_written"] is False
        assert result["global_coverage"] == {
            "api": "partial", "data": "partial", "events": "partial", "consumers": "unknown",
        }
        assert any(row["relation"] == "imports" and row["from"] == "src/consumer.py" for row in result["candidates"])
        assert any(row["relation"] == "test_imports" and row["from"] == "tests/test_feature.py" for row in result["candidates"])
        assert any(row["relation"] == "documented_by" and row["to"] == "docs/human/ARCHITECTURE_OVERVIEW.md" for row in result["candidates"])
        assert any(row["kind"] == "dynamic_python_relation" for row in result["unresolved"])
        assert all(row["review_status"] == "unreviewed" and row["provenance"]["line"] > 0 for row in result["candidates"])
        assert graph_path.read_bytes() == graph_before

        cli = implementation.generate_relation_candidates(root, ["scripts/cli.py"])
        assert any(row["relation"] == "dispatches_to" and row["from"] == "scripts/cli.py#command:compile" for row in cli["candidates"])
        capped = implementation.generate_relation_candidates(root, ["src/feature.py"], max_candidates=1)
        assert capped["status"] == "TRUNCATED"
        assert len(capped["candidates"]) == 1

    print("PROJECT INTELLIGENCE RELATION CANDIDATES LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
