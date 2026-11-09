# Product definition

## Customer and problem

Initial users are developers and small security teams responsible for web applications. They need to establish which outside-facing findings are real, understand their impact, and give engineers actionable fixes.

The product evaluates application behavior, including interactions between users and roles. Source analysis may supplement it later.

The [input, process, and output contract](input-process-output.md) specifies the customer request, execution stages, model responsibilities, and final result, including failed and rejected assessments.

## Assessment flow

Project creation → domain ownership/authorization verification → scope configuration → discovery → investigation → verification → report → retest.

Domain control does not automatically authorize testing third-party services embedded in a site. Explicitly enumerate permitted origins. For local labs, use a separate lab policy instead of internet domain verification.

Public assessments inspect permitted unauthenticated pages. Account-based assessments use supplied synthetic accounts and documented role/ownership expectations.

## Screens

1. Projects: domain, last assessment, unresolved findings, coverage.
2. Setup: ownership verification, allowed origins, limits, optional accounts.
3. Assessment: current stage, tested areas, exclusions, failures, stop action.
4. Findings: severity and verification status, with evidence and recommended fixes.
5. Reports: summary, scope, limitations, technical evidence, retest outcomes.
6. Settings: credentials, retention, team access, billing for hosted use.

## Finding lifecycle

Candidate → needs review or confirmed → fix proposed → retest pending → resolved, still reproducible, or inconclusive.

Severity describes impact. Verification describes evidence. They are independent.

An observation such as an absent security header must not be promoted to a confirmed exploitable vulnerability without evidence of an actual security violation.

## Reports

JSON is the first machine-readable output. Human-readable HTML/PDF follows.

Include affected URL and version context, expected and observed behavior, sanitized evidence, reproduction steps, impact, fix guidance, coverage limitations, and retest status.

Fix guidance can be behavioral or configuration-specific. Exact code changes require sufficient source context. A successful retest covers only the tested behavior and variations.

## Initial exclusions

No autonomous production modification, payment/refund execution, destructive testing, broad network scanning, or promise to find every vulnerability. Public bug-bounty submissions are outside the initial workflow.
