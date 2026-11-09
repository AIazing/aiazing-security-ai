"""Run independent, scripted controls against a new lab; no arbitrary target URLs."""

import argparse
import http.client
import json
from pathlib import Path

from .control import InvoiceLab


def request(server, method, path, body=None, token=None, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    headers.update(extra_headers or {})
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        connection.request(
            method, path, body=json.dumps(body) if body is not None else None,
            headers=headers,
        )
        response = connection.getresponse()
        content = response.read()
        return response.status, json.loads(content)
    finally:
        connection.close()


def verify_lab(lab):
    """Read ground truth through the controller, not through website responses."""
    truth = lab.ground_truth
    owner = next(a for a in truth.accounts if a.account_id == truth.invoice.owner_id)
    other = next(a for a in truth.accounts if a.account_id != truth.invoice.owner_id)
    records = []
    for label, server in lab.servers.items():
        tokens = {}
        for account in (owner, other):
            status, response = request(server, "POST", "/api/sessions", {
                "email": account.email, "password": account.password
            })
            if status != 200 or not isinstance(response.get("token"), str):
                raise RuntimeError("Could not establish controlled test sessions")
            tokens[account.account_id] = response["token"]
        path = "/api/invoices/" + truth.invoice.invoice_id
        expected_record = truth.invoice.public_record()
        checks = []

        def check(name, actor, status, response, expected_status, expected_body):
            checks.append({
                "check": name, "actor": actor,
                "expected_status": expected_status, "observed_status": status,
                "response": response,
                "passed": status == expected_status and response == expected_body,
            })

        status, body = request(server, "GET", path, token=tokens[owner.account_id])
        check("owner-access", owner.account_id, status, body, 200, expected_record)
        status, body = request(server, "GET", path, token=tokens[other.account_id])
        check(
            "cross-account-access", other.account_id, status, body,
            200 if label == "vulnerable" else 404,
            expected_record if label == "vulnerable" else {"error": "Not found"},
        )
        status, body = request(server, "GET", path)
        check("unauthenticated-access", "anonymous", status, body, 401,
              {"error": "Authentication required"})
        status, body = request(server, "GET", "/api/invoices/missing",
                               token=tokens[owner.account_id])
        check("missing-record", owner.account_id, status, body, 404, {"error": "Not found"})
        records.append({
            "fixture": label,
            "checks": checks,
            "passed": all(item["passed"] for item in checks),
        })
    return {
        "kind": "invoice_lab_control_results",
        "scenario": "invoice-cross-account-access",
        "fixture_version": "1",
        "synthetic": True,
        "model_used": False,
        "fixtures": records,
        "passed": all(record["passed"] for record in records),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON control-results path")
    args = parser.parse_args()
    try:
        with InvoiceLab() as lab:
            result = verify_lab(lab)
            lab.reset()
            reset_result = verify_lab(lab)
            result["reset_repeatable"] = result == reset_result
            result["passed"] = result["passed"] and result["reset_repeatable"]
    except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
        parser.exit(1, "Lab verification failed: {}\n".format(error))
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
