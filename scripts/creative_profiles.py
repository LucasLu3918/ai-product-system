"""User-local ComfyUI model profiles: draft from installed weights, approve with host confirmation.

A draft is generated only from file names found in a local models directory (no
download, no network, no model switching). Approval requires an interactive
terminal and an exact typed phrase; it records a hash-bound approval, and the
executor loads a local profile only when that hash still matches. Outputs carry
profile ids and weight file names only, never prompt text or absolute paths.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from creative_errors import Blocked

PROFILE_ID = re.compile(r"^local-[a-z0-9][a-z0-9-]{0,69}$")
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
WEIGHT_SUFFIXES = (".safetensors", ".gguf")
MAX_PROFILE_BYTES = 64 * 1024
MAX_SCAN_ENTRIES = 4096
# Component -> model subdirectories searched for local weights (ComfyUI layout).
COMPONENT_DIRS: dict[str, tuple[str, ...]] = {
    "unet_name": ("diffusion_models", "unet"),
    "clip_name": ("text_encoders", "clip"),
    "prompt_upsampler_name": ("text_encoders", "clip"),
    "vae_name": ("vae",),
}
META_KEYS = {"version", "profile_id", "status"}
Validator = Callable[[str, dict[str, Any]], dict[str, Any]]


def config_home() -> Path:
    """Same resolution as the AIPS config home (XDG_CONFIG_HOME, else ~/.config/aips)."""
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).expanduser().resolve() / "aips"


def profiles_dir() -> Path:
    return config_home() / "creative" / "profiles"


def approvals_path() -> Path:
    return config_home() / "creative" / "profile-approvals.json"


def _profile_file(profile_id: str) -> Path:
    if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
        raise Blocked("profile_id_invalid", "User-local profile ids must start with local- and use lowercase letters, digits and hyphens.")
    return profiles_dir() / f"{profile_id}.yaml"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".aips-profile-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def _read_approvals() -> dict[str, Any]:
    path = approvals_path()
    if not path.exists():
        return {}
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Blocked("profile_approval_record_invalid", "The local ComfyUI profile approval record could not be read.") from exc
    approvals = record.get("approvals") if isinstance(record, dict) and record.get("version") == 1 else None
    if not isinstance(approvals, dict):
        raise Blocked("profile_approval_record_invalid", "The local ComfyUI profile approval record is invalid.")
    return approvals


def load_approved_profile(profile_id: str) -> dict[str, Any] | None:
    """Return the approved local document, None when no local file exists, or fail closed."""
    if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
        return None
    path = _profile_file(profile_id)
    if not path.is_file():
        return None
    data = path.read_bytes()
    if len(data) > MAX_PROFILE_BYTES:
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile exceeds its size limit.")
    record = _read_approvals().get(profile_id)
    if not isinstance(record, dict) or record.get("sha256") != _sha256(data):
        raise Blocked("profile_not_approved", "User-local ComfyUI profile is not approved for its current contents; run approval again.")
    try:
        document = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile is not valid YAML.") from exc
    if not isinstance(document, dict) or document.get("status") != "APPROVED":
        raise Blocked("profile_not_approved", "User-local ComfyUI profile has not been approved.")
    return document


def resolve_models_dir(explicit: str | None) -> Path:
    raw = explicit or os.environ.get("AIPS_COMFYUI_MODELS_DIR") or str(Path.home() / "ComfyUI" / "models")
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise Blocked("profile_models_dir_unavailable", "The local ComfyUI models directory is not available.")
    return path


def local_weight_files(models_dir: Path, component: str) -> list[str]:
    """File names only, from the component's ComfyUI model subdirectories; never recursive, never network."""
    names: set[str] = set()
    for subdir in COMPONENT_DIRS[component]:
        directory = models_dir / subdir
        if not directory.is_dir():
            continue
        with os.scandir(directory) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_SCAN_ENTRIES:
                    break
                if entry.is_file() and entry.name.lower().endswith(WEIGHT_SUFFIXES):
                    names.add(entry.name)
    return sorted(names)


def _choose_component(key: str, listed: Any, models_dir: Path, override: str | None) -> str:
    if key not in COMPONENT_DIRS:
        raise Blocked("profile_component_unsupported", "The base profile uses a component this draft cannot discover.")
    local = local_weight_files(models_dir, key)
    if override is not None:
        if override not in local:
            raise Blocked("profile_component_not_found", "A requested weight file is not installed in the local models directory.")
        return override
    listed_names = set(listed) if isinstance(listed, list) else {listed} if isinstance(listed, str) else set()
    preferred = [name for name in local if name in listed_names]
    if len(preferred) == 1:
        return preferred[0]
    if not preferred and len(local) == 1:
        return local[0]
    if not local and not preferred:
        raise Blocked("comfy_model_unavailable", "No matching weight file for a profile component is installed locally.")
    raise Blocked("profile_component_ambiguous", "More than one local weight file matches a profile component; select it explicitly.")


