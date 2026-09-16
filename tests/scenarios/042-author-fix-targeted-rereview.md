# Scenario 042 — Original Author Fix and Targeted Re-review

Context: consolidated findings are returned after multi-perspective review.

Expected:
- original implementation Author remains the writer;
- reviewer does not silently rewrite the code;
- Author fixes accepted findings and runs affected tests;
- re-review uses original finding + fix diff + relevant tests by default;
- full broad review repeats only when the fix materially expands the Change Boundary.
