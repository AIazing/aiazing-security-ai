# Decision 0002: controlled HTTP assessment engine

Status: accepted for the local research slice.

## Choice

Use Python for the deterministic controller, policy-gated HTTP tools, private lab grant/credential registry, independent scenario verifier, and local JSON export. Validate request and report contracts with jsonschema 4.25.1.

Runtime JSON Schema validation avoids maintaining a second hand-written copy of the contract. Schema resources are registered from repository files; unknown references cannot trigger network schema retrieval.

The transport uses direct literal-IP loopback sockets and an exact action allowlist. Public hosts, redirects, proxies, and arbitrary endpoints are unsupported. We do not build a generic crawler before the verified scenario works.

## Module boundaries

- security_ai/contracts.py: local schema registry and validation.
- security_ai/policy.py: caller context, grant resolution, credential references, immutable execution policy, and budgets.
- security_ai/transport.py: scoped HTTP operations, private session handling, bounded JSON responses, sanitized observations.
- security_ai/invoice.py: scripted observation collection and independent verification; neither uses fixture mode.
- security_ai/runner.py: lifecycle, terminal status, coverage, findings, local artifacts.
- labs/invoice/assessment.py: trusted adapter issuing bindings for live controller-owned fixtures.

No model is integrated. The verifier's evaluator assertions stay separate from any future model context. The collector discovers the candidate invoice through account observations.

## Limits

The grant registry and artifact store are local, in-process implementations. They do not constitute customer identity, production secret management, encrypted tenant storage, or OS isolation.

Timers are cooperative between operations; network I/O has capped socket timeouts. Hardened, preemptive worker cancellation and browser/network containment are not implemented here.

Model selection, inference/training, browser tooling, broader checks, and production infrastructure remain separate decisions.
