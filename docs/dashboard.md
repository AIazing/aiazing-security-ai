# Local research dashboard

The working dashboard shows current assessment activity, saved findings/evidence, and repository-maintained project progress. It is separate from the earlier interface concept and the synthetic invoice application's own page.

## Start

After the [assessment setup](assessment-engine.md):

~~~sh
.venv/bin/python -m security_ai.dashboard
~~~

Open http://127.0.0.1:8767 in your browser. Use the numeric loopback URL printed by the command; the Host check intentionally does not accept other hostnames.

If the port is occupied:

~~~sh
.venv/bin/python -m security_ai.dashboard --port 8768
~~~

Ctrl-C stops the dashboard and requests cancellation of its active assessment. The dashboard does not need an external AI API or a model to run.

## What you can see and do

- Choose the vulnerable lab, fixed lab, or a comparison.
- Start a real assessment and watch authorization, request collection, independent verification, and export events.
- Stop the active run.
- Review saved results, severity, verification status, sanitized requests/responses, fix guidance, coverage, and limitations.
- Download actual report/evidence JSON.
- View the six project phases and the next planned increment.

The form selects controller-owned fixtures; there is deliberately no arbitrary-domain scan field yet.

Stage markers indicate stages reached, not a fabricated completion percentage. Failed, cancelled, and partial assessments retain their own statuses. The findings panel explicitly warns that an incomplete run is not a clean scan.

## Current project status

The lab and HTTP assessment slice work. The local web preview now works. The base model, inference adapter, training, and hosted pilot are not implemented.

The roadmap comes from project-status.json in this repository, aligned with [the delivery plan](work-plan.md). It is maintained alongside code; it is not inferred automatically from tests, GitHub issues, elapsed time, or an AI model.

## Persistence

By default, reports are read/written under artifacts/assessment-demo, shared with the CLI's default output. Existing valid CLI results appear in the dashboard. The most recent 30 reports from up to 200 recent assessment directories are shown.

Report JSON and evidence survive a restart. Live jobs, fixture labels, and activity events are kept in memory for the current dashboard session; imported reports use a generic assessment label. Artifacts are ignored by Git.

Use --output to select a different local report root:

~~~sh
.venv/bin/python -m security_ai.dashboard --output artifacts/my-dashboard
~~~

## Local boundaries

The dashboard binds to 127.0.0.1 only. It validates Host and browser origin, requires a per-process token for mutation requests, blocks cross-site browser reads, uses same-origin assets, and allows one active job. It accepts only fixed fixture choices and bounded request limits. Download routes accept registered-format assessment IDs, not filesystem paths, and reject symlinked report paths.

This remains a trusted-machine research tool. The token/origin checks are not customer authentication or tenant isolation. Local processes can access the service; do not expose it through a tunnel or public reverse proxy. Report storage is not encrypted hosted storage.

The assessment engine's existing cooperative cancellation and network-timeout limits still apply. The UI does not make them stronger or connect an AI model.

## Verification

Backend and engine tests:

~~~sh
.venv/bin/python -m unittest discover -v
~~~

Optional real-browser checks:

~~~sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m tests.browser_dashboard
~~~

The browser check uses an isolated headless Chrome profile on macOS when Google Chrome is installed. Otherwise install Playwright's Chromium with .venv/bin/python -m playwright install chromium before running it.

It starts its own temporary dashboard/lab, verifies comparison results, evidence/fix/coverage tabs, JSON download, 390px/320px layouts, incomplete results, cancellation, and JavaScript exceptions. Screenshots and the downloaded JSON go to the ignored artifacts/dashboard-preview directory.
