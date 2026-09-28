"""Record only AIPS-owned execution boundaries when a run is explicitly selected."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator
from uuid import uuid4

from telemetry_record import record


@contextmanager
def observed_stage(project: Path, run_id: str | None, name: str) -> Iterator[dict[str, str]]:
    observation = {"status": "DISABLED"}
    if not run_id:
        yield observation
        return
    operation_id = uuid4().hex
    def marker(action: str, outcome: str = "OK") -> None:
        record(SimpleNamespace(
            project=str(project), run_id=run_id, kind="tool", action=action,
            operation_id=operation_id, parent_operation_id=None,
            related_operation_id=None, name=name,
            provider=None, model=None, input_tokens=None, output_tokens=None,
            outcome=outcome,
        ))
    try:
        marker("started")
    except (OSError, RuntimeError, ValueError):
        observation["status"] = "DEGRADED"
        yield observation
        return
    observation["status"] = "RECORDING"
    outcome = "OK"
    try:
        yield observation
    except BaseException:
        outcome = "ERROR"
        raise
    finally:
        try:
            marker("completed", outcome)
            observation["status"] = "RECORDED"
        except (OSError, RuntimeError, ValueError):
            observation["status"] = "DEGRADED"
