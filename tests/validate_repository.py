from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f"YAML parse failed: {path.relative_to(ROOT)}: {exc}")
        return None

for rel in [
    'roles/INDEX.yaml',
    'skills/INDEX.yaml',
    'capabilities/INDEX.yaml',
    'orchestration/schemas/context-manifest.yaml',
    'orchestration/schemas/workspace-state.yaml',
    'orchestration/schemas/execution-profile.yaml',
    'templates/artifact-contract.yaml',
    'templates/change-boundary.yaml',
    'templates/project/architecture-profile.yaml',
    'templates/workspace/MANIFEST.yaml',
    'templates/workspace/STATE.yaml',
]:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"Missing required YAML: {rel}")
    else:
        load_yaml(p)

roles = load_yaml(ROOT / 'roles/INDEX.yaml') or {}
for role_id, meta in (roles.get('roles') or {}).items():
    path = ROOT / 'roles' / meta['path']
    if not path.exists():
        errors.append(f"Role path missing for {role_id}: roles/{meta['path']}")

skills = load_yaml(ROOT / 'skills/INDEX.yaml') or {}
for skill_id, meta in (skills.get('skills') or {}).items():
    path = ROOT / 'skills' / meta['path']
    if not path.exists():
        errors.append(f"Skill path missing for {skill_id}: skills/{meta['path']}")
    mr = meta.get('model_requirements') or {}
    for key in ('reasoning', 'coding', 'reliability', 'minimum_tier', 'preferred_tier'):
        if key not in mr:
            errors.append(f"Skill {skill_id} missing model_requirements.{key}")
    if isinstance(mr.get('minimum_tier'), int) and isinstance(mr.get('preferred_tier'), int):
        if mr['minimum_tier'] > mr['preferred_tier']:
            errors.append(f"Skill {skill_id}: minimum_tier exceeds preferred_tier")

required_docs = [
    'AGENTS.md', 'SYSTEM.md', 'README.md', 'USER_GUIDE.md', 'VERSION',
    'core/PRINCIPLES.md', 'core/GOVERNANCE.md', 'core/DECISIONS.md',
    'orchestration/ORCHESTRATOR.md', 'orchestration/MODEL_ROUTING.md',
    'orchestration/INSTRUCTION_RESOLUTION.md', 'orchestration/WORKSPACE_STATE.md',
    'examples/EXAMPLES.md', 'work-modes/README.md',
]
for rel in required_docs:
    if not (ROOT / rel).exists():
        errors.append(f"Missing required document: {rel}")

scenarios = sorted((ROOT / 'tests/scenarios').glob('*.md'))
if len(scenarios) < 10:
    errors.append(f"Expected at least 10 acceptance scenarios, found {len(scenarios)}")

if errors:
    print('VALIDATION FAILED')
    for e in errors:
        print(f'- {e}')
    sys.exit(1)

print('VALIDATION PASSED')
print(f"roles={len((roles.get('roles') or {}))}")
print(f"skills={len((skills.get('skills') or {}))}")
print(f"scenarios={len(scenarios)}")
