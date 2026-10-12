---
id: technical-teaching
description: Teach a technical concept through a goal, short explanation, practice, feedback and a learner-chosen next step.
capability: product
estimated_context_cost: medium
triggers:
- explicit_technical_teaching_request
- guided_learning_session
- concept_practice_request
- exercise_scaffold_setup
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Technical Teaching

Use this Skill when the user asks to learn a concept or practice a technical task.

1. Set one learning goal and match the explanation to the learner's stated experience.
2. Explain a small concept with one concrete example; distinguish simplification from exact behavior.
3. Offer a short exercise that checks understanding without exposing secrets or changing the user's project.
4. Give feedback on the learner's attempt, correct misconceptions with evidence and invite a choice of next step.
5. Keep the session state only in the current conversation unless the user requests a saved learning record.

When the user explicitly asks to scaffold course exercises, use the project's existing directory and lint conventions for problem, solution and explanation files. This is an artifact-creation task; do not turn it into an unsolicited teaching session or impose a course structure the project does not use.

Do not turn ordinary implementation help into a lesson. The user controls the pace and can stop or change direction at any time.

Source note: adapted from mattpocock/skills productivity/teach at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
