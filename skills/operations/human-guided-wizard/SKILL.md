---
id: human-guided-wizard
description: Prepare a clear step-by-step guide for operational actions that only a human can complete in an external service or dashboard.
capability: operations
estimated_context_cost: low
triggers:
- human_only_dashboard_step
- user_requested_manual_setup_guide
- human_approval_sequence
model_requirements:
  reasoning: high
  coding: none
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Human-Guided Operations

Use this Skill when the next action must be performed by a person, such as an external dashboard approval or a manual account configuration.

1. Separate human-only steps from actions the Agent can safely perform in the authorized workspace.
2. Give the person one step at a time, with the expected screen or result and a safe recovery path.
3. Explain what each permission or setting changes before asking the person to apply it.
4. Keep credentials in the service's native secure input or an approved secret manager. Never ask the user to paste, save, echo or screenshot a secret.
5. Stop at the human decision. Do not claim the action succeeded until the user or a read-only source confirms it.

Do not generate a shell wizard that requests secrets or performs privileged actions. The guide does not grant authority to change infrastructure, accounts or production.

Source note: adapted from mattpocock/skills engineering/wizard at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
