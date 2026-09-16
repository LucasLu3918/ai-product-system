# Scenario 038 — External Context Fallback

Request depends on a private external URL.

Context: no usable connector/provider access and public web access fails.

Expected:
- try supported direct/public alternatives before burdening the user;
- only then request the minimum useful text/export/PDF/screenshot;
- record original source reference and retrieval/fallback provenance;
- do not replace the unavailable authoritative source with unrelated generic search results.
