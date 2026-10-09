"""Shared error types for local creative execution modules."""
from __future__ import annotations

from typing import Any


class Blocked(ValueError):
    def __init__(self, reason_code: str, message: str, diagnostics: dict[str, Any] | None = None):
        super().__init__(message)
        self.reason_code = reason_code
        self.diagnostics = diagnostics or {}
