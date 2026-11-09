"""Assess controller-owned local invoice fixtures and export real lab reports."""

import argparse
import json
from pathlib import Path

from labs.invoice.assessment import prepare_assessment
from labs.invoice.control import InvoiceLab

from .runner import AssessmentRunner, LocalArtifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", choices=("vulnerable", "fixed", "both"), default="both")
    parser.add_argument("--output", type=Path, default=Path("artifacts/assessment-demo"))
    parser.add_argument("--max-requests", type=int, default=30)
    args = parser.parse_args()
    if args.max_requests < 1:
        parser.error("--max-requests must be positive")
    summaries = []
    try:
        with InvoiceLab() as lab:
            for label in ("vulnerable", "fixed") if args.fixture == "both" else (args.fixture,):
                registry, context, expected, document = prepare_assessment(lab, label)
                document["limits"]["max_requests"] = args.max_requests
                runner = AssessmentRunner(registry, context, expected, LocalArtifacts(args.output))
                result = runner.run(document)
                summaries.append({
                    "fixture": label,
                    "status": result["status"],
                    "confirmed_findings": len(result["findings"]),
                    "requests": result["usage"]["requests"],
                    "report": str(args.output / result["assessment_id"] / "report.json"),
                })
    except (OSError, RuntimeError) as error:
        parser.exit(1, "Local assessment could not finish: {}\n".format(type(error).__name__))
    print(json.dumps(summaries, indent=2))
    return 0 if all(item["status"] == "completed" for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
