---
id: human-guided-wizard
description: Guide human-only setup or cutover steps without handling credentials.
capability: engineering
estimated_context_cost: low
triggers:
- explicit_human_setup_wizard
- manual_cutover_instruction_wizard
model_requirements:
  reasoning: high
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Human-Guided Wizard

## Admission
Distinct from AIPS installation and deployment automation: only human-exclusive steps need an interactive guide. Adapted from Matt Pocock's `wizard`.

## Method
1. Identify exact human-only actions, prerequisites, rollback points and required approvals.
2. Map each stage's description, observable completion condition, recovery path and safe skip behavior.
3. When asked for an executable wizard, use an auditable local script with dry-run defaults, no hidden network calls and clearly labeled manual actions.
4. Never ask the user to paste passwords, private keys, secret values or personal access tokens. Use external dashboards' own secret-entry controls instead.
5. Verify command quoting, platform assumptions and failure handling using fixtures or a sandbox before proposing real use.

## Non-triggers
Tasks an agent may safely perform, general documentation-only queries, unattended production changes, authorization bypasses or publication. Human-guided does not mean human-approved.
