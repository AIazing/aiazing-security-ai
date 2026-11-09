"""Scripted collection and independent verification for one lab scenario."""

from dataclasses import dataclass
import re

from .policy import AssessmentError

CHECK_ID = "invoice-cross-account-access"


@dataclass(frozen=True)
class ExpectedInvoice:
    """Evaluator-only assertion. Never supply this to a future model."""
    invoice_id: str
    owner_id: str
    record_items: tuple

    @property
    def record(self):
        return dict(self.record_items)


@dataclass
class InvoiceCase:
    identities: dict
    lists: dict
    selected_account: str
    invoice_id: str
    owner_read: object
    other_read: object
    anonymous_read: object
    missing_read: object


def collect(transport, accounts):
    identities, lists = {}, {}
    for account in accounts:
        transport.login(account)
        identities[account] = transport.get("/api/me", account)
        lists[account] = transport.get("/api/invoices", account)
    # Select from observed account listings, not evaluator labels or fixture mode.
    selected = None
    for account, observation in lists.items():
        body = observation.body
        if observation.status != 200 or not isinstance(body, dict):
            continue
        rows = body.get("invoices")
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            identifier = rows[0].get("id")
            if isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier):
                selected = (account, identifier)
                break
    if selected is None:
        raise AssessmentError("VERIFICATION_INCONCLUSIVE",
                              "No supported invoice could be selected from account observations.",
                              "verify")
    account, identifier = selected
    other = next(value for value in accounts if value != account)
    path = "/api/invoices/" + identifier
    return InvoiceCase(
        identities, lists, account, identifier,
        transport.get(path, account),
        transport.get(path, other),
        transport.get(path),
        transport.get("/api/invoices/invoice-missing-control", account),
    )


def verify(case, expected):
    """Return exposure only after independently checking identity and controls."""
    if case.invoice_id != expected.invoice_id or case.selected_account != expected.owner_id:
        return "inconclusive"
    if any(item.status != 200 or not isinstance(item.body, dict)
           or item.body.get("id") != account for account, item in case.identities.items()):
        return "inconclusive"
    for account, item in case.lists.items():
        wanted = [expected.record] if account == expected.owner_id else []
        if item.status != 200 or item.body != {"invoices": wanted}:
            return "inconclusive"
    if (
        case.owner_read.status != 200 or case.owner_read.body != expected.record
        or case.anonymous_read.status != 401
        or case.anonymous_read.body != {"error": "Authentication required"}
        or case.missing_read.status != 404 or case.missing_read.body != {"error": "Not found"}
    ):
        return "inconclusive"
    # Returning the exact record is exposure even if the server labels it 403/404.
    if case.other_read.body == expected.record:
        return "exposed"
    if case.other_read.status in (403, 404) and case.other_read.body in (
        {"error": "Not found"}, {"error": "Forbidden"}
    ):
        return "denied"
    return "inconclusive"


def finding(case, assessment_id, observations, origin):
    evidence = []
    for item, description in (
        (case.owner_read, "The legitimate owner received the independently known synthetic record."),
        (case.other_read, "The other test account received the same record."),
        (case.anonymous_read, "The unauthenticated control was denied without record data."),
        (case.missing_read, "The nonexistent-record control returned no invoice."),
    ):
        index = next(i for i, observation in enumerate(observations)
                     if observation.trace_id == item.trace_id)
        evidence.append({
            "description": description,
            "artifact_ref": "artifact://{}/evidence.json#/observations/{}".format(
                assessment_id, index),
            "redacted": True,
        })
    return {
        "id": assessment_id + "-001",
        "title": "Customer can access another customer's invoice",
        "target_url": origin + case.other_read.path,
        "severity": "high",
        "verification": "confirmed",
        "expected_behavior": "Only the invoice owner or an explicitly authorized role can read it.",
        "observed_behavior": (
            "The non-owner test account received the owner's exact synthetic invoice. "
            "Identity, legitimate-owner, anonymous, and missing-record controls were checked."
        ),
        "evidence": evidence,
        "reproduction_steps": [
            "Establish separate approved sessions for the two supplied customer accounts.",
            "List each customer's invoices and identify the owner's synthetic record.",
            "Read the record as its owner, then request it using the other customer's session.",
            "Compare the returned record with independent ownership and response-content controls.",
        ],
        "recommendation": (
            "Enforce object ownership on the server using the authenticated customer identity "
            "before returning an invoice. Deny cross-account reads without returning record data. "
            "Retest non-owner denial, owner access, anonymous denial, and relevant identifier "
            "variations. This is implementation guidance, not a generated code patch."
        ),
        "limitations": [
            "Confirmed in a synthetic controlled lab only; no model was used.",
            "Only this invoice-detail access-control scenario was assessed.",
        ],
        "retest": "not_run",
        "illustrative": False,
    }
