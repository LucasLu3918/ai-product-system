#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

def main() -> int:
    import retrieval_intelligence as facade
    import retrieval_relations as implementation

    source = (
        "def apply_change(value):\n"
        "    # ignored_comment()\n"
        "    text = 'ignored_string()'\n"
        "    return normalize(value)\n"
    )
    masked = facade.code_without_comments_or_strings(source)
    assert masked == implementation.code_without_comments_or_strings(source)
    expected = implementation.relation_rows(
        masked,
        facade.extract_symbols("sample.py", source),
        max_rows=facade.IMPACT_MAX_RELATIONS_PER_FILE,
    )
    assert facade.extract_code_relations("sample.py", source) == expected
    assert expected == [
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "text",
            "source_line": 3,
            "relation": "references",
        },
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "normalize",
            "source_line": 4,
            "relation": "calls",
        },
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "value",
            "source_line": 4,
            "relation": "references",
        },
    ]
    assert any(
        row["target_name"] == "normalize" and row["relation"] == "calls"
        for row in expected
    )
    assert all(
        row["target_name"] not in {"ignored_comment", "ignored_string"}
        for row in expected
    )
    annotated_source = (
        "from typing import Any\n"
        "def annotated(value: Any) -> dict[str, Any]:\n"
        "    message = 'normalize(value)'\n"
        "    client.lookup(value)\n"
        "    return normalize(value)\n"
    )
    annotated_rows = facade.extract_code_relations("annotated.py", annotated_source)
    calls = {row["target_name"] for row in annotated_rows if row["relation"] == "calls"}
    assert calls == {"normalize"}
    assert not any(row["relation"] == "calls" and row["target_name"] in {"Any", "dict", "lookup"} for row in annotated_rows)
    assert any(row["target_name"] == "lookup" and row["relation"] == "references" for row in annotated_rows)
    capped_source = (
        "def capped():\n"
        "    alpha + beta + gamma + delta\n"
        "    return normalize(value)\n"
    )
    capped_rows = implementation.relation_rows(
        implementation.code_without_comments_or_strings(capped_source),
        facade.extract_symbols("capped.py", capped_source),
        max_rows=2,
        call_names_by_line=implementation.python_call_names_by_line(capped_source),
    )
    assert any(row["target_name"] == "normalize" and row["relation"] == "calls" for row in capped_rows)
    assert len(capped_rows) == 2
    assert facade.extract_code_relations("sample.txt", source) == []
    assert facade.extract_code_relations("config/credentials.json", source) == []
    print("RETRIEVAL RELATIONS EXTRACTION FACADE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
