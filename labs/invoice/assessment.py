"""Trusted adapter: issue grants and credentials only for a live lab we started."""

import secrets
import time

from security_ai.invoice import ExpectedInvoice
from security_ai.policy import Context, Credential, LabGrant, LabRegistry


def prepare_assessment(lab, label):
    if lab.closed or len(lab.threads) != 2 or not all(t.is_alive() for t in lab.threads):
        raise RuntimeError("Assessment grants require a live controller-owned lab")
    origin = lab.urls[label]
    context = Context("local-research", "invoice-lab")
    reference = "lab-auth-" + secrets.token_hex(16)
    approved, credentials = [], {}
    for account in lab.ground_truth.accounts:
        credential_ref = "lab-credential-" + secrets.token_hex(16)
        approved.append((account.account_id, credential_ref))
        credentials[(context.tenant_id, context.project_id, credential_ref)] = Credential(
            account.account_id, account.email, account.password
        )
    grant = LabGrant(reference, context, origin, tuple(approved), time.monotonic() + 300)
    lab.register_authorization(grant.revoked)
    registry = LabRegistry([grant], credentials)
    expected = lab.ground_truth.invoice
    assertion = ExpectedInvoice(
        expected.invoice_id, expected.owner_id, tuple(expected.public_record().items())
    )
    document = {
        "schema_version": "1.0",
        "target": {"type": "web_application", "entry_url": origin},
        "authorization_ref": reference,
        "environment": "isolated_lab",
        "mode": "account_based",
        "scope": {"allowed_origins": [origin], "excluded_path_prefixes": []},
        "limits": {"max_requests": 30, "max_requests_per_second": 10,
                   "max_duration_seconds": 30, "max_model_tokens": 1000},
        "application_context": {
            "description": "Synthetic invoice application.",
            "expected_permissions": ["Customers may only read their own invoices."],
        },
        "test_accounts": [
            {"account_id": account, "role": "customer", "credential_ref": ref}
            for account, ref in approved
        ],
        "export_formats": ["json"],
    }
    return registry, context, assertion, document
