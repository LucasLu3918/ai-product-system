#!/usr/bin/env python3
"""Fast, diff-aware checks that must pass before expensive lifecycle validation."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import documentation_audience  # noqa: E402
import documentation_placement  # noqa: E402
import documentation_sync  # noqa: E402


MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(\s*(<[^>]+>|[^\s)]+)")
NODE_VERSION = re.compile(r"^v?(\d+)\.")


def markdown_files_changed(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return []
    return [path for path in result.stdout.splitlines() if path.lower().endswith(".md")]


def check_markdown_links(root: Path, paths: list[str]) -> list[str]:
    errors: list[str] = []
    for rel_path in paths:
        source = (root / rel_path).resolve()
        if not source.is_file() or not source.is_relative_to(root.resolve()):
            continue
        text = source.read_text(encoding="utf-8")
        text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\S\r\n]*$", "", text)
        for match in MARKDOWN_LINK.finditer(text):
            raw = match.group(1).strip("<>")
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target_text = unquote(parsed.path)
            if target_text.startswith("/"):
                site_root = root / "docs/human" if source.is_relative_to((root / "docs/human").resolve()) else root
                target = (site_root / target_text.lstrip("/")).resolve()
            else:
                target = (source.parent / target_text).resolve()
            if not target.is_relative_to(root.resolve()):
                errors.append(f"{rel_path}: local Markdown link escapes the repository: {raw}")
                continue
            candidates = [target]
            if target.is_dir():
                candidates.extend((target / "index.md", target / "index.html"))
            if not any(candidate.is_file() for candidate in candidates):
                errors.append(f"{rel_path}: local Markdown link target does not exist: {raw}")
    return errors


def resolve_node_binary() -> str | None:
    configured = os.environ.get("AIPS_NODE_BINARY")
    if configured:
        path = Path(configured).expanduser()
        return str(path.resolve()) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which("node")


def resolve_vitepress_entrypoint(root: Path = ROOT) -> tuple[Path | None, list[str]]:
    # This is read-only: no package install or registry access is attempted.
    configured = os.environ.get("AIPS_VITEPRESS_NODE_MODULES")
    node_modules = Path(configured).expanduser() if configured else root / "node_modules"
    if configured and not node_modules.is_absolute():
        return None, ["AIPS_VITEPRESS_NODE_MODULES must be an absolute path."]
    try:
        node_modules = node_modules.resolve(strict=True)
    except OSError:
        return None, ["VitePress dependencies are unavailable at the selected node_modules path."]
    if not node_modules.is_dir():
        return None, ["VitePress dependencies are unavailable at the selected node_modules path."]

    try:
        lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
        locked_version = lock["packages"]["node_modules/vitepress"]["version"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None, ["package-lock.json must pin an exact VitePress version before building documentation."]

    package_dir = node_modules / "vitepress"
    try:
        package = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
        installed_version = package.get("version")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None, ["VitePress package metadata is missing or invalid at the selected node_modules path."]
    if package.get("name") != "vitepress" or not isinstance(locked_version, str) or not locked_version:
        return None, ["package-lock.json or the installed VitePress package metadata is invalid."]
    if installed_version != locked_version:
        return None, ["installed VitePress version does not match the exact version pinned in package-lock.json."]

    entrypoint = package_dir / "bin/vitepress.js"
    if not entrypoint.is_file():
        return None, ["VitePress is missing its bin/vitepress.js entrypoint."]
    return entrypoint, []


def external_vitepress_resolver(root: Path, node_modules: Path) -> str:
    candidate_url = json.dumps(root.resolve().as_uri().rstrip("/") + "/")
    anchor_urls = json.dumps([
        (node_modules.parent / "__aips_resolver_anchor__.mjs").resolve().as_uri(),
        (node_modules / ".pnpm" / "__aips_pnpm_resolver_anchor__.mjs").resolve().as_uri(),
    ])
    return f"""import {{ registerHooks }} from 'node:module';
