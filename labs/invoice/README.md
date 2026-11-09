# Invoice access-control lab

This is the first executable research fixture. It contains synthetic data and an intentional authorization flaw. It is not the security AI model or a general website scanner.

## Run

From the repository root, using Python 3.9 or later:

~~~sh
python3 -m labs.invoice
~~~

Open the printed URLs in a browser. Defaults:

- Vulnerable fixture: http://127.0.0.1:8765
- Fixed fixture: http://127.0.0.1:8766

If these ports are occupied, select available ports automatically:

~~~sh
python3 -m labs.invoice --vulnerable-port 0 --fixed-port 0
~~~

Only numeric loopback URLs are accepted by the Host check. There is intentionally no public bind option.

## Synthetic accounts

| Account | Email | Password |
| --- | --- | --- |
| Customer A | customer-a@example.test | lab-customer-a |
| Customer B | customer-b@example.test | lab-customer-b |

Customer B owns invoice-b-001: a USD 125.00 synthetic monthly-service invoice. Customer A owns no invoices.

Both instances require login. The invoice list always returns only the signed-in customer's records. In the vulnerable instance, the detail endpoint fails to check ownership; the fixed instance denies cross-account reads without returning invoice contents.

The browser keeps its token in memory only. Refreshing the page signs out the visible session. Sign out revokes that token on the server.

## Expected controls

| Request | Vulnerable | Fixed |
| --- | --- | --- |
| Owner reads invoice | 200 with the exact synthetic record | Same |
| Other customer reads invoice | 200 with the exact synthetic record | 404, no record |
| Anonymous reads invoice | 401, no record | Same |
| Signed-in customer reads missing invoice | 404 | Same |

Evaluator ground truth comes from seed.py through the controller, not an HTTP endpoint. Do not feed evaluator files, variant labels, or this answer-bearing README to a model during evaluation.

## Verify and retain evidence

~~~sh
python3 -m labs.invoice.verify --output artifacts/invoice-lab-controls.json
~~~

This command manages its own temporary-port instances. It does not contact arbitrary targets or evaluate instances from a separate interactive session. It checks response content as well as status, repeats after reset, and exits nonzero on failure.

The output is evaluator-side lab-control evidence, not a complete assessment report or model performance measurement. It contains synthetic invoice data and account handles but no session tokens or passwords. Artifacts are ignored by Git.

Run integration tests:

~~~sh
python3 -m unittest discover -v
~~~

## Reset and stop

In the terminal running the interactive lab:

- reset restores the original accounts/records and invalidates sessions in both instances.
- quit or Ctrl-C closes both servers.
- End-of-input also stops the lab.

Reset only between assessment runs, not while requests are active. Restarting the command also restores a fresh seed.

## Boundary

The fixture binds only to 127.0.0.1, rejects unrecognized Host and cross-origin browser requests, serves no external resources, and initiates no outbound connections. State lives in memory; no local database or real customer data is used.

This is local development isolation, not a container or operating-system sandbox. Other local processes can connect. Do not publish, tunnel, or reverse-proxy the vulnerable instance to the internet. Worker/tenant isolation and the assessment policy engine belong to later work.
