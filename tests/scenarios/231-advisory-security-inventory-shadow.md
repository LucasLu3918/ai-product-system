# Scenario 231: Advisory Security Inventory and Secret-Scanner Shadow

## Given

- The public repository already has a required candidate-bound secret scan, required repository Gate, and CodeQL default setup.
- Cross-ecosystem inventory and scanner-parity observations are useful as supplementary maintenance evidence.

## When

- The weekly advisory security workflow runs, or a maintainer dispatches it manually.

## Then

- OSV Scanner inventories repository dependencies using a pinned reusable workflow and narrowly scoped SARIF upload permission.
- Gitleaks scans full Git history alongside the existing project scanner; both outcomes are reported for review.
- Scanner findings, mismatches, and operational failures remain advisory and cannot replace or weaken the required candidate secret scan or repository Gate.
- The workflow does not run on pull requests, comment on pull requests, upload a Gitleaks report artifact, merge, or publish.
- CodeQL remains verified through the repository's configured GitHub default setup, not a duplicate local workflow declaration.

## Evidence

- `tests/validation/security_workflow_contracts.py`
- `.github/workflows/security-inventory.yml`
- `.github/workflows/dependency-review.yml`
- `.github/workflows/scorecard.yml`
- `config/documentation-placement.yaml`
