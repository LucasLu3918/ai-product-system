# Scenario 161 — Parallel Runtime Port Isolation

Two or more approved Agent tasks execute concurrently in separate AIPS-managed Git worktrees and need local TCP development/test servers.

Expected:
- each runtime port request is bound to an ACTIVE AIPS isolation and a stable resource id;
- concurrent AIPS allocators use atomic repository-scoped coordination and cannot commit the same TCP port lease;
- an occupied preferred/host port is skipped and allocation follows a deterministic bounded candidate order;
- the runtime manifest exposes canonical `AIPS_PORT_<RESOURCE>` values, `AIPS_PORT` when unambiguous, and only explicitly requested aliases such as `PORT`;
- Scheduler output validates and propagates Task Graph runtime requests but does not allocate OS resources;
- an existing lease is stable across repeated reads/lease requests;
- bounded reallocation excludes the previous failed port for address-in-use recovery;
- runtime release works independently from dirty worktree cleanup;
- clean isolation removal releases its remaining leases;
- orphaned leases whose AIPS isolation is no longer ACTIVE can be reconciled without treating an ACTIVE-but-idle lease as stale;
- v0.51 supports TCP ports only and does not grant broader Change Boundary, network, publication, merge, release or Human authority.
