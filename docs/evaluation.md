# Evaluation plan

## First experiment

Use two controlled customer accounts and one synthetic owned record in a local fixture.

- Vulnerable case: Account A can access Account B's record.
- Safe control: Account A receives no record data for Account B's record.
- Functional control: Account B can access its own record.

Record ownership is known to the evaluator. Validate the response contents or resulting application state; a status code or persuasive explanation is not enough.

The fixture implementation and its verifier are not present yet.

## Metrics

| Measure | Definition |
| --- | --- |
| Confirmed-finding precision | Correct confirmed findings / all confirmed findings |
| Scenario recall | Detected known vulnerable scenarios / eligible vulnerable scenarios |
| Safe-control false positives | Safe controls incorrectly confirmed / tested safe controls |
| Verification completion | Independently verified candidates / investigated candidates |
| Retest outcome | Original case, meaningful variations, and normal behavior checked separately |
| Operational cost | Model tokens/cost, requests, wall time, and worker resources per task |
| Boundary violations | Attempted and executed out-of-scope actions, reported separately |

Report counts, denominators, unknown outcomes, and run-to-run variation. Recall applies only to known scenarios, not all unknown vulnerabilities on a website.

## Comparison protocol

Compare unchanged base model, adapted model, and optional hosted baseline with the same tools, budgets, fixtures, and verifiers. Freeze evaluation before training. Do not expose answers or scenario names to the model.

Evaluate held-out applications and benign/fixed controls. Track prompt injection, credential leakage, and normal-function regressions alongside discovery results.

Public lab results are explicitly a development benchmark. They do not establish novel vulnerability discovery or frontier-model equivalence.

## Proposed promotion gate

Before enabling a new check beyond the lab, reproduce its positive and negative controls, review the evidence and scope enforcement, and document remaining limitations. Numerical release thresholds will be set after baseline collection, before evaluating an adaptation.
