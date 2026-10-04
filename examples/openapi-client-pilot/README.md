# OpenAPI client reference pilot

AI implementers onboarding a real product should follow
[AI_ONBOARDING.md](AI_ONBOARDING.md); this folder is the synthetic workflow
fixture, not product acceptance evidence.

This small Widgets product is the shared Phase 5B reference. It proves the AIPS
Phase 2 → Phase 4 → Phase 3 workflow with a real local HTTP service and consumer.
It does not claim that another product's API behavior has been accepted.

Run from the AIPS repository root after installing `requirements-validation.txt`
and `requirements-openapi.txt`:

```sh
python3 tests/evidence/openapi_client_pilot_lifecycle.py
```

The lifecycle copies this folder into a temporary standalone Git project. It
validates the canonical `api/openapi.json`, previews the pinned generator without
executing it, explicitly runs it twice, commits the generated client and Profile,
then runs operation coverage and project-native checks against a loopback service.
Finally, the Phase 3 inspector checks current OpenAPI, ownership, generated-file,
quality-command and Phase 4 execution evidence. Missing or altered generator
reports block the opt-in check; hand-edited client output cannot be replaced.

`tools/generate_client.py` is deliberately scoped to this contract. It verifies
the operations and authentication shape, then renders `tools/client_template.py.txt`.
Both files, the canonical spec, executable hash, version and argv are pinned in
`IMPLEMENTATION_PROFILE.yaml`. The generated output lives under
`client/generated/`, while `consumer.py` is product-owned. No external account,
secret or production service is used; `pilot-token` is a local fixture value.

## Multiple products

Keep this one shared reference example in AIPS. Each real product needs its own
canonical contract, Profile, client ownership records, generator report and
compile/contract/integration evidence in its repository. A product with multiple
independent API/client boundaries may need multiple local acceptance suites.
Add another AIPS example only when a materially different language, generator or
architecture reveals a reusable gap in the common workflow.

To onboard a real product, start with its existing project-native conventions,
confirm who owns the API contract, pin the repository-local generator, run the
adapter explicitly, and run tests against that product's actual service behavior.
The project may use a general-purpose generator; this example's bounded tool is
only a reproducible demonstration.
