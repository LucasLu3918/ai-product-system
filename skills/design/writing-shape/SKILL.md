---
id: writing-shape
description: Turn a fixed set of writing material into a coherent article by agreeing on its reader journey and shaping one section at a time.
capability: design
estimated_context_cost: medium
triggers:
- explicit_writing_shape_request
- explicit_writing_workflow_request
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Writing Shape

Use only when the user explicitly asks to shape supplied material into an article.

Read the input pile end-to-end. Keep it read-only and create a separate article. Agree on the article's goal, reader prerequisites and a candidate opening before building the rest. Each paragraph or section should advance the promised reader journey and rely only on grounded concepts. Use the user's material; name a missing example or fact instead of inventing one.

Draft one agreed section at a time and reread the current article before each edit so user revisions remain intact. The user decides when the piece is complete. This is the optional final step in the Fragments → Beats → Shape workflow.

Source note: adapted from mattpocock/skills in-progress/writing-shape at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
