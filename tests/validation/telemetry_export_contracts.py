import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []
schema = yaml.safe_load((ROOT / "orchestration/schemas/telemetry-export.yaml").read_text(encoding="utf-8"))
config = yaml.safe_load((ROOT / "config/telemetry-export.yaml").read_text(encoding="utf-8"))
coverage = yaml.safe_load((ROOT / "tests/scenario_coverage.yaml").read_text(encoding="utf-8"))
record = (ROOT / "scripts/telemetry_record.py").read_text(encoding="utf-8")
projection = (ROOT / "scripts/telemetry_projection.py").read_text(encoding="utf-8")
exporter = (ROOT / "scripts/telemetry_export.py").read_text(encoding="utf-8")
cli = (ROOT / "bin/aips").read_text(encoding="utf-8")
scenario = ROOT / "tests/scenarios/181-opentelemetry-telemetry-export.md"

if config.get("enabled") is not False:
    errors.append("telemetry export must default to disabled")
if schema.get("export", {}).get("default_enabled") is not False:
    errors.append("telemetry schema must keep export disabled by default")
if schema.get("mapping", {}).get("genai_revision") != "0c87594975195608dc91b3f702e250a7b240c151":
    errors.append("GenAI mapping must remain bound to the reviewed immutable upstream snapshot")
if schema.get("privacy", {}).get("unknown_attributes") != "reject":
    errors.append("unknown telemetry attributes must reject")
if schema.get("privacy", {}).get("raw_runtime_payload_persisted") is not False:
    errors.append("raw runtime payload must not be persisted")
if not scenario.is_file():
    errors.append("Scenario 181 is missing")
elif "TELEMETRY_DEGRADED" not in scenario.read_text(encoding="utf-8"):
    errors.append("Scenario 181 must cover telemetry failure truth")
entries = coverage.get("scenarios", [])
match = [item for item in entries if str(item.get("id")) == "181"]
if len(match) != 1 or match[0].get("coverage") != "lifecycle":
    errors.append("Scenario 181 must be registered exactly once as lifecycle coverage")
elif "tests/evidence/telemetry_export_lifecycle.py" not in match[0].get("evidence", []):
    errors.append("Scenario 181 must bind its lifecycle evidence")
if "aips.telemetry.record" in projection or "gen_ai.input.messages" in projection or "gen_ai.output.messages" in projection:
    errors.append("projection must not capture content or confuse telemetry attributes with durable source events")
if "NoRedirect" not in exporter or "HTTPRedirectHandler" not in exporter:
    errors.append("exporter must not forward credentials or run telemetry through redirects")
if "HTTPS_or_loopback_only" not in schema.get("export", {}).get("endpoint_policy", ""):
    errors.append("schema must constrain remote telemetry endpoints")
if "scripts/telemetry_record.py" not in cli or "telemetry_cmd" not in cli:
    errors.append("aips CLI must route telemetry commands")
if 'help|-h|--help)' not in cli or "Usage: aips telemetry" not in cli:
    errors.append("aips telemetry must expose command help")
if "prompt" not in schema.get("privacy", {}).get("forbidden", []):
    errors.append("telemetry schema must explicitly forbid prompt capture")
current_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if not re.search(rf"^## {re.escape(current_version)}$", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE):
    errors.append("CHANGELOG must contain a heading for the current VERSION")
if not (ROOT / "docs/human/assets/system-overview.svg").read_text(encoding="utf-8").endswith("</svg>\n"):
    errors.append("System overview SVG must remain closed and newline-terminated")
