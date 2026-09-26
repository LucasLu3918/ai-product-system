#!/usr/bin/env python3
"""Bounded, offline-first adapters for external Eval and red-team evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 1_000_000
MAX_DEPTH = 20
MAX_NODES = 10_000
MAX_CASES = 100
MAX_TEXT = 20_000
FORBIDDEN_KEYS = {
    "analysis", "chain_of_thought", "chain-of-thought", "cot", "private_reasoning",
    "reasoning_trace", "scratchpad", "thoughts", "reasoning",
}
SENSITIVE_KEY = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|secret|private[_-]?key)")
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]{8,}"),
)
PROMPTFOO_ASSERTIONS = {"equals", "contains", "not-contains", "is-json"}
PROMPTFOO_ROOT_KEYS = {"description", "prompts", "providers", "tests"}
PROMPTFOO_RESULT_KEYS = {"vars", "response", "success", "score"}
PROMPTFOO_PROVIDER = re.compile(r"openai:(?:chat:)?[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}\Z")


class InputError(ValueError):
    pass


class UniqueSafeLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys and aliases."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            raise InputError("YAML aliases are not supported")
        return super().compose_node(parent, index)


class NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _construct_mapping(loader: UniqueSafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise InputError("YAML mapping keys must be scalar") from exc
        if duplicate:
            raise InputError("duplicate YAML mapping key")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _validate_tree(value: Any, depth: int = 0, counter: list[int] | None = None) -> None:
    counter = counter if counter is not None else [0]
    counter[0] += 1
    if counter[0] > MAX_NODES or depth > MAX_DEPTH:
        raise InputError("input exceeds structural limits")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, (str, int, float, bool)):
                raise InputError("mapping keys must be scalar")
            _validate_tree(child, depth + 1, counter)
    elif isinstance(value, list):
        for child in value:
            _validate_tree(child, depth + 1, counter)
    elif isinstance(value, str) and len(value) > MAX_TEXT:
        raise InputError("text field exceeds size limit")
    elif isinstance(value, float) and not math.isfinite(value):
        raise InputError("non-finite numeric values are not supported")


def parse_yaml_bytes(raw: bytes, *, label: str = "YAML") -> Any:
    if len(raw) > MAX_BYTES:
        raise InputError(f"{label} exceeds byte limit")
    try:
        text = raw.decode("utf-8")
        depth = 0
        for nodes, event in enumerate(yaml.parse(text, Loader=UniqueSafeLoader), start=1):
            if nodes > MAX_NODES:
                raise InputError("input exceeds structural limits")
            if isinstance(event, yaml.NodeEvent) and getattr(event, "tag", None):
                raise InputError("explicit YAML tags are not supported")
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
                if depth > MAX_DEPTH:
                    raise InputError("input exceeds structural limits")
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
        data = yaml.load(text, Loader=UniqueSafeLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise InputError(f"invalid {label}") from exc
    if data is None:
        data = {}
    _validate_tree(data)
    _validate_sensitive(data)
    return data


def load_yaml(path: Path) -> Any:
    try:
        return parse_yaml_bytes(read_bounded(path, "YAML file"), label="YAML file")
    except OSError as exc:
        raise InputError("cannot read YAML file") from exc


def read_bounded(path: Path, label: str) -> bytes:
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise InputError(f"cannot read {label}") from exc
    if len(raw) > MAX_BYTES:
        raise InputError(f"{label} exceeds byte limit")
    return raw


def _validate_sensitive(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        keys = [str(key).strip().lower() for key in value]
        if any(key in FORBIDDEN_KEYS for key in keys):
            raise InputError("private reasoning field is prohibited")
        if any(SENSITIVE_KEY.search(key) for key in keys):
            raise InputError("secret-like field name is prohibited")
        for child in value.values():
            _validate_sensitive(child, f"{path}.field")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                raise InputError("secret-like value is prohibited")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_json(value))


def fingerprint_evidence(value: dict[str, Any]) -> str:
    unsigned = {key: child for key, child in value.items() if key != "fingerprint"}
    return digest_value(unsigned)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise InputError(f"{label} must be a mapping with string keys")
    return value


def _keys(value: dict[str, Any], allowed: set[str], label: str, required: set[str] = frozenset()) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise InputError(f"unsupported {label} field")
    if missing:
        raise InputError(f"missing {label} key: {missing[0]}")


def _text(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or len(value) > MAX_TEXT or (nonempty and not value.strip()):
        raise InputError(f"{label} must be a bounded {'non-empty ' if nonempty else ''}string")
    return value


def validate_case(case: Any) -> dict[str, Any]:
    case = _mapping(case, "Agent Eval case")
    _keys(case, {"version", "id", "scenario_id", "description", "input", "rubric", "source", "provenance"}, "Agent Eval case", {"version", "id", "scenario_id", "input", "rubric"})
    if case.get("version") != 1 or not isinstance(case.get("id"), str):
        raise InputError("invalid Agent Eval case identity")
    scenario_id = str(case.get("scenario_id") or "")
    if not re.fullmatch(r"\d{3}", scenario_id):
        raise InputError("Agent Eval case requires a 3-digit scenario_id")
    inp = _mapping(case.get("input"), "case.input")
    _keys(inp, {"prompt", "context", "vars"}, "case.input", {"prompt"})
    prompt = _text(inp.get("prompt"), "case.input.prompt")
    variables = inp.get("vars", inp.get("context", {}))
    variables = _mapping(variables, "case.input.vars")
    for key, value in variables.items():
        _text(key, "case input variable name")
        if not isinstance(value, (str, int, float, bool)):
            raise InputError("case input variables must be scalar")
    rubric = _mapping(case.get("rubric", {}), "case.rubric")
    _keys(rubric, {"equals", "contains", "excludes", "set_equals", "nonempty"}, "case.rubric")
    for field in ("equals", "contains", "excludes", "set_equals"):
        if field in rubric and not isinstance(rubric[field], dict):
            raise InputError(f"case.rubric.{field} must be a mapping")
    if "nonempty" in rubric and (not isinstance(rubric["nonempty"], list) or not all(isinstance(path, str) for path in rubric["nonempty"])):
        raise InputError("case.rubric.nonempty must be a list of paths")
    return {"id": case["id"], "scenario_id": scenario_id, "prompt": prompt, "vars": variables, "rubric": rubric}


def _parse_promptfoo_config(doc: Any) -> tuple[str, str, list[dict[str, Any]]]:
    config = _mapping(doc, "Promptfoo config")
    _keys(config, PROMPTFOO_ROOT_KEYS, "Promptfoo config", {"prompts", "providers", "tests"})
    prompts, providers, tests = config["prompts"], config["providers"], config["tests"]
    if not isinstance(prompts, list) or len(prompts) != 1 or not isinstance(prompts[0], str):
        raise InputError("Promptfoo import supports exactly one inline prompt")
    if not isinstance(providers, list) or len(providers) != 1 or not isinstance(providers[0], str):
        raise InputError("Promptfoo import supports exactly one built-in provider")
    if not PROMPTFOO_PROVIDER.fullmatch(providers[0]):
        raise InputError("Promptfoo provider is outside the supported built-in provider subset")
    if not isinstance(tests, list) or not 1 <= len(tests) <= MAX_CASES:
        raise InputError("Promptfoo tests must contain 1 to 100 cases")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(tests):
        test = _mapping(item, f"Promptfoo test {index}")
        _keys(test, {"vars", "assert"}, f"Promptfoo test {index}", {"vars"})
        variables = _mapping(test["vars"], f"Promptfoo test {index}.vars")
        _validate_promptfoo_vars(variables)
        assertions = test.get("assert", [])
        if not isinstance(assertions, list) or len(assertions) > 20:
            raise InputError("Promptfoo assertions must be a bounded list")
        validated_assertions = []
        for assertion in assertions:
            item_doc = _mapping(assertion, "Promptfoo assertion")
            _keys(item_doc, {"type", "value"}, "Promptfoo assertion", {"type", "value"})
            kind = item_doc["type"]
            if kind not in PROMPTFOO_ASSERTIONS:
                raise InputError("unsupported or executable Promptfoo assertion")
            if kind == "is-json":
                if item_doc["value"] not in (True, None):
                    raise InputError("is-json assertion does not accept a value")
                validated_assertions.append({"type": kind})
            else:
                validated_assertions.append({"type": kind, "value": _text(item_doc["value"], "assertion value", nonempty=False)})
        normalized.append({"vars": variables, "assertions": validated_assertions})
    prompt = _text(prompts[0], "Promptfoo prompt")
    return prompt, providers[0], normalized


def _result_lines(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try:
        raw = read_bounded(path, "Promptfoo result file")
    except OSError as exc:
        raise InputError("cannot read Promptfoo result file") from exc
    if len(raw) > MAX_BYTES:
        raise InputError("Promptfoo result file exceeds byte limit")
    try:
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("invalid Promptfoo JSONL result file") from exc
    if not 1 <= len(rows) <= MAX_CASES:
        raise InputError("Promptfoo result count must be 1 to 100")
    _validate_tree(rows)
    _validate_sensitive(rows)
    return [_mapping(row, "Promptfoo result row") for row in rows], raw


def _validate_promptfoo_vars(variables: dict[str, Any]) -> None:
    for key, value in variables.items():
        _text(key, "Promptfoo variable name")
        if not isinstance(value, (str, int, float, bool)):
            raise InputError("Promptfoo variables must be scalar")


def _assertion_result(assertion: dict[str, Any], output: str) -> dict[str, Any]:
    kind, expected = assertion["type"], assertion.get("value")
    if kind == "equals":
        passed = output == expected
    elif kind == "contains":
        passed = expected in output
    elif kind == "not-contains":
        passed = expected not in output
    else:
        try:
            json.loads(output)
            passed = True
        except json.JSONDecodeError:
            passed = False
    return {"type": kind, "status": "PASS" if passed else "FAIL"}


def import_promptfoo(config_path: Path, results_path: Path) -> dict[str, Any]:
    config_raw = read_bounded(config_path, "Promptfoo config")
    config = parse_yaml_bytes(config_raw, label="Promptfoo config")
    prompt, provider, tests = _parse_promptfoo_config(config)
    rows, results_raw = _result_lines(results_path)
    if len(rows) != len(tests):
        raise InputError("Promptfoo result count does not match configured tests")
    observations = []
    all_assertions = []
    for index, (test, row) in enumerate(zip(tests, rows, strict=True)):
        _keys(row, PROMPTFOO_RESULT_KEYS, f"Promptfoo result row {index}", {"response"})
        if "success" in row and not isinstance(row["success"], bool):
            raise InputError(f"Promptfoo success flag is invalid for test {index}")
        if "score" in row and (not isinstance(row["score"], (int, float)) or not math.isfinite(row["score"])):
            raise InputError(f"Promptfoo score is invalid for test {index}")
        row_vars = _mapping(row.get("vars", test["vars"]), f"Promptfoo result vars {index}")
        _validate_promptfoo_vars(row_vars)
        if row_vars != test["vars"]:
            raise InputError(f"Promptfoo result vars do not match test {index}")
        response = row["response"]
        if isinstance(response, str):
            output = response
        else:
            response_doc = _mapping(response, "Promptfoo response")
            _keys(response_doc, {"output"}, "Promptfoo response", {"output"})
            output = _text(response_doc["output"], "Promptfoo response.output", nonempty=False)
        checks = [_assertion_result(assertion, output) for assertion in test["assertions"]]
        all_assertions.extend(checks)
        observations.append({"test_index": index, "vars": test["vars"], "prompt": prompt, "response": output, "assertions": checks})
    # External-runner status and scores are intentionally not promoted to hard-gate evidence.
    evidence = {
        "schema": "aips.external-eval-evidence.v1",
        "id": "promptfoo-" + hashlib.sha256(results_raw).hexdigest()[:16],
        "source": {"tool": "promptfoo", "config_sha256": digest_bytes(config_raw), "results_sha256": digest_bytes(results_raw), "provider": provider},
        "evidence_class": "external_observation",
        "status": "REVIEW" if any(check["status"] == "FAIL" for check in all_assertions) else "SIGNAL",
        "gate_eligibility": "CANONICAL_REGRESSION_REQUIRED",
        "assertions": all_assertions,
        "observations": observations,
    }
    evidence["fingerprint"] = fingerprint_evidence(evidence)
    return evidence


def export_promptfoo(case_doc: Any, provider: str) -> dict[str, Any]:
    case = validate_case(case_doc)
    if not PROMPTFOO_PROVIDER.fullmatch(provider):
        raise InputError("export requires an explicit supported built-in provider")
    description = f"AIPS Agent Eval case {case['id']} ({digest_value(case_doc)})"
    return {
        "description": description,
        "prompts": [case["prompt"]],
        "providers": [provider],
        "tests": [{"vars": case["vars"]}],
    }


def import_pyrit_bridge(path: Path) -> dict[str, Any]:
    raw = read_bounded(path, "PyRIT bridge")
    bridge = parse_yaml_bytes(raw, label="PyRIT bridge")
    doc = _mapping(bridge, "PyRIT bridge")
    _keys(doc, {"version", "producer", "run", "findings"}, "PyRIT bridge", {"version", "producer", "findings"})
    if doc["version"] != 1:
        raise InputError("unsupported PyRIT bridge version")
    producer = _mapping(doc["producer"], "bridge.producer")
    _keys(producer, {"name", "version"}, "bridge.producer", {"name", "version"})
    if producer["name"] != "pyrit":
        raise InputError("bridge producer must be pyrit")
    findings = doc["findings"]
    if not isinstance(findings, list) or len(findings) > MAX_CASES:
        raise InputError("bridge findings must be a bounded list")
    observations = []
    for index, finding in enumerate(findings):
        item = _mapping(finding, f"bridge finding {index}")
        _keys(item, {"id", "category", "prompt", "response", "scorer"}, "bridge finding", {"id", "prompt", "response"})
        scorer = _mapping(item.get("scorer", {}), "bridge scorer")
        _keys(scorer, {"name", "outcome"}, "bridge scorer")
        outcome = scorer.get("outcome", "unknown")
        if outcome not in {"success", "failure", "unknown"}:
            raise InputError("invalid bridge scorer outcome")
        observations.append({"id": _text(item["id"], "finding.id"), "category": str(item.get("category") or "unspecified"), "prompt": _text(item["prompt"], "finding.prompt"), "response": _text(item["response"], "finding.response", nonempty=False), "scorer": {"name": str(scorer.get("name") or "unspecified"), "outcome": outcome}, "status": "REVIEW"})
    evidence = {"schema": "aips.external-eval-evidence.v1", "id": "pyrit-" + hashlib.sha256(raw).hexdigest()[:16], "source": {"tool": "pyrit", "version": str(producer["version"]), "bridge_sha256": digest_bytes(raw)}, "evidence_class": "discovery", "status": "REVIEW", "gate_eligibility": "ADVISORY_ONLY", "observations": observations}
    evidence["fingerprint"] = fingerprint_evidence(evidence)
    return evidence


def verify_evidence(path: Path, config_path: Path | None = None, results_path: Path | None = None, bridge_path: Path | None = None) -> dict[str, Any]:
    evidence = _mapping(load_yaml(path), "external Eval evidence")
    if evidence.get("schema") != "aips.external-eval-evidence.v1":
        raise InputError("unsupported external evidence schema")
    if evidence.get("fingerprint") != fingerprint_evidence(evidence):
        raise InputError("external evidence fingerprint is stale or invalid")
    source = _mapping(evidence.get("source"), "external evidence source")
    checked: list[str] = []
    if config_path is not None:
        expected = source.get("config_sha256")
        if not expected or digest_bytes(read_bounded(config_path, "Promptfoo config")) != expected:
            raise InputError("Promptfoo config digest does not match evidence")
        checked.append("config")
    if results_path is not None:
        expected = source.get("results_sha256")
        if not expected or digest_bytes(read_bounded(results_path, "Promptfoo results")) != expected:
            raise InputError("Promptfoo results digest does not match evidence")
        checked.append("results")
    if bridge_path is not None:
        expected = source.get("bridge_sha256")
        if not expected or digest_bytes(read_bounded(bridge_path, "PyRIT bridge")) != expected:
            raise InputError("PyRIT bridge digest does not match evidence")
        checked.append("bridge")
    if source.get("tool") == "promptfoo" and (config_path is None) != (results_path is None):
        raise InputError("verify Promptfoo evidence with both --config and --results")
    return {"status": "VERIFIED", "evidence_fingerprint": evidence["fingerprint"], "checked_sources": checked, "gate_eligibility": evidence.get("gate_eligibility")}


def choose_profile(change_class: str, areas: list[str], deep_pyrit: bool) -> dict[str, Any]:
    config = _mapping(load_yaml(ROOT / "config" / "eval-profiles.yaml"), "Eval profile config")
    profiles = _mapping(config.get("profiles"), "Eval profiles")
    known = set(profiles)
    if change_class not in known:
        raise InputError("unsupported change class")
    if any(area not in known for area in areas):
        raise InputError("unsupported evaluation area")
    selected = set(areas) | {change_class}
    profile_order = list(profiles)
    profile = max(selected, key=profile_order.index)
    profile_doc = _mapping(profiles[profile], f"Eval profile {profile}")
    requirements = profile_doc.get("required")
    if not isinstance(requirements, list) or not requirements or not all(isinstance(item, str) for item in requirements):
        raise InputError("selected Eval profile has no valid requirements")
    result = {"schema": "aips.eval-profile-selection.v1", "profile": profile, "requirements": requirements, "external_scans": "OPTIONAL_ADVISORY", "hard_gate_source": "VERIFIED_CANONICAL_DETERMINISTIC_REGRESSION_ONLY", "human_authority_preserved": True}
    if deep_pyrit:
        pyrit_config = _mapping(_mapping(config.get("deep_scan"), "deep_scan").get("pyrit"), "deep_scan.pyrit")
        if pyrit_config.get("enabled_by_default") is not False or pyrit_config.get("authority") != "advisory_only":
            raise InputError("PyRIT deep scan policy must remain optional and advisory")
        result["optional_deep_scan"] = {"producer": "pyrit", "authority": "ADVISORY_ONLY", "requires_external_runtime": pyrit_config.get("requires_external_runtime") is True}
    return result


def promote_finding(finding_doc: Any) -> dict[str, Any]:
    finding = _mapping(finding_doc, "red-team finding")
    _keys(finding, {"version", "id", "state", "title", "category", "minimal_reproduction", "review"}, "red-team finding", {"version", "id", "state", "title", "minimal_reproduction", "review"})
    if finding["version"] != 1 or finding["state"] != "CONFIRMED":
        raise InputError("only version 1 CONFIRMED findings may be promoted")
    review = _mapping(finding["review"], "finding.review")
    _keys(review, {"status", "reviewer", "approval_reference", "reviewed_at"}, "finding.review", {"status", "reviewer", "approval_reference", "reviewed_at"})
    if review["status"] != "APPROVED" or review["reviewer"] != "human":
        raise InputError("Human review is required to promote a finding")
    for field in ("approval_reference", "reviewed_at"):
        _text(review[field], f"finding.review.{field}")
    reproduction = _mapping(finding["minimal_reproduction"], "finding.minimal_reproduction")
    _keys(reproduction, {"scenario_id", "prompt", "vars", "rubric"}, "minimal reproduction", {"scenario_id", "prompt", "rubric"})
    case = {"version": 1, "id": "regression-" + re.sub(r"[^a-zA-Z0-9-]", "-", _text(finding["id"], "finding.id"))[:60], "scenario_id": str(reproduction["scenario_id"]), "description": _text(finding["title"], "finding.title"), "input": {"prompt": reproduction["prompt"], "vars": reproduction.get("vars", {})}, "rubric": reproduction["rubric"], "provenance": {"finding_id": finding["id"], "approval_reference": review["approval_reference"]}}
    validate_case(case)
    return case


def write_yaml(path: Path, data: Any) -> None:
    _validate_sensitive(data)
    rendered = yaml.dump(data, Dumper=NoAliasSafeDumper, sort_keys=False, allow_unicode=True)
    if len(rendered.encode("utf-8")) > MAX_BYTES:
        raise InputError("output exceeds byte limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(rendered, encoding="utf-8")
    temp.replace(path)


def emit(data: Any, fmt: str) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2) if fmt == "json" else yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS offline-first external Eval interoperability")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-promptfoo")
    imp.add_argument("--config", required=True)
    imp.add_argument("--results", required=True)
    imp.add_argument("--output", required=True)
    exp = sub.add_parser("export-promptfoo")
    exp.add_argument("--case", required=True)
    exp.add_argument("--provider", required=True)
    exp.add_argument("--output", required=True)
    pyrit = sub.add_parser("import-pyrit")
    pyrit.add_argument("--bridge", required=True)
    pyrit.add_argument("--output", required=True)
    profile = sub.add_parser("profile")
    profile.add_argument("--change-class", required=True)
    profile.add_argument("--area", action="append", default=[])
    profile.add_argument("--deep-pyrit", action="store_true")
    profile.add_argument("--format", choices=["yaml", "json"], default="yaml")
    promote = sub.add_parser("promote-finding")
    promote.add_argument("--finding", required=True)
    promote.add_argument("--output", required=True)
    verify = sub.add_parser("verify-evidence")
    verify.add_argument("--evidence", required=True)
    verify.add_argument("--config")
    verify.add_argument("--results")
    verify.add_argument("--bridge")
    verify.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = parser.parse_args()
    try:
        if args.command == "verify-evidence":
            emit(verify_evidence(Path(args.evidence), Path(args.config) if args.config else None, Path(args.results) if args.results else None, Path(args.bridge) if args.bridge else None), args.format)
        elif args.command == "import-promptfoo":
            result = import_promptfoo(Path(args.config), Path(args.results))
            write_yaml(Path(args.output), result)
            emit({"status": result["status"], "gate_eligibility": result["gate_eligibility"], "output": Path(args.output).name}, "yaml")
        elif args.command == "export-promptfoo":
            result = export_promptfoo(load_yaml(Path(args.case)), args.provider)
            write_yaml(Path(args.output), result)
            emit({"status": "EXPORTED", "output": Path(args.output).name}, "yaml")
        elif args.command == "import-pyrit":
            result = import_pyrit_bridge(Path(args.bridge))
            write_yaml(Path(args.output), result)
            emit({"status": result["status"], "gate_eligibility": result["gate_eligibility"], "output": Path(args.output).name}, "yaml")
        elif args.command == "profile":
            emit(choose_profile(args.change_class, args.area, args.deep_pyrit), args.format)
        else:
            result = promote_finding(load_yaml(Path(args.finding)))
            write_yaml(Path(args.output), result)
            emit({"status": "PROMOTED", "case_id": result["id"], "output": Path(args.output).name}, "yaml")
        return 0
    except (OSError, InputError, yaml.YAMLError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
