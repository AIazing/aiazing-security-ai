# Implementation roadmap

The [delivery work plan](work-plan.md) breaks this roadmap into task IDs, dependencies, deliverables, and acceptance criteria. The initial model path is a self-hosted open-weight baseline followed by our specialized adaptation; external AI APIs are not required.

## Current: definition

- [x] Describe product, architecture, model strategy, and evaluation.
- [x] Record candidate lab sources and finding output format.
- [x] Preserve the illustrative dashboard concept.
- [x] Define assessment input, process, output, and delivery work breakdown.
- [ ] Select the first base-model candidates and deployment hardware.

## Milestone 1: one reproducible experiment

- [x] Build a loopback-only vulnerable/fixed access-control fixture with two test accounts.
- [x] Add deterministic seed/reset and evaluator-only ground truth.
- [x] Define structured HTTP tool operations and an enforced lab scope.
- [x] Add HTTP evidence collection and an independent invoice verifier.
- [x] Export validated JSON findings with redacted evidence and fix guidance.

The local HTTP slice is complete: fixture, input validation, grant/scope enforcement, credential handling, deterministic collection, independent verification, and contract-valid reports. See the [engine instructions](assessment-engine.md). General crawling, browser automation, and OS/container isolation are not implemented.

Acceptance: distinguish the vulnerable case from safe and functional controls with reproducible artifacts, then add the policy-gated collector and report contract. No broad scanner or model training is required for this milestone.

## Milestone 2: baseline system

- [ ] Define the model observation/action contract and self-hosted inference adapter.
- [ ] Integrate an unchanged model through a provider-neutral interface.
- [ ] Add policy-enforced browser collection and its boundary tests.
- [ ] Add a small set of pinned lab scenarios from the catalog.
- [ ] Measure precision, recall, abstention, cost, and boundary enforcement.
- [ ] Build the web setup/findings flow and human-readable report export.

The local dashboard now supports fixture selection, progress/cancellation, findings/evidence/fix review, saved JSON downloads, and project status. Customer URL/ownership setup, linked retests, and HTML/PDF exports remain pending. See [dashboard instructions](dashboard.md).

## Milestone 3: specialized model

- [ ] Curate reviewed episodes and freeze held-out evaluation.
- [ ] Select a base model and record its terms/revision.
- [ ] Train an initial adaptation for evidence assessment and fix guidance.
- [ ] Compare against the unchanged base and publish a model card.

Acceptance: measurable benefit on held-out tasks without unacceptable regressions. If adaptation does not help, retain the baseline and document the result.

## Milestone 4: hosted pilot

- [ ] Add ownership verification, tenant isolation, credential management, and retention controls.
- [ ] Enforce scope across DNS, redirects, browser requests, and internal destinations.
- [ ] Add scheduling, cancellation, usage limits, and retests.
- [ ] Pilot on explicitly authorized applications with documented limitations.
