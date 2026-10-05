# Scenario 211: GitHub-native supply-chain security

Given a pull request changes a dependency manifest or lockfile, when GitHub validates the pull request, then the least-privilege Dependency Review workflow blocks newly introduced high or critical vulnerabilities; scheduled OpenSSF Scorecard publishes advisory SARIF without granting PR, merge, release, or code-change authority. Actions are pinned to immutable commit SHAs, and CodeQL default setup remains independently controlled by the repository security setting.

Evidence: `tests/validation/security_workflow_contracts.py`, `.github/workflows/dependency-review.yml`, and `.github/workflows/scorecard.yml`.
