# Order, payment, and refund prompts

Model order, payment attempt, capture, fulfillment, cancellation, return, and refund as separate concepts or state machines where the domain evidence supports that choice. Define allowed transitions, actor, trigger, side effects, retries, and audit evidence.

Clarify the external payment provider boundary, authorization versus capture, asynchronous notifications, duplicate delivery, reconciliation, partial payment/refund, and failure recovery when applicable. Never store or request raw payment credentials in planning artifacts. Do not assert compliance scope without evidence; route security and payment review for human assessment.
