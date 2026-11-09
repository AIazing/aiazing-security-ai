# System architecture

See the [input, process, and output contract](input-process-output.md) for request/result schemas and the boundaries between model decisions, policy enforcement, and verification.

## Components

| Component | Responsibility |
| --- | --- |
| Web dashboard and API | Projects, authorization, scope, jobs, reports |
| Job scheduler | Queue work with explicit request, time, and cost budgets |
| Policy engine | Enforce approved destinations and actions outside the model |
| Isolated worker | Run browser and HTTP tools per assessment |
| Model adapter | Exchange structured observations and proposed actions |
| Evidence store | Retain encrypted artifacts with access and deletion controls |
| Independent verifier | Check observed outcomes against scenario-specific expectations |
| Report generator | Produce sanitized findings and fix guidance |
| Evaluation harness | Compare model/system variants on resettable applications |

## Runtime path

1. API creates a job with immutable scope and budget.
2. Worker discovers permitted pages and records observations.
3. Model proposes a structured action; policy engine validates it.
4. Tools execute only approved actions and return sanitized observations.
5. Verifier checks security behavior using independently defined assertions.
6. Reporting records confirmed findings, observations, and unresolved candidates separately.

The model has no direct shell, unrestricted network, credential store, or production deployment authority.

## Network and tenant isolation

- Validate destinations when connecting, including DNS results, redirects, browser subrequests, and WebSocket connections.
- Block cloud metadata and internal/control-plane destinations in the hosted service. A separate isolated lab network can explicitly allow its lab targets.
- Use network enforcement and approved destination resolution to address DNS rebinding; a one-time hostname check is insufficient.
- Apply origin restrictions to browser tools, not just direct HTTP requests.
- Isolate workers and evidence by tenant and job; enforce request, concurrency, timeout, response-size, and compute limits.
- Provide cancellation and guaranteed teardown.

## Sensitive and untrusted content

Inject short-lived test credentials through a credential broker. Avoid sending raw session secrets to the model. Redact secrets and personal data before reports or model requests.

Website content and tool output are untrusted data, not instructions. A target page cannot change scope, authorize tool use, or override policy.

## Verification

Evidence should include a control when relevant. For cross-account access, compare a legitimate owner request with the other test account's request and verify the returned record's ownership. An HTTP 200 alone is insufficient.

Where possible, use an evaluator-only fixture or state inspection to establish ground truth. The model must not invent its own success criterion and certify that it passed.

## Technology decisions

Language, database, queue, browser runtime, inference stack, and model provider are pending. Choose them after the first scenario and deployment requirements are specified. All model integrations use the same observation/action/finding contracts.
