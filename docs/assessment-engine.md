# Local assessment engine

The first assessment engine is implemented for the controller-owned invoice lab. It uses deterministic collection and independent verification, not an AI model. It cannot scan arbitrary websites.

For a working interface, use the [local dashboard](dashboard.md). It runs this same engine and shows real progress, findings, evidence, and exports.

## Setup

From the repository root with Python 3.9+:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
~~~

The only direct runtime dependency is the pinned JSON Schema validator. There is no AI API, model download, GPU requirement, or cloud service.

## Run a full comparison

~~~sh
.venv/bin/python -m security_ai --output artifacts/assessment-demo
~~~

The command starts both lab versions on temporary loopback ports, issues scoped grants, assesses each, exports artifacts, and closes the lab. The expected result:

| Fixture | Job status | Confirmed findings | Target requests |
| --- | --- | --- | --- |
| Vulnerable | completed | 1 | 10 |
| Fixed | completed | 0 | 10 |

Zero findings on the fixed fixture applies only to the tested scenario. It is not a general security certification.

To assess one fixture:

~~~sh
.venv/bin/python -m security_ai --fixture vulnerable
.venv/bin/python -m security_ai --fixture fixed
~~~

To demonstrate an interrupted assessment:

~~~sh
.venv/bin/python -m security_ai --fixture vulnerable --max-requests 1
~~~

That command returns a partial result and a nonzero process exit code. It must not be presented as a clean scan.

## Input and authorization

The trusted lab adapter builds a schema-valid request using the live controller's exact origin, two account handles, credential references, and request/time limits. A private registry binds the grant to its tenant, project, permitted origin, accounts, and expiry.

The CLI deliberately has no URL or raw-credential parameter. Setting environment to isolated_lab in a JSON object does not issue a grant. Reset and shutdown revoke outstanding grants.

Programmatic entry: prepare_assessment in labs/invoice/assessment.py builds the trusted bindings; AssessmentRunner.run accepts the request and an optional cancellation event. These are local research interfaces, not a network API.

## Processing

1. Validate the request schema and resolve authorization within the caller's context.
2. Reject unsupported environments, modes, targets, origins, accounts, and malformed scope.
3. Freeze the policy and cap budgets to server ceilings.
4. Establish separate sessions using broker-held credentials.
5. Read identities and each account's invoice list.
6. Select the observed invoice; collect owner, other-account, anonymous, and missing-record responses.
7. Compare observations with independent ownership/content expectations.
8. Export a confirmed finding only when its controls pass, or record verified denial/inconclusive coverage.

The collector does not receive a vulnerable/fixed label. The private verifier receives evaluator assertions, separate from target responses. A full invoice in a 403 response still constitutes exposure; a 200 with the wrong content does not prove it.

## Execution boundaries

- Only literal 127.0.0.1 addresses at the registered port are connected; the transport does not resolve names, use proxies, or follow redirects.
- Each action must match an approved HTTP method/path/account and the immutable origin. Excluded paths override allowed actions.
- Grants are checked before actions and during rate waits; reset, shutdown, expiry, or revocation prevents further requests.
- Request attempts, rate spacing, elapsed time, response bytes, and network socket timeouts are bounded. No model runs; model token usage is zero.
- HTTP bodies are capped at 64 KiB, must be JSON, and reject nonfinite numbers. No HTML, JavaScript, or response-supplied instructions are executed.
- Cancellation is checked between operations and interrupts rate waits. Network operations have a socket timeout capped at three seconds.

Time/cancellation checks are cooperative, not a hard process deadline. Socket timeouts do not provide preemptive isolation against every slow-stream/header behavior. A hardened worker with forced teardown, browser subrequest controls, and general network isolation remains future work.

## Output and evidence

Each job creates an assessment-ID directory containing:

- report.json: validated against assessment-result.schema.json, including findings, coverage, usage, errors, and fix guidance.
- evidence.json: sanitized observations indexed by stable trace IDs.

Finding references use artifact URIs with JSON pointers into evidence. They are local references, not public download URLs.

Files are written through temporary files and replaced atomically per file. Job directories are private to the local user; files use temporary-file permissions. Storage is local and is not an encrypted, tenant-aware hosted artifact service.

Passwords, known session values, emails, and sensitive response keys are redacted. Login request bodies and authorization headers are not exported. Artifacts use actual observations from synthetic applications and are marked illustrative=false; they are not model-generated discoveries.

Incomplete runs preserve their coverage and errors. Rejected runs have no target requests, findings, or start timestamp. Export failures fail the command rather than producing a successful-looking report.

## Verification

~~~sh
.venv/bin/python -m unittest discover -v
~~~

Tests cover vulnerable/fixed outcomes, reordered accounts, authorization/project boundaries, expiry/revocation, reset/shutdown, excluded/unsupported actions, request/rate/time budgets, cancellation, DNS avoidance, redirects, oversized/invalid responses, independent identity/content controls, and secret redaction.

## Next increment

Define a model observation/action contract and a self-hosted inference adapter using this policy/verification path. Before enabling a model-driven action loop, add its specific adversarial and boundary tests. Browser collection, public-target authorization, and hosted deployment remain distinct later work.
