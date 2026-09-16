# Product Workspace

A complete product should have one discoverable System of Record even when it contains multiple deployable units or repositories.

Recommended shape:

~~~text
product/
├── PRODUCT.yaml
├── README.md
├── .ai/
├── docs/
├── brand/
├── apps/
│   ├── frontend/
│   └── backend/
├── packages/
├── database/
├── tests/
├── infra/
├── deployment/
├── scripts/
└── Makefile
~~~

Do not create non-applicable directories.

## Repository strategy

Default to a monorepo when it simplifies:
- shared contracts;
- coordinated changes;
- E2E tests;
- documentation;
- local developer experience.

Use multi-repo only when evidence such as independent ownership, permissions, release cadence, scale or shared-service boundaries justifies it.

PRODUCT.yaml is the navigation manifest regardless of repository strategy.
