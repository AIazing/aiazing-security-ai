# Delivery work plan

## Planning basis

Build a specialized security transformer adaptation on an existing open-weight foundation, hosted by us. External AI APIs are not a dependency of the initial plan. We have not selected, downloaded, or trained a model.

The first release accepts an authorized website/API URL, investigates supported behaviors, verifies findings, recommends fixes, and exports results. Its initial research environment is isolated labs.

Completed: product definition, architecture, input/process/output schemas and examples, evaluation strategy, illustrative dashboard, local invoice lab, and the policy-gated HTTP assessment slice with independent verification and validated JSON exports.

Not implemented: general crawling, browser automation, model inference/training, production web application, hosted authorization/storage, or OS-level worker isolation. The implemented verifier covers the controlled invoice scenario, not arbitrary vulnerabilities.

This is a dependency-based plan, not a calendar commitment. Confirm hardware, compute budget, available engineering capacity, and security-review capacity before assigning dates or purchasing infrastructure.

## Delivery sequence

| Phase | Deliverable | Depends on | Exit condition |
| --- | --- | --- | --- |
| 1. Reproducible lab | Vulnerable and fixed versions of one access-control scenario | Existing specifications | Positive, safe, and normal-function controls are reproducible |
| 2. Execution and verification | Scoped worker, evidence collection, verifier, JSON result | Phase 1 | A complete assessment works without relying on model judgment |
| 3. Self-hosted baseline | Unchanged model connected to the same tools and budgets | Phase 2 and model/hardware selection | Repeatable measured baseline with documented failures |
| 4. Web research preview | URL/setup, assessment progress, findings, JSON export, retest request | Phase 2; integrate AI after Phase 3 | End-to-end local lab workflow through the web interface |
| 5. Dataset and adaptation | Reviewed dataset, trained adapter, held-out comparison, model card | Phase 3; expanded scenarios and reviewed data | Adaptation meets predeclared evaluation gates |
| 6. Authorized pilot | Hardened hosted deployment and a limited customer pilot | Phase 4 and pilot security gate | Documented results and sustainable operating costs on authorized targets |

Phases 4 and 5 can proceed independently once their prerequisites exist. A limited pilot can use the unchanged self-hosted baseline if the adaptation does not improve results; it must be labeled accordingly. Model-release criteria and hosted-service security criteria are separate.

## Phase 1: reproducible lab

LAB-01 through LAB-05 are implemented for the local loopback fixture. SYS-01 is recorded in [decision 0001](decisions/0001-local-lab-runtime.md). The lab instructions and verification commands are in [labs/invoice/README.md](../labs/invoice/README.md).

Verification: 15 integration tests cover API controls, browser asset serving, reset, session isolation, request boundaries, evidence, and teardown. The CLI control run passed all eight controls across both variants and reproduced its results after reset. Interactive start/reset/quit also passed a smoke test. Artifacts are stored locally under the ignored artifacts directory. This verifies the lab's intended behavior, not an AI model's discovery capability.

LAB-04 currently means loopback-only listeners, same-origin browser requests, no outbound server requests, and evaluator controls outside the HTTP API. Container/OS and tenant isolation remain future worker and hosted-service work.

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| LAB-01 | Define the first scenario | Two synthetic customer accounts, one owned invoice, expected access rules, and evaluator-only ground truth |
| LAB-02 | Implement vulnerable/fixed fixtures | Identical normal behavior; the intended access-control flaw distinguishes the versions |
| LAB-03 | Implement seed/reset | Repeated resets restore the same accounts, ownership, and records |
| LAB-04 | Isolate the lab | Lab-only network/destinations, synthetic data, deterministic startup/teardown, no public exposure |
| LAB-05 | Establish independent controls | Owner access succeeds; non-owner access distinguishes vulnerable/fixed versions; unauthenticated behavior is specified |

Do not add multiple public lab integrations yet. The first scenario establishes the pattern. Before calling it complete, demonstrate the controls against both versions and retain reproducible artifacts.

