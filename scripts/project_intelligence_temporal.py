"""Temporal query adapter extracted from Project Intelligence."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from temporal_intelligence import (
    active_assertions as temporal_active_assertions,
)
from temporal_intelligence import (
    between as temporal_between,
)
from temporal_intelligence import (
    load_temporal,
    temporal_digest,
)
from temporal_intelligence import (
    validate_document as validate_temporal_document,
)
from temporal_intelligence import (
    why as temporal_why,
)


def temporal_query(root: Path, store: Path, mode: str, revision: str | None,
                   base: str | None, head: str | None, assertion_id: str | None) -> dict[str, Any]:
    doc = load_temporal(store)
    errors = validate_temporal_document(doc)
    if errors:
        raise RuntimeError("invalid temporal assertions: " + "; ".join(errors))
    if mode == "current":
        result = temporal_active_assertions(root, doc)
    elif mode == "as-of":
        if not revision:
            raise RuntimeError("--revision is required for --mode as-of")
        result = temporal_active_assertions(root, doc, revision)
    elif mode == "between":
        if not base or not head:
            raise RuntimeError("--base and --head are required for --mode between")
        result = temporal_between(root, doc, base, head)
    elif mode == "why":
        if not assertion_id:
            raise RuntimeError("--assertion is required for --mode why")
        result = temporal_why(doc, assertion_id)
    else:
        raise RuntimeError(f"unsupported temporal mode: {mode}")
    result["canonical"] = str(store / "TEMPORAL_ASSERTIONS.yaml")
    result["digest"] = temporal_digest(doc)
    return result
