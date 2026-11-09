# AIazing Security AI

An open-source project to build a specialized AI model and assessment system that investigates authorized websites and APIs, verifies security findings, explains fixes, and exports reports.

**Status: project definition and interface concept. There is no trained model, live scanner, or validated benchmark result yet.**

## The intended experience

1. Supply a website URL and prove authority to test it.
2. Define permitted hosts, actions, request limits, and optional test accounts.
3. Explore the application through a browser and HTTP tools.
4. Investigate candidate vulnerabilities and verify their impact.
5. Return findings with evidence, reproduction steps, limitations, and fix guidance.
6. Export reports and retest after changes.

The initial target type is a web application or HTTP API. Repository, file, mobile, and infrastructure analysis are separate future integrations, rather than an unrestricted “anything” input.

## Our model

We aim to develop a specialized transformer model, initially by fine-tuning an existing open-weight model. We will compare it against unchanged base models and optional hosted-model baselines before claiming improvements. The base model and its redistribution terms have not been selected.

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
- [Proposed lab catalog](benchmarks/catalog.json)
- [Finding schema](schemas/finding.schema.json)
- [Assessment request schema](schemas/assessment-request.schema.json)
- [Assessment result schema](schemas/assessment-result.schema.json)
- [Example request](examples/assessment-request.json) and [illustrative result](examples/assessment-result.json)
- [Illustrative finding](examples/finding.json)
- [Interface concept](design/security-workspace.html)

The interface concept contains fictional findings. It does not perform assessments.

## Open source and paid service

The project-owned software is released under the MIT license. The intended community edition includes the scanning engine, basic dashboard, evidence, fix guidance, and report exports. A hosted service can charge for managed infrastructure, AI usage, scheduled jobs, collaboration, and support.

The software license does not grant rights to third-party model weights, datasets, lab applications, or customer data. Track their terms separately.

## First milestone

Build one isolated lab, implement an evidence collector and an independent verifier for one access-control scenario, then export a structured finding. Establish this baseline before training a specialized model.

No model provider, cloud account, API key, or paid compute is required to review this repository. There are currently no commands for live scanning or training.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Keep product features, measured capabilities, and future research clearly distinguished. Never commit credentials, private customer findings, or model checkpoints.

## Security

See [SECURITY.md](SECURITY.md) for project boundaries and vulnerability reporting.
