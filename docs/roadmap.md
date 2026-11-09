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
- [ ] Define structured tool requests and an enforced lab scope.
- [ ] Add browser/HTTP evidence collection and an independent verifier.
- [ ] Export a validated JSON finding with redacted evidence.

The local fixture and its scripted control verifier are available; the general collector, policy engine, and assessment-contract export remain pending. See the [lab instructions](../labs/invoice/README.md). Loopback development isolation is implemented; OS/container isolation is not.

Acceptance: distinguish the vulnerable case from safe and functional controls with reproducible artifacts, then add the policy-gated collector and report contract. No broad scanner or model training is required for this milestone.

## Milestone 2: baseline system

- [ ] Integrate an unchanged model through a provider-neutral interface.
- [ ] Add a small set of pinned lab scenarios from the catalog.
- [ ] Measure precision, recall, abstention, cost, and boundary enforcement.
- [ ] Build the web setup/findings flow and human-readable report export.

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
