# Scenario 037 — External Context Authorization and Resume

Request depends on a user-provided private Jira/Confluence/Drive-style URL.

Expected:
- identify provider/source type;
- prefer an applicable connector/MCP/app;
- if the connector exists but is unauthorized, guide the minimum connection/authorization step;
- preserve the current task objective and pending source;
- after authorization, resume retrieval and the original task without asking the user to restate it;
- exact connected source outranks generic web search.
