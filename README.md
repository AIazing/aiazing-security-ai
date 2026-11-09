# AIazing Security AI

An open-source project to build a specialized AI model and assessment system that investigates authorized websites and APIs, verifies security findings, explains fixes, and exports reports.

**Status: the local invoice lab and policy-gated HTTP assessment engine are implemented, including verified findings, fix guidance, and contract-valid JSON reports. There is no trained model, general website scanner, or measured model benchmark yet.**

## Run a local assessment

With Python 3.9+, from the repository root:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m security_ai --output artifacts/assessment-demo
~~~

The command starts its own vulnerable/fixed lab instances, assesses them, exports sanitized reports and evidence, and shuts them down. The vulnerable fixture produces one confirmed finding; the fixed fixture produces none for the tested scenario. Each full run makes 10 target requests.

See [assessment engine instructions](docs/assessment-engine.md) for scope, limits, failure states, and output. No model API, model download, GPU, or cloud service is required. The schema validator is the only direct external package.

## Run the first milestone

Python 3.9+ is sufficient; no external packages, model API, or GPU are required.

~~~sh
python3 -m labs.invoice
~~~

This starts vulnerable and fixed invoice applications on loopback only. See the [lab instructions](labs/invoice/README.md) for synthetic accounts, ports, reset, and shutdown.

To run independent controls and save sanitized evaluator evidence:

~~~sh
python3 -m labs.invoice.verify --output artifacts/invoice-lab-controls.json
python3 -m unittest tests.test_invoice_lab -v
~~~

The verifier starts its own temporary-port lab, checks both versions, resets and repeats, then shuts down. Its JSON is lab-control evidence, not a complete assessment report or AI discovery result.

## The intended experience

1. Supply a website URL and prove authority to test it.
2. Define permitted hosts, actions, request limits, and optional test accounts.
3. Explore the application through a browser and HTTP tools.
4. Investigate candidate vulnerabilities and verify their impact.
5. Return findings with evidence, reproduction steps, limitations, and fix guidance.
6. Export reports and retest after changes.

The initial target type is a web application or HTTP API. Repository, file, mobile, and infrastructure analysis are separate future integrations, rather than an unrestricted “anything” input.

## Our model

We aim to develop a specialized transformer model, initially by fine-tuning an existing open-weight model hosted by us. We will compare it against unchanged self-hosted base models before claiming improvements. External AI APIs are not required by the initial plan. The base model and its redistribution terms have not been selected.

Model responsibilities: choose relevant checks, interpret browser/request observations, assess evidence, and recommend fixes. Independent tools and verifiers establish whether the claimed security behavior occurred.

A URL alone is not sufficient input to a language model: the surrounding system must collect observations from the target. Source access is optional for behavioral testing, but normally needed for a repository-specific code patch.

## Start with known vulnerabilities

We will build a repeatable lab using deliberately vulnerable applications:

| Candidate lab | Intended use | Integration status |
| --- | --- | --- |
| [OWASP Juice Shop](https://github.com/juice-shop/juice-shop) | Browser workflows and modern web application assessment | Planned |
| [OWASP crAPI](https://github.com/OWASP/crAPI) | API behavior and authorization checks | Planned |
| [DVWA](https://github.com/digininja/DVWA) | Controlled examples of common web weaknesses | Planned |

Use our own isolated deployments, not the projects' public demos. Pin each deployment version and keep evaluator-only answers separate from model inputs. Known challenge results are development measurements, not proof of discovering novel vulnerabilities.

## Project map

- [Product definition](docs/product.md)
- [Input, process, and output contract](docs/input-process-output.md)
- [System architecture](docs/architecture.md)
- [Model development strategy](docs/model-strategy.md)
- [Dataset specification](docs/dataset.md)
- [Evaluation plan](docs/evaluation.md)
- [Implementation roadmap](docs/roadmap.md)
- [Delivery work plan and task breakdown](docs/work-plan.md)
- [Local invoice lab](labs/invoice/README.md)
- [Local assessment engine](docs/assessment-engine.md)
- [First runtime decision](docs/decisions/0001-local-lab-runtime.md)
- [Assessment engine decision](docs/decisions/0002-local-assessment-engine.md)
- [Proposed lab catalog](benchmarks/catalog.json)
- [Finding schema](schemas/finding.schema.json)
- [Assessment request schema](schemas/assessment-request.schema.json)
- [Assessment result schema](schemas/assessment-result.schema.json)
- [Example request](examples/assessment-request.json) and [illustrative result](examples/assessment-result.json)
- [Illustrative finding](examples/finding.json)
- [Interface concept](design/security-workspace.html)

The interface concept contains fictional findings. It does not perform assessments. The separate local invoice lab and HTTP assessment engine are executable.

## Open source and paid service

The project-owned software is released under the MIT license. The intended community edition includes the scanning engine, basic dashboard, evidence, fix guidance, and report exports. A hosted service can charge for managed infrastructure, AI usage, scheduled jobs, collaboration, and support.

The software license does not grant rights to third-party model weights, datasets, lab applications, or customer data. Track their terms separately.

## First implemented milestone

The local invoice lab implements two synthetic accounts, one owned invoice, vulnerable/fixed detail access, deterministic reset, and independent controls. It binds only to loopback and exposes no reset or ground-truth HTTP endpoints. It is not an operating-system sandbox.

The HTTP assessment engine now validates authorized lab inputs, enforces exact scope and budgets, collects sanitized evidence, independently verifies the invoice scenario, and exports JSON findings and fix guidance. Run .venv/bin/python -m unittest discover -v after setup to verify the full suite.

Next: define the model observation/action contract and self-hosted inference adapter before connecting a model-driven loop. Browser automation and public-target assessment remain later work.

No model provider, cloud account, API key, or paid compute is required to run this milestone. There are currently no commands for arbitrary website scanning or model training.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Keep product features, measured capabilities, and future research clearly distinguished. Never commit credentials, private customer findings, or model checkpoints.

## Security

See [SECURITY.md](SECURITY.md) for project boundaries and vulnerability reporting.