## Phase 2: execution and verification

The HTTP lab slice of SYS-01 through SYS-06 is implemented; see [engine instructions](assessment-engine.md) and [decision 0002](decisions/0002-local-assessment-engine.md). It validates requests and reports, enforces registered origins/actions and budgets, brokers credentials, collects sanitized observations, and independently verifies the invoice scenario.

SYS-07 has HTTP tests for scope, grants/revocation, DNS avoidance, redirects, limits, cancellation, response handling, and target-supplied text remaining inert. Browser subrequests, model-directed adversarial behavior, preemptive worker teardown, and general network/OS isolation are still pending. Do not mark those complete based on the HTTP fixture.

Verification: the full 40-test suite passed. The documented CLI produced completed, schema-valid reports with one confirmed finding for the vulnerable fixture and none for the fixed fixture (10 requests each). A separate one-request run exported partial coverage and returned exit code 1 as intended.

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| SYS-01 | Choose runtime and module boundaries | Small architecture decision recording backend language, browser/HTTP interfaces, local artifact storage, and test commands |
| SYS-02 | Compile and enforce a lab job policy | Validate input and resolved authorization; enforce exact approved destinations, excluded actions/paths, and request/time budgets |
| SYS-03 | Build tools and credential handling | Browser/HTTP operations use account handles; credentials do not enter model context or exported evidence |
| SYS-04 | Capture sanitized evidence | Trace IDs, account handles, requests/responses, relevant browser state, and redaction checks |
| SYS-05 | Implement the independent verifier | Ownership and control assertions establish the invoice issue; a status code alone cannot pass |
| SYS-06 | Produce final JSON results | Contract-valid completed, partial, failed, cancelled, and rejected results with coverage and errors |
| SYS-07 | Test execution boundaries | Redirects, browser subrequests, target-supplied instructions, limits, cancellation, and worker teardown cannot bypass policy |

Use a deterministic scripted scenario driver initially. It exercises the same tool interfaces the model will later use and isolates infrastructure failures from model failures.

## Phase 3: self-hosted baseline

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| BASE-01 | Select candidate model and hardware | Document eligible model terms, immutable revision, tool-use support, memory requirements, deployment options, and proposed compute cap |
| BASE-02 | Define model I/O | Versioned observation/action structures with account handles, context selection, budget state, and abstention |
| BASE-03 | Connect local inference | Run an unchanged model behind the interface; no external AI API required |
| BASE-04 | Implement the reasoning loop | Controller requests proposals, policy gates execution, tools return observations, verifier evaluates candidates, report builder preserves verification status |
| BASE-05 | Expand development scenarios | Pin chosen lab versions; add reviewed vulnerable, fixed, and benign controls; track provenance |
| BASE-06 | Measure baseline | Precision, scenario recall, false positives, abstention/inconclusive outcomes, latency, token use, resource use, and boundary violations |

Hardware allocation and paid compute need a concrete estimate before execution. Do not start with a large GPU purchase or a foundation-model pretraining run.

Baseline measurements must distinguish discovery from merely explaining a supplied finding. Keep tool permissions, context, request limits, and verifiers fixed when comparing models.

## Phase 4: web research preview

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| WEB-01 | Project and assessment setup | URL, lab authorization reference, explicit scope, account references, and limits create a valid job |
| WEB-02 | Job progress and cancellation | Show stages, stop reasons, partial coverage, and cancellation outcome |
| WEB-03 | Findings workspace | Evidence, severity, verification status, expected/observed behavior, fixes, and limitations |
| WEB-04 | JSON export and retest flow | Download a sanitized result; create a separately authorized retest job linked to the original |
| WEB-05 | Human-readable report | Add HTML/PDF only after JSON output is stable; preserve coverage and uncertainty in every format |

The local research preview uses controlled lab targets. Internet-facing customer use requires the Phase 6 security gate. User authentication and authorization must exist before any shared deployment.

