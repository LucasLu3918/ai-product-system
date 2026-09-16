# Product Creation

Use for a new product or major greenfield initiative.

For a complete product request, use `orchestration/PRODUCT_DELIVERY.md` as the lifecycle coordinator.

Flow:

~~~text
Discovery / User Assets
→ Resolve Product Workspace
→ Draft PRODUCT.yaml
→ Product Definition
→ UX / Visual / Brand
→ Risk Profile / Security Assurance
→ API / Data / Architecture / Deployment Units / Delivery Planning
→ Persist Reproducible Planning Package
→ Cross-role Consistency Review
→ Gate 1: Human Planning Package Approval
→ Initial Implementation Items + Recommended Flow
→ Gate 2: Human Implementation Readiness Approval
→ Implementation
→ Local Environment + Automated Verification
→ Security / Independent Review
→ Release Candidate
→ Staging (when applicable)
→ Release Readiness
→ Production Promotion
→ Post-deploy Verification
~~~

Ask only blocking questions. Translate non-expert user intent into professional product/architecture/delivery decisions and offer safe defaults.

A complete product uses one discoverable Product Workspace. Frontend/backend/worker components are independent Deployment Units; separate repositories are optional, not mandatory.

Use:
- `orchestration/PLANNING_PACKAGE.md`
- `orchestration/PRODUCT_DELIVERY.md`
- `orchestration/RELEASE_READINESS.md`
- `templates/product/`
- `templates/delivery/`

Security remains risk-proportional. Security is considered during planning and verified again during implementation/release.

Production delivery is complete only after the exact candidate is deployed, post-deploy verification succeeds, observability/recovery information is available, and workspace state is persisted.
