# Runtime Adapter Contract

Every AIPS Runtime Adapter describes the smallest safe mechanism needed to place the Minimal Bootstrap into an Agent runtime.

## Required fields

~~~yaml
id:
runtime:
detection:
integration:
  strategy:
  automatic:
ownership:
  resources: []
bootstrap:
  source:
verification:
uninstall:
  reversible:
  preserves_user_content:
limitations: []
~~~

## Adapter responsibilities

An Adapter may:

- detect the runtime;
- install/register an AIPS-owned bootstrap integration;
- report runtime-native instruction locations;
- verify its own installation;
- unregister/remove only AIPS-owned resources.

An Adapter must not:

- implement AIPS planning/security/quality logic;
- copy the whole AIPS system into runtime context;
- overwrite existing user instruction/config/skills;
- claim AUTOMATIC if a manual user edit is required;
- delete a file that differs from the AIPS-owned installed copy.

## Runtime-native precedence

Adapters record relevant native precedence/limitations. AIPS does not falsely claim that every runtime can enforce identical instruction precedence.

If native precedence can override the Global Bootstrap, the Adapter documents that limitation and the Orchestrator surfaces conflicts when discovered.
