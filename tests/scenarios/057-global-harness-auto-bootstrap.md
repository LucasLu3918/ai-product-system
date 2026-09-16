# Scenario 057 — Global Harness Automatic Bootstrap

A supported runtime is installed and its AIPS integration location is unused.

Expected:
- aips install / harness install creates only an AIPS-owned minimal bootstrap integration;
- runtime status becomes AUTOMATIC;
- session bootstrap points to AIPS Harness Resolution;
- the entire AIPS repository is not preloaded.
