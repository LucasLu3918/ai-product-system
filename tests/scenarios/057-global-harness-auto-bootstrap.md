# Scenario 057 — Global Harness Automatic Bootstrap

A supported runtime is installed and its AIPS integration surface can be safely composed.

Expected:
- `aips install` / `aips harness install` creates only AIPS-owned minimal runtime integration;
- existing user-owned content is preserved through managed composition where supported;
- runtime installation status and capability are recorded truthfully;
- current Turn Context resolves through AIPS Harness Resolution rather than preloading the entire AIPS repository;
- unsafe/colliding integrations become MANUAL/CONFLICT instead of overwriting user state.
