import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from security_ai.dashboard import Dashboard, DashboardServer


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.dashboard = Dashboard(self.directory.name)
        self.server = DashboardServer(0, self.dashboard)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.dashboard.close()
        self.directory.cleanup()

    def call(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(
                method, path, body=None if body is None else json.dumps(body),
                headers=headers or {},
            )
            response = connection.getresponse()
            content = response.read()
            value = json.loads(content) if response.headers.get_content_type() == "application/json" else content
            return response.status, value, dict(response.headers)
        finally:
            connection.close()

    def mutation_headers(self):
        return {
            "Content-Type": "application/json", "Origin": self.server.origin,
            "X-Dashboard-Token": self.dashboard.token,
        }

    def start(self, fixture="vulnerable", limit=30):
        status, body, _ = self.call("POST", "/api/jobs",
                                    {"fixture": fixture, "max_requests": limit},
                                    self.mutation_headers())
        self.assertEqual(status, 202)
        return body["job_id"]

    def wait(self, identifier):
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            state = self.dashboard.snapshot()
            job = next(item for item in state["jobs"] if item["id"] == identifier)
            if job["status"] != "running":
                return job
            time.sleep(0.02)
        self.fail("Dashboard assessment did not finish")

    def test_assets_and_status_are_available_only_on_loopback(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        for route in ("/", "/app.css", "/app.js"):
            status, body, headers = self.call("GET", route)
            self.assertEqual(status, 200)
            self.assertGreater(len(body), 100)
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
        status, state, _ = self.call("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(len(state["project"]["phases"]), 6)
        self.assertEqual(state["jobs"], [])
        self.assertIn("AI inference", state["project"]["summary"])

    def test_cross_origin_and_wrong_host_cannot_read_state(self):
        for headers, expected in (
            ({"Origin": "https://attacker.example"}, 403),
            ({"Host": "attacker.example"}, 421),
            ({"Sec-Fetch-Site": "cross-site"}, 403),
        ):
            status, body, _ = self.call("GET", "/api/state", headers=headers)
            self.assertEqual(status, expected)
            self.assertNotIn("csrf_token", body)

    def test_mutations_require_both_exact_origin_and_token(self):
        good = self.mutation_headers()
        for headers in (
            {"Content-Type": "application/json"},
            {key: value for key, value in good.items() if key != "Origin"},
            {key: value for key, value in good.items() if key != "X-Dashboard-Token"},
            {**good, "X-Dashboard-Token": "wrong"},
            {**good, "X-Dashboard-Token": "é"},
        ):
            status, _, _ = self.call("POST", "/api/jobs",
                                     {"fixture": "both", "max_requests": 30}, headers)
            self.assertEqual(status, 403)
        self.assertEqual(self.dashboard.snapshot()["jobs"], [])

    def test_invalid_job_settings_cannot_create_arbitrary_scans(self):
        for body in (
            {"fixture": "https://example.com", "max_requests": 30},
            {"fixture": "both", "max_requests": True},
            {"fixture": "both", "max_requests": 0},
            {"fixture": "both", "max_requests": 101},
            {"fixture": "both", "max_requests": 30, "url": "http://169.254.169.254"},
        ):
            self.assertEqual(self.call("POST", "/api/jobs", body,
                                       self.mutation_headers())[0], 400)
        self.assertEqual(self.dashboard.snapshot()["jobs"], [])

    def test_one_active_job_and_cancellation(self):
        identifier = self.start("both")
        self.assertEqual(self.call("POST", "/api/jobs", {"fixture": "fixed", "max_requests": 30},
                                   self.mutation_headers())[0], 409)
        self.assertEqual(self.call("POST", "/api/jobs/" + identifier + "/cancel", {},
                                   self.mutation_headers())[0], 202)
        job = self.wait(identifier)
        self.assertEqual(job["status"], "cancelled")
        self.assertIsNone(self.dashboard.snapshot()["active_job"])

    def test_completed_comparison_exports_real_results_and_safe_events(self):
        job = self.wait(self.start("both"))
        self.assertEqual(job["status"], "completed")
        self.assertEqual([item["findings"] for item in job["runs"]], [1, 0])
        self.assertEqual([item["requests"] for item in job["runs"]], [10, 10])
        self.assertEqual(len([e for e in job["events"] if "method" in e]), 20)
        self.assertTrue({"validate", "collect", "verify", "report", "finished"}
                        <= {e["stage"] for e in job["events"]})
        serialized = json.dumps(job)
        self.assertNotIn("lab-customer-", serialized)
        self.assertNotIn("customer-a@example.test", serialized)
        for event in job["events"]:
            self.assertNotIn("body", event)
            self.assertNotIn("headers", event)
        self.assertEqual(len(self.dashboard.snapshot()["reports"]), 2)
        for run in job["runs"]:
            status, report, headers = self.call(
                "GET", "/api/reports/" + run["assessment_id"] + "/report/download"
            )
            self.assertEqual(status, 200)
            self.assertTrue(headers["Content-Disposition"].startswith("attachment;"))
            self.assertEqual(report["assessment_id"], run["assessment_id"])
            status, evidence, _ = self.call(
                "GET", "/api/reports/" + run["assessment_id"] + "/evidence"
            )
            self.assertEqual(status, 200)
            self.assertEqual(len(evidence["observations"]), 10)

    def test_partial_run_keeps_errors_and_incomplete_coverage(self):
        job = self.wait(self.start(limit=1))
        self.assertEqual(job["status"], "partial")
        identifier = job["runs"][0]["assessment_id"]
        report = self.dashboard.read(identifier, "report")
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["errors"][0]["code"], "REQUEST_BUDGET_EXHAUSTED")

    def test_saved_reports_survive_dashboard_restart(self):
        job = self.wait(self.start(limit=1))
        second = Dashboard(self.directory.name)
        self.addCleanup(second.close)
        self.assertEqual(second.snapshot()["jobs"], [])
        self.assertEqual(second.reports()[0]["assessment_id"], job["runs"][0]["assessment_id"])

    def test_paths_and_symlinks_cannot_escape_report_root(self):
        for path in ("/api/reports/../../README.md/report",
                     "/api/reports/%2e%2e/report",
                     "/api/reports/not-an-id/report", "/seed.py"):
            self.assertEqual(self.call("GET", path)[0], 404)
        identifier = "assessment-" + "0" * 32
        with tempfile.TemporaryDirectory() as other:
            (Path(self.directory.name) / identifier).symlink_to(other, target_is_directory=True)
            self.assertEqual(self.call("GET", "/api/reports/" + identifier + "/report")[0], 404)
            self.assertEqual(self.dashboard.reports(), [])

    def test_unexpected_worker_failure_is_visible_without_raw_exception(self):
        with patch("security_ai.dashboard.InvoiceLab", side_effect=RuntimeError("secret-value")):
            job = self.wait(self.start())
        self.assertEqual(job["status"], "failed")
        self.assertNotIn("secret-value", json.dumps(job))
        self.assertTrue(any(e["stage"] == "error" for e in job["events"]))


if __name__ == "__main__":
    unittest.main()
