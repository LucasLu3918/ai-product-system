# System Improvement Review — READY Stale Project Intelligence Advisory

- **Appropriateness:** Suitable. Freshness is derived evidence about source drift; when semantic readiness is already READY, staleness alone need not block an ordinary confined local source edit.
- **User problem:** A stale derived cache can block software changes even when its limits are understood and the authoritative project instructions remain available.
- **Proposed solution:** Keep freshness and targeted refresh metadata visible, but remove READY+STALE as a standalone fail-closed condition for local L2 source writes. Preserve the native path guard and every other approved blocker.
- **Reuse / lower-layer alternative:** Reuse Turn Context `fail_policy` and the existing OpenCode permission guard. Do not add a new mode, data store, runtime component, or approval mechanism.
- **Security / reliability:** UNKNOWN freshness, non-READY Intelligence, missing canonical protocols, authority conflicts, escaping paths, creative writes, external/high-risk actions and other closed-policy reasons remain denied. Legacy cached manifests may have the single `intelligence_stale` reason; the guard ignores it only when readiness is READY and freshness is STALE.
- **Compatibility:** Keep the manifest shape and freshness reporting; existing targeted refresh guidance remains intact.
- **Constitution impact:** NO. No authority, safety, Human approval, privacy, or publication rule changes.
- **Recommendation:** Make stale READY intelligence advisory only for the approved local L2 case and bind it to lifecycle evidence.
- **Additional optimization candidates:** None included.
