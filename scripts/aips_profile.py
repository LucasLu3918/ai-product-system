"""AIPS profile switches: relaxations are off by default and only a person can change them.

The file is ``profile.yaml`` under the AIPS config home (``XDG_CONFIG_HOME`` honored)::

    version: 1
    settings:
      <switch-id>: true | false

A missing file means every switch keeps its strict default. A malformed file, an unknown
key or a value of the wrong type fails closed to the defaults and reports a bounded
diagnostic (reason code and field names only). Switches come from the fixed allow-list
``SWITCHES`` in code; every switch defaults to off.

``aips profile set`` is the only writer. It needs an interactive terminal on stdin and
stderr, prints the old value, the new value and the security implication, and requires
the exact typed phrase ``SET <key> <value>``. No flag skips confirmation. The write is
atomic and the file is 0600 inside a 0700 directory. The Claude Code guard denies agent
writes to the file and to ``aips profile set`` (scripts/protected_paths.py).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from protected_paths import profile_settings_path
except ModuleNotFoundError:  # imported as a repository module
    from scripts.protected_paths import profile_settings_path

SCHEMA_VERSION = 1
PROFILE_NAME = "strict"
FILE_LABEL = "~/.config/aips/profile.yaml"
MAX_FILE_BYTES = 16 * 1024
MAX_REPORTED_FIELDS = 8
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
VALUE_TEXT = {"true": True, "false": False}
TOP_LEVEL_KEYS = ("version", "settings")


@dataclass(frozen=True)
class Switch:
    """One relaxation a person may enable. Each entry states its security implication."""

    default: bool
    implication_zh: str
    implication_en: str


# Fixed allow-list defined in code. Keys from the file or from `set` outside this mapping are refused.
SWITCHES: dict[str, Switch] = {
    "claude_coauthor_trailer": Switch(
        default=False,
        implication_zh="Git 發布閘門的提交訊息 PII 掃描會放行最後 trailer 區塊中確切符合 Claude 共同作者格式的一行；其他電子郵件、內文電子郵件與其他 trailer 仍被攔截。",
        implication_en="The publication gate commit-message PII scan allows one exact Claude co-author trailer in the final trailer block; every other address, body text address and other trailer stays blocked.",
    ),
    "post_merge_refresh": Switch(
        default=False,
        implication_zh="Turn Context hook 在 Intelligence 為 READY 但 STALE 且任務相關主題受影響時，每個 store 每個 HEAD 最多啟動一次背景 `aips intelligence refresh`；只寫入 AIPS Intelligence store，不阻擋該回合。",
        implication_en="When Intelligence is READY but STALE with task-relevant topics affected, the Turn Context hook starts at most one detached `aips intelligence refresh` per store per HEAD; it writes only the AIPS Intelligence store and never blocks the turn.",
    ),
}

RECOVERY = {
    "PROFILE_FILE_MALFORMED": "profile.yaml 不是有效的 version 1 YAML；所有開關已回到預設值。請由人修正或移除該檔。",
    "PROFILE_FILE_UNSAFE": "profile.yaml 必須是一般檔案，不可為符號連結或目錄；所有開關已回到預設值。",
    "PROFILE_FILE_UNREADABLE": "無法讀取 profile.yaml；請檢查檔案權限，所有開關已回到預設值。",
    "PROFILE_FILE_TOO_LARGE": "profile.yaml 超過大小上限；所有開關已回到預設值。請由人縮減或移除該檔。",
    "PROFILE_UNKNOWN_KEY": "profile.yaml 含有不在允許清單中的鍵；整個檔案已忽略，所有開關回到預設值。請由人移除未知鍵。",
    "PROFILE_VALUE_TYPE_INVALID": "profile.yaml 的開關值必須是 true 或 false；整個檔案已忽略，所有開關回到預設值。",
    "PROFILE_UNAVAILABLE": "無法載入 profile 設定；所有開關以嚴格預設值運作。",
    "PROFILE_SET_REQUIRES_TTY": "切換需要互動式終端機，並由人輸入確認片語；代理或非互動環境不得切換。",
    "PROFILE_KEY_NOT_ALLOWED": "此 key 不在允許切換清單中；請以 `aips profile show` 查看可用開關。",
    "PROFILE_VALUE_INVALID": "開關值只能是 true 或 false。",
    "PROFILE_VALUE_UNCHANGED": "此開關已是這個值；未寫入任何設定。",
    "PROFILE_FILE_INVALID": "profile.yaml 目前無效，為避免覆寫內容，拒絕切換；請由人先修正或移除該檔。",
    "PROFILE_SET_DECLINED": "確認片語不符，切換已取消；未寫入任何設定。",
}


class ProfileError(ValueError):
    """A stable, bounded refusal. The message never echoes the submitted key or paths."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class ProfileState:
    status: str
    values: dict[str, bool]
    sources: dict[str, str]
    diagnostic: dict[str, Any] | None


