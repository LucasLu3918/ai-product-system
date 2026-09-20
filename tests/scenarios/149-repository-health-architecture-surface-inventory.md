# Scenario 149 — Repository Health Architecture Surface Inventory

## Given

AIPS has a Capability Map, the explicit `config/architecture-surfaces.yaml` major-subsystem inventory, Scenario Conformance evidence, the repository validator and Repository Health.

## When

Repository Health audits the repository.

## Then

- every Capability Map ID is classified into exactly one architecture surface;
- each surface's required repository paths exist;
- each canonical document exists and is declared by one of the surface's covered Capability Map entries;
- each validation path is deterministically bound either through Scenario Conformance evidence or the top-level repository validator;
- a newly added unclassified capability, missing surface path or unbound validation path produces `architecture_surface_drift`;
- bounded guard/gate discovery remains active as a secondary orphan detector;
- the exact-candidate validate workflow emits and uploads `repository-health-report.json`;
- no external Agent/provider credential or provider network call is required;
- detection and artifact publication grant no remediation, code-change, PR, merge, release or publication authority.
