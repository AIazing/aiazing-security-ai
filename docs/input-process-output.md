# Input, process, and output

This document defines the version 1 assessment contract. The [local HTTP engine](assessment-engine.md) implements the controlled invoice-lab slice, including validation, verification, reporting, and incomplete/rejected states. Public website scanning, browser automation, and model inference are not implemented.

## 1. Input: what the customer supplies

The customer starts with a URL. Before execution, the system must resolve an authorization record, explicit scope, and limits.

| Field | Required | Meaning |
| --- | --- | --- |
| Target | Yes | A web application or HTTP API entry URL |
| Allowed origins | Yes | Exact scheme, host, and port combinations the worker may contact |
| Authorization reference | Yes | Reference to a server-managed authorization record bound to the requesting tenant and approved scope |
| Environment | Yes | Public customer target or an isolated lab deployment |
| Mode | Yes | Public assessment or assessment with supplied test accounts |
| Limits | Yes | Request count, rate, duration, and model-token ceilings |
| Excluded paths | Yes; may be empty | Path prefixes the customer does not permit testing |
| Application context | Optional | Product description and expected permissions/workflows |
| Test accounts | Required for account mode | Account IDs, roles, and secret-store references; never raw passwords or session tokens |
| Export formats | Yes | JSON initially; human-readable formats are later features |

The web interface can fill defaults. The execution request must contain the explicit resulting values. The server may impose stricter limits than the request.

Version 1 accepts one entry URL per job. Additional approved origins support a separately hosted API, but discovery must not automatically expand scope to subdomains or third-party services. Version 1 does not accept arbitrary files, source repositories, or unrestricted natural-language tool instructions as targets.

See [request schema](../schemas/assessment-request.schema.json) and [example request](../examples/assessment-request.json).

### Semantic validation beyond JSON

Schema validation is only a structural check. Before queuing work, the server must:

1. Resolve the authorization reference for the current tenant. A customer-supplied string is not proof.
2. Verify authorization is current, covers the permitted actions/origins, and applies to the selected environment.
3. Normalize origins and reject credentials in URLs, unsupported schemes, invalid hosts/ports, and ambiguous encodings.
4. Require the entry URL's origin to appear in allowed origins. Excluded paths override included destinations.
5. Resolve credential references within this tenant/project and ensure the accounts are approved for this job.
6. Compile the allowed checks and actions with server-enforced limits; freeze this execution policy.
7. Enforce destination rules again at execution time across DNS changes, redirects, and browser subrequests.

A lab authorization is issued by the lab controller for a specific isolated deployment; typing "lab" cannot grant access to internal networks.

## 2. Process: what the system does

| Stage | Work performed | Result passed forward |
| --- | --- | --- |
| Validate | Check input, authorization, scope, and budgets | Accepted immutable job policy, or a rejected result |
| Prepare | Start an isolated worker, resolve credential references, establish test sessions | Approved tools and account handles |
| Discover | Observe permitted pages, forms, API calls, and user workflows | Application map and sanitized observations |
| Plan | Select supported checks using observations and expected permissions | Structured candidate actions and hypotheses |
| Execute | Validate every action against policy, then run approved browser/HTTP operations | Sanitized request/response or browser evidence |
| Verify | Compare expected and observed behavior with independent controls | Confirmed finding, observation, or unresolved candidate |
| Recommend | Explain impact and propose remediation grounded in verified evidence | Finding with fix guidance and limitations |
| Report | Deduplicate supported claims, record coverage, redact, validate output, and export | Final assessment result and artifact references |
| Retest later | Run an explicitly requested new job on the changed target | Linked retest result covering original and varied cases |

Steps from plan through verify can repeat while budgets remain. Stop on cancellation, lost authorization, exhausted limits, or a policy/worker failure. Always record why work stopped.

Discovery is also subject to policy. Browser clicks, page loads, and GET requests can change state; an HTTP method alone does not establish that an action is permitted.

### What the AI sees and returns

The model receives the task, permitted tool descriptions, role expectations, budget remaining, and sanitized observations. It receives account handles rather than credentials.

The model returns a structured proposed action, a candidate finding, or an explicit request to stop/abstain. The policy engine decides whether an action is allowed. The independent verifier, not the model's confidence, decides whether the evidence establishes the claimed behavior.

Target content cannot change these rules or provide authorization. The model cannot certify its own evidence, expand scope, or directly deploy a fix.

### Verification example

For a cross-account invoice issue:

1. Confirm the synthetic record belongs to Account B using the controlled fixture or supplied ground truth.
2. Establish Account B's legitimate access.
3. Request that record using Account A's session within the permitted scenario.
4. Check whether Account B's record data is returned to Account A.
5. Record the security assertion and controls. A status code alone is insufficient.

If ownership or access expectations cannot be independently established, keep the candidate as needing review.

## 3. Output: what the customer receives

One assessment result contains:

| Output | Contents |
| --- | --- |
| Identity and status | Assessment ID, target, timestamps, terminal job status, illustrative flag |
| Coverage | Areas/checks attempted, not run, or inconclusive, and scope limitations |
| Findings | Title, severity, verification status, expected/observed behavior, redacted evidence, reproduction steps |
| Fix guidance | Recommended server, configuration, or workflow changes and what to retest |
| Usage | Observed requests, elapsed time, model tokens |
| Errors | Structured stage/error codes with sanitized explanations |
| Artifacts | Authorized references to JSON and, later, human-readable reports |

See [result schema](../schemas/assessment-result.schema.json), [finding schema](../schemas/finding.schema.json), and [illustrative result](../examples/assessment-result.json).

### Terminal job statuses

- completed: the planned checks finished. This does not certify that the website is secure.
- partial: usable results exist, but some planned work could not complete.
- failed: execution could not produce usable assessment results.
- cancelled: execution was stopped by a cancellation request; preserve any available coverage and evidence.
- rejected: input/authorization/policy checks blocked execution; no target testing occurred.

Finding verification states remain separate: candidate, needs_review, confirmed, or observation. A high-impact theory is not a confirmed finding. Severity may remain unassessed.

An empty finding list means only that this run returned no findings. Coverage, errors, and job status determine what was actually checked. The result must not describe a failed or incomplete assessment as a clean scan.

If validation rejects an invalid target URL, return a null target_url instead of echoing unsafe raw input. Rejected jobs have no start timestamp, target requests, model calls, tested checks, or findings. Non-rejected jobs record a normalized target URL and start timestamp. The server also checks timestamp ordering, actual budget consumption, tenant access to artifacts, and consistency between coverage and terminal status; these are semantic checks beyond the schemas.

## 4. Fixes and retesting

Without source access, provide evidence-based implementation guidance rather than an invented code patch. With an approved repository integration, a later version may propose an exact patch for human review.

Retesting is a new assessment with its own current authorization and budgets, linked to the original assessment and findings. Confirm the original case, relevant variations, and normal functionality. "Resolved for tested cases" is narrower than a guarantee that the entire application is secure.

## 5. First implementation slice

Input: an isolated fixture URL, a lab authorization record, two test-account references, explicit scope, and small execution budgets.

Process: collect account/record observations, run the approved access-control scenario, and evaluate independent positive and safe controls.

Output: a JSON assessment with one verified finding for the vulnerable fixture, no confirmed finding for the safe control, and explicit evidence/limitations for both.

Model adaptation follows after this workflow produces reviewed, reproducible episodes.
