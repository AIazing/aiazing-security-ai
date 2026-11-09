"""Run a controlled assessment and export contract-valid, redacted artifacts."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import uuid

from .contracts import validate_result
from .invoice import CHECK_ID, collect, finding, verify
from .policy import AssessmentError, Budget, compile_policy
from .transport import LabTransport


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class LocalArtifacts:
    """Local developer storage, not a hosted tenant-aware evidence service."""
    def __init__(self, root):
        self.root = Path(root)

    def write(self, result, evidence):
        identifier = result["assessment_id"]
        result["artifacts"] = [
            {"format": "json", "artifact_ref": "artifact://{}/{}".format(identifier, name)}
            for name in ("report.json", "evidence.json")
        ]
        validate_result(result)
        directory = self.root / identifier
        directory.mkdir(parents=True, mode=0o700)
        for name, content in (
            ("evidence.json", {"assessment_id": identifier, "observations": evidence}),
            ("report.json", result),
        ):
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=directory, delete=False
                ) as stream:
                    temporary = Path(stream.name)
                    json.dump(content, stream, indent=2, allow_nan=False)
                    stream.write("\n")
                os.replace(str(temporary), str(directory / name))
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
        return directory / "report.json"


class AssessmentRunner:
    def __init__(self, registry, context, expected_invoice, artifacts):
        self.registry = registry
        self.context = context
        self.expected_invoice = expected_invoice
        self.artifacts = artifacts

    def run(self, document, cancellation=None, on_progress=None):
        def emit(stage, **details):
            if on_progress is not None:
                on_progress({"stage": stage, **details})

        result = {
            "schema_version": "1.0",
            "assessment_id": "assessment-" + uuid.uuid4().hex,
            "target_url": None,
            "status": "rejected",
            "started_at": None,
            "finished_at": timestamp(),
            "coverage": {"checks": [], "limitations": [
                "Controlled synthetic invoice lab only. No AI model or browser automation used.",
                "No arbitrary website discovery, production scanning, or general security guarantee.",
            ]},
            "findings": [],
            "usage": {"requests": 0, "duration_seconds": 0, "model_tokens": 0},
            "errors": [],
            "artifacts": [],
            "illustrative": False,
        }
        transport = budget = None
        evidence = []
        try:
            emit("validate")
            policy = compile_policy(document, self.context, self.registry)
            result["target_url"] = policy.grant.origin
            result["started_at"] = timestamp()
            budget = Budget(policy, cancellation)
            budget.check()
            emit("prepare")
            transport = LabTransport(policy, self.registry, budget, on_progress)
            emit("collect")
            case = collect(transport, policy.account_ids)
            emit("verify")
            outcome = verify(case, self.expected_invoice)
            budget.check()
            if outcome == "inconclusive":
                raise AssessmentError(
                    "VERIFICATION_INCONCLUSIVE",
                    "Independent controls could not establish exposure or a verified denial.",
                    "verify",
                )
            result["status"] = "completed"
            result["coverage"]["checks"] = [{
                "check_id": CHECK_ID, "status": "tested",
                "detail": (
                    "Cross-account invoice exposure verified with independent controls."
                    if outcome == "exposed" else
                    "The tested cross-account read was denied; owner and negative controls passed."
                ),
            }]
            if outcome == "exposed":
                result["findings"].append(finding(
                    case, result["assessment_id"], transport.observations, policy.grant.origin
                ))
        except AssessmentError as error:
            result["errors"].append(error.record())
            if budget is not None:
                has_evidence = transport is not None and bool(transport.observations)
                result["status"] = (
                    "cancelled" if error.code == "CANCELLED" else
                    "partial" if has_evidence else "failed"
                )
                result["coverage"]["checks"] = [{
                    "check_id": CHECK_ID,
                    "status": "inconclusive" if has_evidence else "not_run",
                    "detail": error.message,
                }]
                result["coverage"]["limitations"].append(
                    "Assessment did not finish; no conclusion should be drawn from an empty finding list."
                )
        finally:
            if transport is not None:
                evidence = transport.evidence()
                transport.close()
            if budget is not None:
                result["usage"]["requests"] = budget.requests
                result["usage"]["duration_seconds"] = round(
                    max(0, budget.clock() - budget.started), 6
                )
            result["finished_at"] = timestamp()
        emit("report")
        self.artifacts.write(result, evidence)
        emit("finished", status=result["status"], requests=result["usage"]["requests"],
             assessment_id=result["assessment_id"])
        return result
