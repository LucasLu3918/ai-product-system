# Scenario 210: Python runtime support policy

Given an AIPS installation or managed virtual environment using Python below 3.12, when the user runs `aips doctor` or an install/update repair, then the CLI reports the required Python >=3.12 version, refuses an explicitly selected older interpreter before creating a partial environment, and rebuilds an owned older venv only when a compatible interpreter is available. The published support facts and scheduled compatibility smoke matrix agree on Python 3.12, 3.13, and 3.14.

Evidence: `tests/evidence/install_preflight_lifecycle.py`, `tests/evidence/system_facts_lifecycle.py`, `tests/validation/system_facts_contracts.py`, and `.github/workflows/python-compatibility.yml`.
