# E-commerce planning reference

Use this pack when the confirmed product scope contains online commerce. It supplies prompts and common boundaries; it does not prescribe a solution or replace user research, policy review, or product decisions.

## Planning prompts

- Identify customer, operator, merchant, supplier, and support actors; do not assume every product has all of them.
- Define product, offer, price, availability, and inventory ownership.
- Map guest and authenticated journeys, including interruption and recovery.
- Separate an order's commercial state from payment, fulfillment, and refund states.
- Identify data ownership, source of truth, retention, privacy, and audit needs.
- Record jurisdiction, tax, currency, shipping, accessibility, and localization assumptions for later validation.

## Suggested decomposition

Load only the modules relevant to the confirmed scope: catalog and inventory, cart and checkout, order and payment/refund, and operations. Link identified concepts and operations to stable IDs in DOMAIN_MODEL.md and API_SPEC.md. Mark excluded capabilities explicitly in DECISIONS_ASSUMPTIONS.md.

## Decisions requiring evidence or human input

Do not invent policies for cancellation, returns, refund timing, inventory reservation, tax calculation, fraud review, payment methods, or fulfillment promises. Capture the decision owner, source, open question, and downstream artifacts. Security, privacy, legal, and payment review applicability depends on product scope and assurance requirements.