def _defaults() -> dict[str, bool]:
    return {key: switch.default for key, switch in SWITCHES.items()}


def _name(value: Any) -> str:
    """Bounded, printable field name; anything outside the key pattern is shown as a placeholder."""
    return value if isinstance(value, str) and KEY_PATTERN.fullmatch(value) else "<invalid-key>"


def _diagnostic(reason: str, fields: list[str] | None = None) -> dict[str, Any]:
    names = sorted(set(fields or []))[:MAX_REPORTED_FIELDS]
    return {"reason_code": reason, "fields": names, "recovery": RECOVERY.get(reason, "")}


def _invalid(reason: str, fields: list[str] | None = None) -> ProfileState:
    values = _defaults()
    return ProfileState("INVALID", values, {key: "default" for key in values}, _diagnostic(reason, fields))


def _default_state() -> ProfileState:
    values = _defaults()
    return ProfileState("DEFAULT", values, {key: "default" for key in values}, None)


def _load(path: Path) -> ProfileState:
    if not os.path.lexists(path):
        return _default_state()
    if path.is_symlink() or not path.is_file():
        return _invalid("PROFILE_FILE_UNSAFE")
    try:
        raw = path.read_bytes()
    except OSError:
        return _invalid("PROFILE_FILE_UNREADABLE")
    if len(raw) > MAX_FILE_BYTES:
        return _invalid("PROFILE_FILE_TOO_LARGE")
    try:
        document = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError):
        return _invalid("PROFILE_FILE_MALFORMED")
    if not isinstance(document, dict):
        return _invalid("PROFILE_FILE_MALFORMED")
    unknown_top = [_name(key) for key in document if key not in TOP_LEVEL_KEYS]
    if unknown_top:
        return _invalid("PROFILE_UNKNOWN_KEY", unknown_top)
    version = document.get("version")
    if type(version) is not int or version != SCHEMA_VERSION:
        return _invalid("PROFILE_FILE_MALFORMED")
    settings = document.get("settings")
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        return _invalid("PROFILE_FILE_MALFORMED")
    unknown = [_name(key) for key in settings if not (isinstance(key, str) and key in SWITCHES)]
    if unknown:
        return _invalid("PROFILE_UNKNOWN_KEY", unknown)
    wrong_type = [_name(key) for key, value in settings.items() if type(value) is not bool]
    if wrong_type:
        return _invalid("PROFILE_VALUE_TYPE_INVALID", wrong_type)
    values = _defaults()
    values.update(settings)
    sources = {key: ("file" if key in settings else "default") for key in SWITCHES}
    return ProfileState("LOADED", values, sources, None)


def load_profile(path: Path | None = None) -> ProfileState:
    """Return the effective switches. Never raises: any unexpected failure falls back to strict defaults."""
    target = path if path is not None else profile_settings_path()
    try:
        return _load(target)
    except Exception:  # noqa: BLE001 - an unreadable or unexpected profile must fail closed.
        return _invalid("PROFILE_UNAVAILABLE")


def non_default_fields(state: ProfileState) -> list[str]:
    return sorted(key for key, value in state.values.items() if value != SWITCHES[key].default)


def turn_context_line(state: ProfileState | None = None) -> str:
    """One short Turn Context line: the profile name, non-default switch names and any invalid-file reason."""
    state = state or load_profile()
    parts = [f"aips_profile={PROFILE_NAME}"]
    non_default = non_default_fields(state)
    if non_default:
        parts.append("aips_profile_non_default=" + ",".join(non_default))
    if state.diagnostic:
        parts.append("aips_profile_status=INVALID reason=" + state.diagnostic["reason_code"])
    return " ".join(parts)


def diagnostic_fields(state: ProfileState | None = None) -> dict[str, Any]:
    """Publication diagnostics carry field names and a reason code only, never switch values or paths."""
    state = state or load_profile()
    return {"name": PROFILE_NAME, "status": state.status, "non_default_fields": non_default_fields(state),
            "reason_code": state.diagnostic["reason_code"] if state.diagnostic else None}


def show_payload(state: ProfileState | None = None) -> dict[str, Any]:
    state = state or load_profile()
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": PROFILE_NAME,
        "status": state.status,
        "profile_file": FILE_LABEL,
        "switches": {key: {"value": state.values[key], "default": SWITCHES[key].default, "source": state.sources[key]}
                     for key in sorted(SWITCHES)},
        "non_default_fields": non_default_fields(state),
        "diagnostic": state.diagnostic,
    }


def _write_private(path: Path, data: bytes) -> None:
    """Atomic replace with a 0600 file inside a 0700 directory."""
    directory = path.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    fd, temporary = tempfile.mkstemp(prefix=".aips-profile-", dir=directory)
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


