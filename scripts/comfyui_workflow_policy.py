"""Fail-closed trust and side-effect policy for ComfyUI API workflows."""
from __future__ import annotations

import re
from typing import Any

from creative_errors import Blocked

CORE_MODULES = ("nodes", "comfy_extras.")
API_MODULE_PREFIXES = ("comfy_api_nodes", "api_nodes")
MAX_NODE_CLASS_CHARS = 128
MAX_NODE_ID_CHARS = 64
NODE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SENSITIVE_CLASS = re.compile(r"(?:http|https|api|upload|remote|cloud|webhook|python|script|execute|command)", re.IGNORECASE)
SENSITIVE_INPUT = re.compile(r"(?:^|_)(?:url|uri|endpoint|api_key|token|script|command|path|directory|folder)(?:$|_)", re.IGNORECASE)


def classify_node(node_class: str, metadata: Any) -> dict[str, str]:
    """Trust only nodes whose runtime metadata identifies a built-in Comfy module."""
    if not isinstance(node_class, str) or not node_class or len(node_class) > MAX_NODE_CLASS_CHARS:
        return {"trust": "DENY", "reason_code": "WORKFLOW_NODE_INVALID"}
    module = metadata.get("python_module") if isinstance(metadata, dict) else None
    if not isinstance(module, str) or not module or len(module) > 256:
        return {"trust": "DENY", "reason_code": "NODE_TRUST_UNKNOWN"}
    module = module.strip()
    if module.startswith(API_MODULE_PREFIXES) or SENSITIVE_CLASS.search(node_class):
        return {"trust": "DENY", "reason_code": "EXTERNAL_EGRESS_DENIED"}
    if module == "nodes" or module.startswith("comfy_extras."):
        inputs = metadata.get("input") or {}
        names = set()
        if isinstance(inputs, dict):
            for group in ("required", "optional", "hidden"):
                values = inputs.get(group) or {}
                if isinstance(values, dict):
                    names.update(str(name) for name in values)
        if any(SENSITIVE_INPUT.search(name) for name in names):
            return {"trust": "DENY", "reason_code": "WORKFLOW_CAPABILITY_DENIED"}
        return {"trust": "TRUSTED_CORE", "reason_code": "CORE_NODE_ALLOWED"}
    return {"trust": "DENY", "reason_code": "CUSTOM_NODE_TRUST_REQUIRED"}


def require_safe_node(node_class: str, metadata: Any) -> None:
    decision = classify_node(node_class, metadata)
    if decision["trust"] != "TRUSTED_CORE":
        message = {
            "CUSTOM_NODE_TRUST_REQUIRED": "Unreviewed custom ComfyUI nodes require a separate trust boundary.",
            "EXTERNAL_EGRESS_DENIED": "API, remote-service, and external-egress nodes are not permitted.",
            "WORKFLOW_CAPABILITY_DENIED": "This node exposes an unreviewed filesystem or execution capability.",
            "NODE_TRUST_UNKNOWN": "ComfyUI did not identify a verifiable built-in node module.",
        }.get(decision["reason_code"], "ComfyUI node is outside the supported trust boundary.")
        raise Blocked(decision["reason_code"], message, phase="creative.workflow_policy", source="comfyui")


def validate_node_id(node_id: Any) -> bool:
    return isinstance(node_id, str) and bool(NODE_ID.fullmatch(node_id))
