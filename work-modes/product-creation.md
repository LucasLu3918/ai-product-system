# Product Creation

Use for a new product or major greenfield initiative.

For a complete product request, use `orchestration/PRODUCT_DELIVERY.md` and `orchestration/QUALITY_PLANNING.md`.

Flow:

~~~text
Discovery / User Assets
→ Resolve Product Workspace
→ Draft PRODUCT.yaml
→ Q1/Q2/Q3 Quality Planning
→ Product Definition
→ UX / Visual / Brand
→ Risk Profile / Security Assurance
→ API / Data / Architecture / Deployment Units / Delivery Planning
→ Initial Resource / Cost / Time Estimate
→ Persist Reproducible Planning Package
→ Cross-role Consistency Review
→ Gate 1: Human Planning Package Approval
→ Initial Implementation Items + Recommended Flow
→ Gate 2: Human Implementation Readiness Approval
→ Implementation + Provider-neutral Observability Instrumentation
→ Local Environment + Automated Verification
→ Security / Independent Review
→ Applicable Performance / Usability / Reliability Evidence
→ LOCAL_COMPLETE
→ Production already requested?
   ├─ yes → Production Enablement
   └─ no  → ask whether to continue
→ Production Enablement when applicable
→ Refined Resource / Cost / Time Estimate
→ Staging (when applicable)
→ Release Readiness
→ Production Promotion
→ Post-deploy Verification
→ PRODUCTION_VERIFIED
~~~

Ask only blocking questions. Translate non-expert intent into professional quality/architecture/delivery decisions and offer safe defaults.

A complete product uses one discoverable Product Workspace. Frontend/backend/worker components are Deployment Units; separate repositories are optional.

Use:
- `orchestration/QUALITY_PLANNING.md`
- `orchestration/PLANNING_PACKAGE.md`
- `orchestration/PRODUCT_DELIVERY.md`
- `orchestration/RELEASE_READINESS.md`
- `templates/quality/`
- `templates/product/`
- `templates/delivery/`

Security remains risk-proportional. Observability requirements are planned before vendor selection. Production delivery is complete only at PRODUCTION_VERIFIED.