const candidateRoot = {candidate_url};
const resolverAnchors = {anchor_urls};
function isBarePackage(specifier) {{
  return !specifier.startsWith('.') && !specifier.startsWith('/') && !specifier.startsWith('node:') && !specifier.startsWith('file:');
}}
registerHooks({{
  resolve(specifier, context, nextResolve) {{
    if (context.parentURL?.startsWith(candidateRoot) && isBarePackage(specifier)) {{
      let lastError;
      for (const parentURL of resolverAnchors) {{
        try {{
          return nextResolve(specifier, {{ ...context, parentURL }});
        }} catch (error) {{
          if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error;
          lastError = error;
        }}
      }}
      throw lastError;
    }}
    return nextResolve(specifier, context);
  }}
}});
"""


def docs_build_prerequisites(root: Path = ROOT) -> tuple[str | None, list[str]]:
    node = resolve_node_binary()
    if not node:
        return None, ["documentation build requires Node.js 24 or newer; add it to PATH or set AIPS_NODE_BINARY. No package install or registry access is attempted."]
    version = subprocess.run([node, "--version"], cwd=root, capture_output=True, text=True)
    match = NODE_VERSION.match(version.stdout.strip())
    if version.returncode or not match or int(match.group(1)) < 24:
        actual = version.stdout.strip() or "unavailable"
        return node, [f"documentation build requires Node.js 24 or newer; detected {actual}. Set AIPS_NODE_BINARY or update PATH."]
    _vitepress, errors = resolve_vitepress_entrypoint(root)
    return node, errors


def build_docs_site(root: Path = ROOT) -> list[str]:
    node, errors = docs_build_prerequisites(root)
    if errors:
        return errors
    vitepress, errors = resolve_vitepress_entrypoint(root)
    if errors or vitepress is None:
        return errors
    command = [str(node), str(vitepress), "build", "docs/human"]
    configured = os.environ.get("AIPS_VITEPRESS_NODE_MODULES")
    if configured:
        node_modules = vitepress.parents[2]
        with tempfile.TemporaryDirectory(prefix="aips-vitepress-resolver-") as temporary:
            resolver = Path(temporary) / "resolver.mjs"
            resolver.write_text(external_vitepress_resolver(root, node_modules), encoding="utf-8")
            child_env = os.environ.copy()
            import_option = f"--import={resolver.as_uri()}"
            child_env["NODE_OPTIONS"] = " ".join(filter(None, [child_env.get("NODE_OPTIONS", "").strip(), import_option]))
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, env=child_env)
    else:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stdout + "\n" + result.stderr).strip().splitlines()[-12:]
        return ["documentation site build failed: " + " | ".join(detail)]
    return []


def run(base: str, head: str, docs_build: bool = False) -> list[str]:
    errors: list[str] = []
    diff = subprocess.run(
        ["git", "diff", "--check", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if diff.returncode:
        errors.append(f"git diff --check failed: {diff.stdout.strip() or diff.stderr.strip()}")

    changed_markdown = markdown_files_changed(base, head)
    try:
        files = documentation_sync.changed_files_from_git(base, head)
    except Exception as exc:
        files = []
        errors.append(f"Documentation consistency failed: {exc}")
    errors.extend(f"Markdown links: {item}" for item in check_markdown_links(ROOT, changed_markdown))
    if docs_build and any(path.startswith("docs/human/") or path in {"package.json", "package-lock.json"} for path in files):
        errors.extend(build_docs_site())

    sync_config = yaml.safe_load((ROOT / "config/documentation-sync.yaml").read_text(encoding="utf-8")) or {}
    errors.extend(
        f"Documentation consistency: {item}"
        for item in documentation_sync.evaluate_changes(files, sync_config)
    )

    previous = os.environ.get("AIPS_DOCS_DIFF_BASE")
    os.environ["AIPS_DOCS_DIFF_BASE"] = base
    try:
        errors.extend(
            f"Documentation placement: {item}"
            for item in documentation_placement.audit()
        )
    finally:
        if previous is None:
            os.environ.pop("AIPS_DOCS_DIFF_BASE", None)
        else:
            os.environ["AIPS_DOCS_DIFF_BASE"] = previous

    audience_config = documentation_audience.load_config(ROOT / "config/documentation-audience.yaml")
    errors.extend(
        f"Documentation audience: {item}"
        for item in documentation_audience.validate_layout(ROOT, audience_config)
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--docs-build", action="store_true", help="Build the VitePress documentation site when documentation paths changed.")
    args = parser.parse_args()
    errors = run(args.base, args.head, docs_build=args.docs_build)
    if errors:
        print("REPOSITORY PREFLIGHT FAILED")
        for item in errors:
            print(f"- {item}")
        return 1
    print("REPOSITORY PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
