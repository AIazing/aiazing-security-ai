# Decision 0001: dependency-free local fixture

Status: accepted for the first research fixture, not the production service.

## Choice

Use Python 3.9+ standard-library HTTP servers, immutable synthetic seed records, and unittest integration tests. Serve a minimal browser page and JSON API from the same origin. The available development runtime is Python 3.9; deployment Python selection remains open.

Start vulnerable and fixed instances under one evaluator-side controller, each bound exclusively to 127.0.0.1. The server does not initiate outbound network requests. The browser page uses local assets and same-origin requests.

## Module boundaries

- labs/invoice/seed.py: evaluator-only fixture records and expected ownership.
- labs/invoice/app.py: target HTTP behavior and private instance state.
- labs/invoice/control.py: start, reset, and teardown outside the target API.
- labs/invoice/verify.py: deterministic independent control checks and sanitized JSON evidence.
- labs/invoice/page.html and app.js: identical browser interface in both versions.

The evaluator obtains ownership directly from its controlled fixture definition. A future model receives observations and account handles, not the seed, passwords, evaluator labels, or variant names.

## Why

This makes the first vulnerability reproducible without package installation, containers, model downloads, or paid compute. Both variants share one application implementation; only the invoice-detail ownership check changes.

## Limits

The local boundary is loopback binding, not container, operating-system, or tenant isolation. Other processes on the same host can reach these deliberately vulnerable fixtures. Use a trusted development machine or an isolated disposable environment.

The Python development HTTP server, fixture authentication, and in-memory sessions are not a production service architecture. No arbitrary URL scanning, browser automation, model inference, assessment policy engine, or hosted network enforcement is implemented by this decision.

The fixture verifier writes local lab-control JSON. A separate [assessment engine](0002-local-assessment-engine.md) now adds policy enforcement and assessment-contract output. Production storage and the browser/inference stacks remain undecided.

## Verification

- python3 -m unittest tests.test_invoice_lab -v
- python3 -m labs.invoice.verify --output artifacts/invoice-lab-controls.json

The second command starts ephemeral loopback servers, verifies both variants, resets and repeats, then closes listeners before exiting. It returns a nonzero exit code if a control fails.
