# Scenario 080 — Legacy Intelligence Copies to External State

Expected:
- attach/bootstrap validates legacy `.ai/intelligence/` before copying to the external user-state store;
- the legacy source remains byte-identical after migration;
- existing external canonical state is not silently overwritten by an older local copy;
- detach does not archive or delete project files;
- all new Intelligence writes target external state.
