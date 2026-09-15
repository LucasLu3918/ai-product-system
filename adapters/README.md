# Adapters

The core is platform-agnostic. An adapter only teaches a host/agent how to enter the system and map generic model/tool requirements to capabilities available on that platform.

Minimum adapter contract:

1. expose/read `AGENTS.md` and `SYSTEM.md`;
2. support progressive file loading rather than preloading the repository;
3. map generic model requirements from `orchestration/MODEL_ROUTING.md`;
4. respect project-local `AGENTS.md` scope and system governance;
5. write project outputs/state into the target workspace, not into the system repository.

Do not duplicate roles, skills or governance inside adapters.
