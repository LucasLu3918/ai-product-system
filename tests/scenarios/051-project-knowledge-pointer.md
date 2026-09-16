# Scenario 051 — Existing Authoritative Source Becomes Intelligence Pointer

AGENTS.md or accepted ADR already states the project's DDD/Clean Architecture rules.

Expected:
- do not duplicate the authoritative rules into Project Intelligence topic content;
- register the source in `SOURCE_REGISTRY.yaml` with its authority/scope/runtime visibility when useful;
- Project Intelligence references the authoritative source rather than replacing it;
- applicable authoritative/runtime/project instructions have higher precedence than derived Project Intelligence.