def draft_profile(*, model_id: str, base_profile_id: str, base_profile: dict[str, Any], models_dir: str | None,
                  profile_id: str | None, overrides: dict[str, str], reserved_ids: set[str], validate: Validator) -> dict[str, Any]:
    """Write one UNAPPROVED local draft whose topology and sampler come from a reviewed system profile."""
    if not isinstance(model_id, str) or not MODEL_ID.fullmatch(model_id):
        raise Blocked("profile_model_id_invalid", "The model id must be an explicit identifier such as the installed model name.")
    slug = re.sub(r"[^a-z0-9]+", "-", model_id.lower()).strip("-")[:70].strip("-")
    chosen_id = profile_id or f"local-{slug}"
    if chosen_id in reserved_ids:
        raise Blocked("profile_id_reserved", "The profile id is reserved by a system profile; choose another local profile id.")
    path = _profile_file(chosen_id)
    if path.exists():
        raise Blocked("profile_draft_exists", "A local profile with this id already exists; choose another --profile-id.")
    root = resolve_models_dir(models_dir)
    unknown = set(overrides) - set(base_profile["components"])
    if unknown:
        raise Blocked("profile_component_unsupported", "The requested component is not part of the base profile.")
    components = {key: _choose_component(key, listed, root, overrides.get(key))
                  for key, listed in base_profile["components"].items()}
    body: dict[str, Any] = {
        "model_id": model_id, "topology": base_profile["topology"], "operation": "generate",
        "components": components, "clip_type": base_profile["clip_type"],
        "sampler": copy.deepcopy(base_profile["sampler"]),
    }
    if base_profile.get("upsampler"):
        body["upsampler"] = copy.deepcopy(base_profile["upsampler"])
    if base_profile.get("runtime_budget"):
        body["runtime_budget"] = copy.deepcopy(base_profile["runtime_budget"])
    validate(chosen_id, body)
    document = {"version": 1, "profile_id": chosen_id, "status": "UNAPPROVED", **body}
    _write_atomic(path, yaml.safe_dump(document, sort_keys=False, allow_unicode=False).encode("utf-8"))
    return {"status": "DRAFTED", "profile_id": chosen_id, "approval_status": "UNAPPROVED",
            "template_id": body["topology"], "components": components,
            "next_step": f"確認權重與參數後執行 aips creative profile approve {chosen_id}（需互動式終端機）。"}


def smoke_check(body: dict[str, Any], models_dir: Path) -> dict[str, Any]:
    """Static smoke preflight: every component file name is installed locally. No ComfyUI call, no inference."""
    failed = [key for key, name in body["components"].items()
              if key not in COMPONENT_DIRS or name not in local_weight_files(models_dir, key)]
    return {"status": "FAIL" if failed else "PASS", "failed_components": failed, "inference": "NOT_RUN"}


def approve_profile(profile_id: str, *, models_dir: str | None, validate: Validator, interactive: bool,
                    read_line: Callable[[str], str], summary_stream: Any = None) -> dict[str, Any]:
    """Approve one draft after a static smoke pass and an exact typed confirmation phrase."""
    if not interactive:
        raise Blocked("profile_approval_requires_tty", "Approval needs an interactive terminal; a person must run it there.")
    path = _profile_file(profile_id)
    if not path.is_file():
        raise Blocked("profile_draft_not_found", "No local profile draft with this id exists.")
    data = path.read_bytes()
    if len(data) > MAX_PROFILE_BYTES:
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile exceeds its size limit.")
    try:
        document = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile is not valid YAML.") from exc
    if not isinstance(document, dict) or document.get("version") != 1 or document.get("profile_id") != profile_id:
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile metadata is invalid.")
    if document.get("status") == "APPROVED":
        raise Blocked("profile_already_approved", "This local profile is already approved for its current contents.")
    if document.get("status") != "UNAPPROVED":
        raise Blocked("profile_local_restricted", "User-local ComfyUI profile status is invalid.")
    body = {key: value for key, value in document.items() if key not in META_KEYS}
    validated = validate(profile_id, body)
    smoke = smoke_check(body, resolve_models_dir(models_dir))
    if smoke["status"] != "PASS":
        raise Blocked("profile_smoke_failed", "Static smoke preflight failed: a component file is not installed locally.",
                      {"failed_components": smoke["failed_components"]})
    stream = summary_stream if summary_stream is not None else sys.stderr
    budget = validated.get("runtime_budget") or {}
    print("本機 ComfyUI profile 核准摘要 (Local ComfyUI profile approval summary)", file=stream)
    print(f"  profile_id: {profile_id}", file=stream)
    print(f"  template_id: {body['topology']}", file=stream)
    print(f"  components: {json.dumps(body['components'], ensure_ascii=False, sort_keys=True)}", file=stream)
    print(f"  sampler: {json.dumps(body['sampler'], ensure_ascii=False, sort_keys=True)}", file=stream)
    print(f"  runtime_budget: {json.dumps(budget, ensure_ascii=False, sort_keys=True) if budget else 'UNESTIMATED'}", file=stream)
    phrase = f"APPROVE {profile_id}"
    typed = read_line(f"請輸入確認片語 `{phrase}` 以核准，其他輸入將取消: ")
    if typed.strip() != phrase:
        raise Blocked("profile_approval_declined", "Approval was cancelled because the confirmation phrase did not match.")
    approved = {**document, "status": "APPROVED"}
    approved_bytes = yaml.safe_dump(approved, sort_keys=False, allow_unicode=False).encode("utf-8")
    _write_atomic(path, approved_bytes)
    approvals = _read_approvals()
    approvals[profile_id] = {"sha256": _sha256(approved_bytes), "template_id": body["topology"],
                             "components": body["components"], "approved_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _write_atomic(approvals_path(), json.dumps({"version": 1, "approvals": approvals}, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"))
    return {"status": "APPROVED", "profile_id": profile_id, "template_id": body["topology"],
            "components": body["components"], "smoke": smoke["status"], "inference": "NOT_RUN",
            "next_step": "在 Bundle 的 comfyui.model_profile 設定此 profile_id 後執行 aips creative preflight。"}
