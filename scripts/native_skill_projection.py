"""Install AIPS catalog Skills into native Agent Skill discovery directories."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from skill_index import UniqueLoader, generate

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"codex", "claude", "gemini"}
SKILL_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
UPSTREAM_CANONICAL_SKIP_DETAIL = "Use the canonical AIPS Skill with this ID; no upstream duplicate was written."


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def config_root() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(configured).expanduser() if configured and Path(configured).is_absolute() else Path.home() / ".config"
    return base / "aips"


def manifest_path() -> Path:
    return config_root() / "skills" / "ownership.json"


def _safe_path(path: Path) -> None:
    absolute = path.absolute()
    for item in (absolute, *absolute.parents):
        if item.is_symlink() and str(item) not in {"/tmp", "/var"}:
            raise ValueError(f"symlink refused: {item}")


def _skill_root(host: str, scope: str, project: Path) -> Path:
    if host not in HOSTS:
        raise ValueError(f"unsupported Agent host: {host}")
    if scope not in {"user", "workspace"}:
        raise ValueError("scope must be user or workspace")
    base = Path.home() if scope == "user" else project.resolve()
    parent = ".claude" if host == "claude" else ".agents"
    return base / parent / "skills"


def _alternate_roots(host: str, scope: str, project: Path) -> list[Path]:
    base = Path.home() if scope == "user" else project.resolve()
    if host == "codex":
        return [base / ".codex" / "skills"]
    if host == "gemini":
        return [base / ".gemini" / "skills"]
    return []


def _source_package(root: Path, skill_id: str) -> tuple[dict[str, bytes], str]:
    catalog = generate(root)["skills"]
    metadata = catalog.get(skill_id)
    if metadata is None:
        raise ValueError(f"unknown AIPS Skill: {skill_id}")
    skills_dir = (root / "skills").resolve()
    source = root / "skills" / metadata["path"]
    _safe_path(source)
    if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(skills_dir):
        raise ValueError(f"Skill source is missing or outside skills/: {skill_id}")
    directory = source.parent.resolve()
    text = source.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError(f"Skill source has invalid frontmatter: {skill_id}")
    frontmatter = yaml.load(match.group(1), Loader=UniqueLoader)
    if not isinstance(frontmatter, dict) or frontmatter.get("id") != skill_id:
        raise ValueError(f"Skill source identity mismatch: {skill_id}")
    body = text[match.end():]
    body = _rewrite_references(body, root.resolve(), source.resolve(), directory)
    header = yaml.safe_dump(
        {"name": skill_id, "description": metadata["description"]},
        sort_keys=False,
        allow_unicode=True,
    )
    generated = (
        "---\n" + header + "---\n\n"
        + f"AIPS catalog Skill `{skill_id}`. Canonical source: `{source.resolve()}`. "
        + "This native projection is managed by AIPS; edit the canonical source and reinstall.\n\n"
        + body
    ).encode("utf-8")
    files: dict[str, bytes] = {"SKILL.md": generated}
    source_hashes = {"SKILL.md": digest(source.read_bytes())}
    for item in sorted(directory.rglob("*")):
        _safe_path(item)
        if item.is_symlink():
            raise ValueError(f"symlinked Skill resource is not installable: {item}")
        if item.is_dir():
            continue
        if not item.is_file() or item == source:
            continue
        relative = item.relative_to(directory).as_posix()
        _validate_relative(relative)
        raw = item.read_bytes()
        if item.suffix.lower() == ".md":
            resource = raw.decode("utf-8")
            resource = _rewrite_references(resource, root.resolve(), item.resolve(), directory)
            raw = resource.encode("utf-8")
        files[relative] = raw
        source_hashes[relative] = digest(item.read_bytes())
    source_digest = hashlib.sha256(
        json.dumps(source_hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return files, source_digest


def _upstream_records(root: Path) -> list[dict[str, Any]]:
    path = root / "skills" / "integrations" / "matt-pocock-skills.json"
    _safe_path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("reviewed upstream Skill inventory is missing or unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"reviewed upstream Skill inventory is invalid: {exc}") from exc
    records = payload.get("skills") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise TypeError("reviewed upstream Skill inventory has no skills list")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("reviewed upstream Skill record must be an object")
        identifier = str(record.get("id") or "")
        if not SKILL_ID.fullmatch(identifier) or identifier in seen:
            raise ValueError("reviewed upstream Skill IDs must be valid and unique")
        seen.add(identifier)
    return records


def _upstream_source_package(
    root: Path, record: dict[str, Any]
) -> tuple[dict[str, bytes], str]:
    identifier = str(record.get("id") or "")
    relative_source = str(record.get("local_path") or "")
    _validate_relative(relative_source)
    source_root = (root / "external-skills" / "matt-pocock").resolve()
    source = root / relative_source
    _safe_path(source)
    if (
        source.is_symlink()
        or source.name != "SKILL.md"
        or not source.is_file()
        or not source.resolve().is_relative_to(source_root)
    ):
        raise ValueError(f"upstream Skill source is missing or outside its vendored root: {identifier}")
    source_bytes = source.read_bytes()
    expected_sha = str(record.get("sha256") or "")
    if not SHA256.fullmatch(expected_sha) or digest(source_bytes) != expected_sha:
        raise ValueError(f"upstream Skill source digest does not match the reviewed inventory: {identifier}")
    try:
        text = source_bytes.decode("utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
        if not match:
            raise ValueError("missing YAML frontmatter")
        frontmatter = yaml.load(match.group(1), Loader=UniqueLoader)
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"upstream Skill frontmatter is invalid: {identifier}: {exc}") from exc
    if not isinstance(frontmatter, dict) or frontmatter.get("name") != identifier:
        raise ValueError(f"upstream Skill identity does not match the reviewed inventory: {identifier}")

    directory = source.parent.resolve()
    files: dict[str, bytes] = {}
    source_hashes: dict[str, str] = {}
    for item in sorted(directory.rglob("*")):
        _safe_path(item)
        if item.is_symlink():
            raise ValueError(f"symlinked upstream Skill resource is not installable: {item}")
        if item.is_dir():
            continue
        if not item.is_file():
            raise ValueError(f"unsupported upstream Skill resource: {item}")
        relative = item.relative_to(directory).as_posix()
        _validate_relative(relative)
        raw = item.read_bytes()
        files[relative] = raw
        source_hashes[relative] = digest(raw)
    if files.get("SKILL.md") != source_bytes:
        raise ValueError(f"upstream Skill package does not contain its reviewed entrypoint: {identifier}")
    source_digest = hashlib.sha256(
        json.dumps(source_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return files, source_digest


def _explicit_upstream_projection(
    files: dict[str, bytes], hosts: list[str], *, skill_id: str, description: str
) -> dict[str, bytes]:
    """Apply native explicit-invocation controls without changing vendored source."""
    projected = dict(files)
    if "claude" in hosts:
        raw = projected.get("SKILL.md")
        if raw is None:
            raise ValueError("upstream Skill package has no SKILL.md entrypoint")
        text = raw.decode("utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---((?:\r?\n|$).*)\Z", text, re.DOTALL)
        if not match:
            raise ValueError("upstream Skill frontmatter is invalid")
        frontmatter = yaml.load(match.group(1), Loader=UniqueLoader)
        if not isinstance(frontmatter, dict):
            raise ValueError("upstream Skill frontmatter must be a mapping")
        frontmatter["disable-model-invocation"] = True
        projected["SKILL.md"] = (
            "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
            + "---" + match.group(2)
        ).encode("utf-8")
    if "codex" in hosts:
        policy_path = "agents/openai.yaml"
        raw = projected.get(policy_path)
        try:
            metadata = yaml.load(raw.decode("utf-8"), Loader=UniqueLoader) if raw is not None else {}
        except (UnicodeError, yaml.YAMLError) as exc:
            raise ValueError(f"upstream Codex Skill metadata is invalid: {exc}") from exc
        if not isinstance(metadata, dict):
            raise ValueError("upstream Codex Skill metadata must be a mapping")
        interface = metadata.get("interface")
        if interface is None:
            interface = {}
        if not isinstance(interface, dict):
            raise ValueError("upstream Codex Skill interface must be a mapping")
        interface.setdefault("display_name", skill_id.replace("-", " ").title())
        interface.setdefault("short_description", description)
        metadata["interface"] = interface
        policy = metadata.get("policy")
        if policy is None:
            policy = {}
        if not isinstance(policy, dict):
            raise ValueError("upstream Codex Skill policy must be a mapping")
        policy["allow_implicit_invocation"] = False
        metadata["policy"] = policy
        projected[policy_path] = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).encode("utf-8")
    return projected


def install_upstream(
    root: Path,
    skill_ids: list[str] | None,
    hosts: list[str],
    *,
    scope: str = "user",
    project: Path | None = None,
    all_upstream: bool = False,
) -> dict[str, Any]:
    records = _upstream_records(root)
    selected_hosts = sorted(set(hosts))
    if not selected_hosts or any(host not in HOSTS for host in selected_hosts):
        raise ValueError("select one or more supported hosts: codex, claude, gemini")
    by_id = {str(record["id"]): record for record in records}
    selected_ids = sorted(by_id) if all_upstream else sorted(set(skill_ids or []))
    if not selected_ids:
        raise ValueError("select at least one upstream Skill or --all")
    unknown = sorted(set(selected_ids) - set(by_id))
    if unknown:
        raise ValueError("unknown upstream Skill ID(s): " + ", ".join(unknown))

    catalog_ids = set(generate(root)["skills"])
    packages_by_host_group: dict[tuple[str, ...], dict[str, tuple[dict[str, bytes], str]]] = {}
    results: list[dict[str, str]] = []
    for identifier in selected_ids:
        record = by_id[identifier]
        if identifier in catalog_ids:
            results.append({
                "skill_id": identifier, "source": "upstream", "host": ",".join(selected_hosts),
                "scope": scope, "status": "SKIPPED_CANONICAL", "path": "",
                "detail": UPSTREAM_CANONICAL_SKIP_DETAIL,
            })
            continue
        source_files, source_digest = _upstream_source_package(root, record)
        for host_group in sorted({("claude",) if host == "claude" else ("codex", "gemini") for host in selected_hosts}):
            files = _explicit_upstream_projection(
                source_files, list(host_group), skill_id=identifier,
                description=str(record.get("description") or identifier),
            )
            packages_by_host_group.setdefault(host_group, {})[identifier] = (files, source_digest)

    source_ids = {identifier: f"matt-pocock-skills:{identifier}" for identifier in selected_ids if identifier not in catalog_ids}
    statuses: list[str] = []
    for host_group, packages in sorted(packages_by_host_group.items()):
        installed = _install_packages(
            packages, list(host_group), scope=scope, project=project or Path.cwd(),
            source_kind="upstream", source_ids=source_ids,
        )
        for row in installed["results"]:
            row["source"] = "upstream"
        results.extend(installed["results"])
        statuses.append(installed["status"])
    status = "CONFLICT" if "CONFLICT" in statuses else "READY"
    return {"status": status, "results": sorted(results, key=lambda row: (row["skill_id"], row.get("host", "")))}


def _rewrite_references(text: str, root: Path, source: Path, skill_dir: Path) -> str:
    def repo_reference(match: re.Match[str]) -> str:
        relative = match.group(1)
        return "`" + str(root / relative) + "`"

    text = re.sub(
        r"`((?:orchestration|templates|scripts|skills|docs|core|harness|config)/[^`]+|SYSTEM(?:_CORE)?\.md)`",
        repo_reference,
        text,
    )

    def markdown_link(match: re.Match[str]) -> str:
        target = match.group(1)
        if re.match(r"(?:[a-z][a-z0-9+.-]*:|#)", target, re.IGNORECASE):
            return match.group(0)
        path_part, separator, anchor = target.partition("#")
        resolved = (source.parent / path_part).resolve()
        if resolved.is_relative_to(skill_dir.resolve()):
            return match.group(0)
        if resolved.is_relative_to(root):
            rewritten = str(resolved)
            if separator:
                rewritten += "#" + anchor
            return match.group(0).replace(target, rewritten)
        return match.group(0)

    return re.sub(r"\]\(([^)]+)\)", markdown_link, text)


def _validate_relative(relative: str) -> None:
    parsed = PurePosixPath(relative)
    if (
        not relative
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parsed.parts)
        or "\\" in relative
        or "\x00" in relative
    ):
        raise ValueError(f"invalid Skill resource path: {relative!r}")


def _target(root: Path, skill_id: str, relative: str) -> Path:
    if not SKILL_ID.fullmatch(skill_id):
        raise ValueError(f"invalid Skill id: {skill_id!r}")
    _validate_relative(relative)
    result = root / skill_id / Path(*PurePosixPath(relative).parts)
    _safe_path(result)
    if not result.resolve(strict=False).is_relative_to(root.resolve(strict=False)):
        raise ValueError("Skill target escapes its discovery root")
    return result


def _load_manifest() -> dict[str, Any]:
    path = manifest_path()
    _safe_path(path)
    if not path.exists():
        return {"version": 1, "artifacts": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid native Skill ownership manifest: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("artifacts"), list):
        raise ValueError("invalid native Skill ownership manifest schema")
    for artifact in data["artifacts"]:
        if (
            not isinstance(artifact, dict)
            or not SKILL_ID.fullmatch(str(artifact.get("skill_id", "")))
            or artifact.get("scope") not in {"user", "workspace"}
            or not isinstance(artifact.get("host_root"), str)
            or not isinstance(artifact.get("hosts"), list)
            or len(set(artifact["hosts"])) != len(artifact["hosts"])
            or any(host not in HOSTS for host in artifact["hosts"])
            or not isinstance(artifact.get("files"), dict)
            or not artifact["files"]
            or artifact.get("source_kind") not in {"catalog", "portable-command", "upstream"}
            or not isinstance(artifact.get("source_id"), str)
            or not artifact["source_id"]
            or not isinstance(artifact.get("source_digest"), str)
            or not SHA256.fullmatch(artifact["source_digest"])
        ):
            raise ValueError("invalid native Skill ownership record")
        if artifact["scope"] == "workspace":
            project_root = artifact.get("project_root")
            if not isinstance(project_root, str) or not Path(project_root).is_absolute():
                raise ValueError("workspace Skill ownership record has no absolute project root")
            project = Path(project_root)
        else:
            project = Path.cwd()
            if artifact.get("project_root") is not None:
                raise ValueError("user Skill ownership record has an unexpected project root")
        recorded_root = Path(artifact["host_root"]).resolve(strict=False)
        for host in artifact["hosts"]:
            expected_root = _skill_root(host, artifact["scope"], project).resolve(strict=False)
            if expected_root != recorded_root:
                raise ValueError("native Skill ownership root does not match its recorded host")
        for relative, file_hash in artifact["files"].items():
            _validate_relative(relative)
            if not isinstance(file_hash, str) or not SHA256.fullmatch(file_hash):
                raise ValueError("invalid native Skill file digest")
    return data


@contextlib.contextmanager
def _locked_manifest() -> Iterator[dict[str, Any]]:
    path = manifest_path()
    lock_path = path.with_suffix(".lock")
    _safe_path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            stream.seek(0)
            if stream.read(1) == b"":
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield _load_manifest()
        finally:
            if os.name == "nt":
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _save_manifest(data: dict[str, Any]) -> None:
    path = manifest_path()
    _safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".aips-skills-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _safe_path(path)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _atomic_write(path: Path, raw: bytes) -> None:
    _safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".aips-skill-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _safe_path(path)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _artifact_index(artifacts: list[dict[str, Any]], skill_id: str, scope: str, host_root: Path) -> int | None:
    wanted = str(host_root.resolve(strict=False))
    for index, item in enumerate(artifacts):
        if item.get("skill_id") == skill_id and item.get("scope") == scope and item.get("host_root") == wanted:
            return index
    return None


def _check_directory(directory: Path, files: dict[str, bytes]) -> tuple[bool, list[str]]:
    conflicts: list[str] = []
    for relative, raw in files.items():
        path = _target(directory.parent, directory.name, relative)
        if path.exists():
            if not path.is_file() or path.is_symlink() or digest(path.read_bytes()) != digest(raw):
                conflicts.append(relative)
        else:
            conflicts.append(relative)
    return not conflicts, conflicts


def _write_new(directory: Path, files: dict[str, bytes]) -> None:
    for relative, raw in files.items():
        _atomic_write(_target(directory.parent, directory.name, relative), raw)


def _existing_discovery(host: str, scope: str, project: Path, skill_id: str) -> Path | None:
    for alternate in _alternate_roots(host, scope, project):
        candidate = alternate / skill_id
        _safe_path(candidate)
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return None


def _install_packages(
    packages: dict[str, tuple[dict[str, bytes], str]],
    hosts: list[str],
    *,
    scope: str,
    project: Path,
    source_kind: str,
    source_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    selected = sorted(set(hosts))
    if not selected or any(host not in HOSTS for host in selected):
        raise ValueError("select one or more supported hosts: codex, claude, gemini")
    if scope not in {"user", "workspace"}:
        raise ValueError("scope must be user or workspace")
    project_root = project.resolve()
    results: list[dict[str, str]] = []
    with _locked_manifest() as manifest:
        artifacts = manifest["artifacts"]
        for host in selected:
            host_root = _skill_root(host, scope, project_root)
            _safe_path(host_root)
            for skill_id, (files, source_digest) in packages.items():
                if not SKILL_ID.fullmatch(skill_id):
                    raise ValueError(f"invalid native Skill id: {skill_id!r}")
                index = _artifact_index(artifacts, skill_id, scope, host_root)
                source_id = (source_ids or {}).get(skill_id, skill_id)
                if index is None:
                    directory = host_root / skill_id
                    alternate = _existing_discovery(host, scope, project_root, skill_id)
                    existing = alternate or directory
                    if existing.exists() or existing.is_symlink():
                        if not existing.is_dir() or existing.is_symlink():
                            results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": "CONFLICT", "path": str(existing)})
                            continue
                        matches, conflicts = _check_directory(existing, files)
                        status = "ALREADY_PRESENT_UNOWNED" if matches else "CONFLICT"
                        results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": status, "path": str(existing), "detail": "" if matches else ",".join(conflicts)})
                        continue
                    _write_new(directory, files)
                    artifacts.append({
                        "skill_id": skill_id, "scope": scope,
                        "host_root": str(host_root.resolve(strict=False)),
                        "project_root": str(project_root) if scope == "workspace" else None,
                        "hosts": [host], "source_kind": source_kind, "source_id": source_id,
                        "source_digest": source_digest,
                        "files": {relative: digest(raw) for relative, raw in files.items()},
                    })
                    results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": "INSTALLED", "path": str(directory)})
                    continue

                artifact = artifacts[index]
                directory = host_root / skill_id
                if artifact.get("source_kind") != source_kind or artifact.get("source_id") != source_id:
                    results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": "CONFLICT", "path": str(directory), "detail": "native Skill name is already owned by a different AIPS source"})
                    continue
                if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
                    results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": "CONFLICT", "path": str(directory)})
                    continue
                conflicts: list[str] = []
                for relative, old_hash in artifact["files"].items():
                    path = _target(host_root, skill_id, relative)
                    if path.exists() and (not path.is_file() or path.is_symlink() or digest(path.read_bytes()) != old_hash):
                        conflicts.append(relative)
                for relative in files:
                    path = _target(host_root, skill_id, relative)
                    if path.exists() and relative not in artifact["files"]:
                        conflicts.append(relative)
                if conflicts:
                    results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": "CONFLICT", "path": str(directory), "detail": ",".join(sorted(set(conflicts)) )})
                    continue
                current = artifact.get("source_digest") == source_digest and all(
                    _target(host_root, skill_id, relative).is_file()
                    and digest(_target(host_root, skill_id, relative).read_bytes()) == digest(raw)
                    for relative, raw in files.items()
                ) and set(artifact["files"]) == set(files)
                already_registered = host in artifact["hosts"]
                artifact["hosts"] = sorted(set(artifact["hosts"]) | {host})
                if not current:
                    for relative in set(artifact["files"]) - set(files):
                        stale = _target(host_root, skill_id, relative)
                        if stale.is_file():
                            stale.unlink()
                    _write_new(directory, files)
                    artifact["files"] = {relative: digest(raw) for relative, raw in files.items()}
                    artifact["source_digest"] = source_digest
                status = "CURRENT" if current and already_registered else "SHARED" if current else "UPDATED"
                results.append({"skill_id": skill_id, "host": host, "scope": scope, "status": status, "path": str(directory)})
        _save_manifest(manifest)
    return {"status": "CONFLICT" if any(item["status"] == "CONFLICT" for item in results) else "READY", "results": results}


def install(
    root: Path,
    skill_ids: list[str],
    hosts: list[str],
    *,
    scope: str = "user",
    project: Path | None = None,
) -> dict[str, Any]:
    ids = sorted(set(skill_ids))
    catalog = generate(root)["skills"]
    if not ids or any(skill_id not in catalog for skill_id in ids):
        unknown = sorted(set(ids) - set(catalog))
        raise ValueError("select at least one catalog Skill" + (f"; unknown: {', '.join(unknown)}" if unknown else ""))
    packages = {skill_id: _source_package(root, skill_id) for skill_id in ids}
    return _install_packages(packages, hosts, scope=scope, project=project or Path.cwd(), source_kind="catalog")


def install_external(
    skill_id: str,
    content: str,
    hosts: list[str],
    *,
    source_id: str,
    scope: str = "user",
    project: Path | None = None,
) -> dict[str, Any]:
    if not SKILL_ID.fullmatch(skill_id):
        raise ValueError(f"invalid native Skill id: {skill_id!r}")
    files = {"SKILL.md": content.encode("utf-8")}
    source_digest = digest(files["SKILL.md"])
    return _install_packages(
        {skill_id: (files, source_digest)}, hosts, scope=scope,
        project=project or Path.cwd(), source_kind="portable-command",
        source_ids={skill_id: source_id},
    )


def _remove_empty_directories(directory: Path, stop: Path) -> None:
    current = directory
    stop = stop.resolve(strict=False)
    while current != stop and current.resolve(strict=False).is_relative_to(stop):
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def uninstall(
    hosts: list[str],
    skill_ids: list[str] | None = None,
    *,
    scope: str | None = None,
    project: Path | None = None,
    all_owned: bool = False,
    source_kind: str | None = None,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    selected = sorted(set(hosts))
    if not selected or any(host not in HOSTS for host in selected):
        raise ValueError("select one or more supported hosts: codex, claude, gemini")
    wanted = set(skill_ids or [])
    if not wanted and not all_owned:
        raise ValueError("select a Skill id or --all")
    project_root = (project or Path.cwd()).resolve()
    results: list[dict[str, str]] = []
    with _locked_manifest() as manifest:
        owned_before = {
            item["skill_id"] for item in manifest["artifacts"]
            if (source_kind is None or item.get("source_kind") == source_kind)
            and (source_ids is None or item.get("source_id") in set(source_ids))
            and (scope is None or item.get("scope") == scope)
            and (item.get("scope") != "workspace" or item.get("project_root") == str(project_root))
            and (set(item.get("hosts", [])) & set(selected))
        }
        retained: list[dict[str, Any]] = []
        for artifact in manifest["artifacts"]:
            skill_id = artifact["skill_id"]
            artifact_scope = artifact["scope"]
            host_root = Path(artifact["host_root"])
            matching_hosts = set(artifact["hosts"]) & set(selected)
            project_matches = artifact_scope != "workspace" or artifact.get("project_root") == str(project_root)
            applies = (scope is None or scope == artifact_scope) and (not wanted or skill_id in wanted) and project_matches
            if source_kind is not None and artifact.get("source_kind") != source_kind:
                applies = False
            if source_ids is not None and artifact.get("source_id") not in set(source_ids):
                applies = False
            if not matching_hosts or not applies:
                retained.append(artifact)
                continue
            for host in sorted(matching_hosts):
                expected_root = _skill_root(host, artifact_scope, project_root)
                if str(expected_root.resolve(strict=False)) != artifact["host_root"]:
                    results.append({"skill_id": skill_id, "host": host, "scope": artifact_scope, "status": "CONFLICT", "path": str(host_root), "detail": "ownership root mismatch"})
                    continue
                artifact["hosts"].remove(host)
            if artifact["hosts"]:
                results.append({"skill_id": skill_id, "host": ",".join(sorted(matching_hosts)), "scope": artifact_scope, "status": "RETAINED_SHARED", "path": str(host_root / skill_id)})
                retained.append(artifact)
                continue
            directory = host_root / skill_id
            leftovers: dict[str, str] = {}
            for relative, expected_hash in artifact["files"].items():
                path = _target(host_root, skill_id, relative)
                if not path.exists():
                    continue
                if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected_hash:
                    leftovers[relative] = expected_hash
                    continue
                path.unlink()
            _remove_empty_directories(directory, host_root)
            if leftovers:
                results.append({"skill_id": skill_id, "host": ",".join(sorted(matching_hosts)), "scope": artifact_scope, "status": "CONFLICT_PRESERVED", "path": str(directory), "detail": ",".join(sorted(leftovers))})
            else:
                results.append({"skill_id": skill_id, "host": ",".join(sorted(matching_hosts)), "scope": artifact_scope, "status": "REMOVED", "path": str(directory)})
        missing = wanted - owned_before
        for skill_id in sorted(missing):
            results.append({"skill_id": skill_id, "host": ",".join(selected), "scope": scope or "all", "status": "NOT_OWNED", "path": ""})
        manifest["artifacts"] = retained
        _save_manifest(manifest)
    if source_kind is not None:
        for row in results:
            row["source"] = source_kind
    return {"status": "CONFLICT" if any(item["status"] in {"CONFLICT", "CONFLICT_PRESERVED"} for item in results) else "READY", "results": results}


def status(
    hosts: list[str] | None = None,
    *,
    scope: str | None = None,
    project: Path | None = None,
    root: Path | None = None,
    source_kind: str | None = None,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    selected = set(hosts or HOSTS)
    if any(host not in HOSTS for host in selected):
        raise ValueError("unsupported Agent host")
    project_root = (project or Path.cwd()).resolve()
    catalog = generate(root or ROOT)["skills"]
    results: list[dict[str, str]] = []
    with _locked_manifest() as manifest:
        for artifact in manifest["artifacts"]:
            if source_kind is not None and artifact.get("source_kind") != source_kind:
                continue
            if source_ids is not None and artifact.get("source_id") not in set(source_ids):
                continue
            active_hosts = sorted(set(artifact["hosts"]) & selected)
            if not active_hosts or (scope is not None and scope != artifact["scope"]):
                continue
            if artifact["scope"] == "workspace" and artifact.get("project_root") != str(project_root):
                continue
            host_root = Path(artifact["host_root"])
            try:
                expected = _skill_root(active_hosts[0], artifact["scope"], project_root).resolve(strict=False)
            except (OSError, ValueError):
                expected = None
            directory = host_root / artifact["skill_id"]
            state = "CURRENT"
            if expected is None or str(expected) != artifact["host_root"]:
                state = "CONFLICT"
            else:
                for relative, expected_hash in artifact["files"].items():
                    path = _target(host_root, artifact["skill_id"], relative)
                    if not path.is_file():
                        state = "MISSING"
                        break
                    if path.is_symlink() or digest(path.read_bytes()) != expected_hash:
                        state = "CONFLICT"
                        break
                if state == "CURRENT" and artifact.get("source_kind") == "catalog" and artifact["skill_id"] in catalog:
                    try:
                        _files, current_source_digest = _source_package(root or ROOT, artifact["skill_id"])
                    except (OSError, ValueError, yaml.YAMLError):
                        current_source_digest = ""
                    if current_source_digest != artifact.get("source_digest"):
                        state = "STALE"
                elif state == "CURRENT" and artifact.get("source_kind") == "upstream":
                    try:
                        upstream = next(
                            item for item in _upstream_records(root or ROOT)
                            if item.get("id") == artifact["skill_id"]
                        )
                        _files, current_source_digest = _upstream_source_package(root or ROOT, upstream)
                    except (OSError, StopIteration, ValueError, yaml.YAMLError):
                        current_source_digest = ""
                    if current_source_digest != artifact.get("source_digest"):
                        state = "STALE"
            results.append({
                "skill_id": artifact["skill_id"],
                "source": artifact.get("source_kind", ""),
                "source_id": artifact.get("source_id", ""),
                "hosts": ",".join(active_hosts),
                "scope": artifact["scope"],
                "status": state,
                "path": str(directory),
            })
    overall = "READY" if all(item["status"] == "CURRENT" for item in results) else "DRIFT"
    return {"status": overall, "results": results}
