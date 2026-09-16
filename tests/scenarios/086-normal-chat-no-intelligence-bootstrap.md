# Scenario 086 — Normal Chat Does Not Bootstrap Project

A general knowledge prompt occurs while the current directory is a repository with no Project Intelligence.

Expected:
- compact Harness / Turn Context may still resolve;
- the prompt is treated as non-mutating;
- no Change Impact is required;
- missing Intelligence is reported truthfully;
- no project `.ai/` workspace is created;
- no External Project Intelligence store is created merely for normal chat.
