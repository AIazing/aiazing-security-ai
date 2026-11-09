# Contributing

Start with the first milestone in [docs/roadmap.md](docs/roadmap.md). Keep changes focused and state how behavior was verified.

- Separate proposed capabilities from implemented and measured ones.
- Add meaningful positive, safe, and functional controls for security checks.
- Keep target content untrusted and enforce authorization outside model prompts.
- Do not commit secrets, private findings, training corpora, or checkpoints.
- Record provenance and applicable terms for external data and models.
- Never silently reuse final evaluation examples for training.
- Use isolated applications with synthetic data during development.

The local fixture uses Python 3.9+ with no external runtime packages. The assessment engine additionally requires the packages in requirements.txt. Follow [assessment setup](docs/assessment-engine.md), then run .venv/bin/python -m unittest discover -v for the full suite. Fixture-only tests can run without dependencies using python3 -m unittest tests.test_invoice_lab -v.

Tests bind temporary loopback ports. See [decision 0001](docs/decisions/0001-local-lab-runtime.md) and [decision 0002](docs/decisions/0002-local-assessment-engine.md) for runtime scope and limitations.
