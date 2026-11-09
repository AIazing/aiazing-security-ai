# Dataset specification

## Record contents

Each reviewed episode should contain:

- Stable episode ID, source/provenance, applicable license, and collection permission.
- Application family, immutable version/image digest, scenario family, and split.
- Scope policy, role descriptions, expected permissions, and fixture seed.
- Ordered browser/HTTP observations and tool actions with redacted artifacts.
- Candidate finding, independent verifier result, expected result, and reviewer decision.
- Recommended remediation, fixed version when available, and retest evidence.
- Model/provider revision, prompt version, tool version, and collection date.

Store credentials outside records. Reference artifacts by access-controlled identifier.

## Ground truth

A finding is not ground truth because a model wrote it. Ground truth comes from a reviewed scenario with an independently established security expectation and observed result.

Public advisories can seed scenarios, but a CVE match does not prove that an arbitrary URL is vulnerable. Version, configuration, reachability, and observed impact matter.

## Sources and review

Start with project-authored fixtures and isolated deployments of known-vulnerable applications. Record rights for each source before redistributing text, traces, patches, or derived examples.

No automatic harvesting of private reports or unreviewed model-generated claims.

## Data splits

Keep training, development, and final evaluation manifests separate. Group related applications, code forks, fixed/vulnerable pairs, and generated variations to avoid leakage.

Public lab tasks can already be present in a base model's pretraining corpus. Report this limitation and introduce private, independently reviewed variations and unseen applications.

## Export

The first finding contract is [finding.schema.json](../schemas/finding.schema.json). It describes report output, not the full episode dataset. An illustrative record is in [examples/finding.json](../examples/finding.json).
