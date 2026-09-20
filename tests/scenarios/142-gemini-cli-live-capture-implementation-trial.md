# Scenario 142 — Gemini CLI AfterTool Live-Capture Implementation Trial

AIPS has adopted the observable-event live-capture design direction and the Human authorizes the first runtime-specific bounded implementation Trial.

Expected:
- choose exactly one concrete runtime: Gemini CLI;
- rely on Gemini CLI's native `AfterTool` hook contract rather than creating a parallel runtime framework;
- wire an AfterTool hook only for the bounded v1 file-tool scope: `read_file|write_file|replace`;
- keep capture disabled by default and require explicit opt-in plus an explicit sink path under the system temporary directory;
- always allow the original tool result to continue; capture evidence cannot deny, rewrite or remediate execution;
- truthfully distinguish flow-control authority from latency: Gemini CLI waits synchronously for AfterTool hooks, so this Trial records synchronous_hook=true / latency_path=synchronous even though critical_path=false means only "not an authorization/result-enforcement gate";
- keep the disabled path lightweight: the shell wrapper returns allow directly without starting Python unless capture is explicitly enabled;
- project only canonical metadata and never persist `tool_input`, `tool_response`, prompt/response text, private reasoning or secret-like raw values;
- supported-tool fixture capture is 6/6 with unexpected event loss=0;
- malformed/unsupported fixture cases degrade or skip safely and do not create false capture claims;
- bounded subprocess overhead is asserted in CI without committing a misleading exact performance number;
- canonical captured events remain monotonic with the existing Resource Authorization profile and reuse the existing anomaly evaluator;
- `live_runtime_execution_verified=false` and `live_capture_verified=false` remain truthful because CI validates the official hook contract but does not execute a real Gemini CLI binary;
- production persistence, shell/MCP/network tools, semantic intent governance and automatic remediation remain out of scope.