## Phase 5: reviewed data and specialized model

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| ML-01 | Define episode storage and review | Provenance, versions, role expectations, sanitized actions/observations, independent outcomes, reviewer decisions |
| ML-02 | Curate examples | Positive, safe/fixed, false-positive, inconclusive, and remediation examples; no automatic customer-data reuse |
| ML-03 | Freeze evaluation and release gates | Split by application/scenario/version lineage; keep evaluator answers out of model inputs; set numerical thresholds before training |
| ML-04 | Train a small adaptation | Reproducible supervised adaptation, initially for evidence assessment and fix guidance; record settings and compute use |
| ML-05 | Compare adapted and unchanged models | Same tools, budgets, prompts where applicable, and held-out cases; report uncertainty and regressions |
| ML-06 | Package release evidence | Adapter/checkpoint as permitted, training recipe, model card, limitations, data provenance, and reproducible evaluation |

Do not promise a number of training examples before checking diversity and quality. Data sufficiency is established with development learning curves; final evaluation is not used for iterative tuning.

If the adapted model does not meet the predeclared gates, document the result and retain the baseline. An improved report-writing score alone does not establish improved vulnerability discovery.

## Phase 6: hosted service and authorized pilot

| ID | Work item | Deliverable and acceptance |
| --- | --- | --- |
| PILOT-01 | Establish tenant and target authorization | Login, project permissions, ownership/authorization verification, expiry/revocation, credential access, and artifact isolation |
| PILOT-02 | Enforce hosted network boundaries | DNS/redirect/subrequest handling, rebinding resistance, internal/control-plane blocking, approved origins, worker isolation, budgets, and teardown |
| PILOT-03 | Operate the service | Encryption, credential rotation, retention/deletion, monitoring, failure recovery, and audit records |
| PILOT-04 | Run a limited authorized pilot | Agreed scopes and supported check families; review findings and measure developer usefulness and false-positive cost |
| PILOT-05 | Validate paid hosting economics | Measure AI/worker/storage/support costs; set usage-based limits and proposed pricing from observed costs |
| PILOT-06 | Publish operating boundaries | Supported checks, known limitations, data practices, model/base identity, and a private vulnerability-reporting route |

Promotion requires demonstrated isolation and scope enforcement, actionable evidence, documented incomplete outcomes, and an operational response path. A functioning dashboard is not sufficient.

Scheduling, integrations, team workflows, and broader target types follow pilot feedback. They should not delay the first verified scenario.

## First implementation iteration

LAB-01 through LAB-05 and SYS-01 are complete for the local development boundary. The implemented review demonstrates:

1. One command starts the isolated fixture and seeds two test accounts.
2. The evaluator identifies record ownership without disclosing its answer to a model.
3. A legitimate owner can access the record in both versions.
4. The non-owner can access it only in the vulnerable version.
5. Reset and teardown are repeatable.
6. The runtime decision and verification command are documented.

No trained model, public scanning, or paid compute is needed for this iteration. The subsequent HTTP iteration is now implemented: policy-gated collection, independent verification, and validated JSON output. The next model increment defines observation/action contracts and a self-hosted adapter.

## Decisions before dependent work

| Decision | Needed by | How to resolve |
| --- | --- | --- |
| Runtime stack | SYS-01 | Prefer the smallest stack that supports reliable browser tooling, testing, and future model integration |
| Hardware and compute budget | BASE-01 / ML-04 | Compare candidate memory/latency needs and obtain a bounded run estimate |
| Base model and applicable terms | BASE-01 | Review candidate capability, hosting, adaptation, and redistribution requirements |
| Supported check families | BASE-05 | Add only scenarios with defined expectations and independently reproducible controls |
| Numerical model-release thresholds | ML-03 | Set from baseline and product requirements before adaptation evaluation |
| First pilot target and scope | PILOT-04 | Use an explicitly authorized application with suitable test accounts and agreed limits |

Keep task IDs stable in commits and future issue tracking. Update completion status only when the deliverable and its acceptance evidence exist.