def set_switch(key: str, raw_value: str, *, interactive: bool, read_line: Any,
               summary_stream: Any = None, path: Path | None = None) -> dict[str, Any]:
    """Change one allow-listed switch after an interactive summary and the exact typed phrase."""
    if not interactive:
        raise ProfileError("PROFILE_SET_REQUIRES_TTY", "Switching needs an interactive terminal; a person must run it there.")
    if not isinstance(key, str) or key not in SWITCHES:
        raise ProfileError("PROFILE_KEY_NOT_ALLOWED", "The key is not in the fixed switch allow-list.")
    if raw_value not in VALUE_TEXT:
        raise ProfileError("PROFILE_VALUE_INVALID", "The value must be true or false.")
    new = VALUE_TEXT[raw_value]
    target = path if path is not None else profile_settings_path()
    state = load_profile(target)
    if state.status == "INVALID":
        raise ProfileError("PROFILE_FILE_INVALID", "The profile file is invalid; it is not overwritten.")
    old = state.values[key]
    if old == new:
        raise ProfileError("PROFILE_VALUE_UNCHANGED", "The switch already has this value; nothing was written.")
    stream = summary_stream if summary_stream is not None else sys.stderr
    switch = SWITCHES[key]
    print("本機 AIPS profile 切換摘要 (AIPS profile switch summary)", file=stream)
    print(f"  file: {FILE_LABEL}", file=stream)
    print(f"  key: {key}", file=stream)
    print(f"  old: {'true' if old else 'false'}", file=stream)
    print(f"  new: {raw_value}", file=stream)
    print(f"  security implication: {switch.implication_zh} / {switch.implication_en}", file=stream)
    phrase = f"SET {key} {raw_value}"
    typed = read_line(f"請輸入確認片語 `{phrase}` 以套用，其他輸入將取消: ")
    if typed.strip() != phrase:
        raise ProfileError("PROFILE_SET_DECLINED", "The confirmation phrase did not match; nothing was written.")
    settings = {name: state.values[name] for name in SWITCHES if state.sources[name] == "file"}
    settings[key] = new
    document = {"version": SCHEMA_VERSION, "settings": dict(sorted(settings.items()))}
    _write_private(target, yaml.safe_dump(document, sort_keys=True, allow_unicode=False).encode("utf-8"))
    written = load_profile(target)
    if written.status != "LOADED" or written.values[key] != new:
        raise ProfileError("PROFILE_FILE_INVALID", "The written profile did not verify; it was left for a person to check.")
    return {"status": "UPDATED", "profile": PROFILE_NAME, "key": key, "old": old, "new": new,
            "profile_file": FILE_LABEL, "non_default_fields": non_default_fields(written)}


def _is_tty(stream: Any) -> bool:
    try:
        return bool(stream is not None and stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def _read_confirmation(prompt: str) -> str:
    """Prompts go to stderr so stdout stays the single JSON result channel."""
    sys.stderr.write(prompt)
    sys.stderr.flush()
    return sys.stdin.readline()


def _text_show(payload: dict[str, Any]) -> str:
    lines = [f"profile={payload['profile']} status={payload['status']} file={payload['profile_file']}"]
    if not payload["switches"]:
        lines.append("switches: none in this version (no relaxation is available)")
    for key, item in payload["switches"].items():
        value = "true" if item["value"] else "false"
        lines.append(f"{key}={value} source={item['source']} default={'true' if item['default'] else 'false'}")
    if payload["diagnostic"]:
        lines.append(f"diagnostic={payload['diagnostic']['reason_code']} fields={','.join(payload['diagnostic']['fields'])}")
        lines.append("recovery=" + payload["diagnostic"]["recovery"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aips profile", description="Show or change AIPS profile switches (strict by default).")
    sub = parser.add_subparsers(dest="action", required=True)
    show = sub.add_parser("show", help="Print the active profile values and the source of each.")
    show.add_argument("--format", choices=("text", "json"), default="text")
    set_parser = sub.add_parser("set", help="Change one switch in an interactive terminal after a typed confirmation phrase.")
    set_parser.add_argument("key")
    set_parser.add_argument("value", help="true or false")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "show":
        payload = show_payload()
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(_text_show(payload))
        return 0
    try:
        result = set_switch(args.key, args.value,
                            interactive=_is_tty(sys.stdin) and _is_tty(sys.stderr), read_line=_read_confirmation)
    except ProfileError as exc:
        print(json.dumps({"status": "BLOCKED", "phase": "profile_set", "reason_code": exc.reason_code,
                          "profile_file": FILE_LABEL, "recovery": RECOVERY.get(exc.reason_code, ""),
                          "message": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
