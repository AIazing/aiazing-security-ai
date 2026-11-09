import http.client
import json
import socket
import unittest
from unittest.mock import patch

from labs.invoice.control import InvoiceLab
from labs.invoice.verify import request, verify_lab


class InvoiceLabTests(unittest.TestCase):
    def setUp(self):
        self.lab = InvoiceLab().start()
        self.addCleanup(self.lab.close)
        self.truth = self.lab.ground_truth

    def login(self, label, account_index):
        account = self.truth.accounts[account_index]
        status, body = request(self.lab.servers[label], "POST", "/api/sessions", {
            "email": account.email, "password": account.password
        })
        self.assertEqual(status, 200)
        return body["token"]

    def test_positive_safe_and_functional_controls(self):
        result = verify_lab(self.lab)
        self.assertTrue(result["passed"])
        outcomes = {
            fixture["fixture"]: {
                check["check"]: check["observed_status"] for check in fixture["checks"]
            }
            for fixture in result["fixtures"]
        }
        self.assertEqual(outcomes["vulnerable"]["cross-account-access"], 200)
        self.assertEqual(outcomes["fixed"]["cross-account-access"], 404)
        for checks in outcomes.values():
            self.assertEqual(checks["owner-access"], 200)
            self.assertEqual(checks["unauthenticated-access"], 401)
            self.assertEqual(checks["missing-record"], 404)

    def test_status_code_without_record_evidence_does_not_pass(self):
        original = request

        def wrong_record(server, method, path, *args, **kwargs):
            status, body = original(server, method, path, *args, **kwargs)
            if method == "GET" and status == 200 and path.startswith("/api/invoices/"):
                return status, {"id": "different-record"}
            return status, body

        with patch("labs.invoice.verify.request", side_effect=wrong_record):
            self.assertFalse(verify_lab(self.lab)["passed"])

    def test_anonymous_and_invalid_sessions_cannot_read_data(self):
        for server in self.lab.servers.values():
            for path in ("/api/me", "/api/invoices", "/api/invoices/invoice-b-001"):
                for token in (None, "invalid-session"):
                    with self.subTest(path=path, token=token):
                        status, _ = request(server, "GET", path, token=token)
                        self.assertEqual(status, 401)

    def test_invoice_list_is_scoped_in_both_versions(self):
        for label, server in self.lab.servers.items():
            for index, expected in ((0, []), (1, [self.truth.invoice.public_record()])):
                status, body = request(server, "GET", "/api/invoices",
                                       token=self.login(label, index))
                self.assertEqual((status, body), (200, {"invoices": expected}))

    def test_sessions_cannot_cross_fixture_boundary(self):
        token = self.login("vulnerable", 1)
        self.assertEqual(request(self.lab.servers["fixed"], "GET", "/api/me",
                                 token=token)[0], 401)

    def test_reset_restores_seed_and_revokes_sessions(self):
        token = self.login("fixed", 1)
        server = self.lab.servers["fixed"]
        with server.store.lock:
            server.store.invoices.clear()
        self.lab.reset()
        self.assertEqual(request(server, "GET", "/api/me", token=token)[0], 401)
        new_token = self.login("fixed", 1)
        self.assertNotEqual(token, new_token)
        status, body = request(server, "GET", "/api/invoices/invoice-b-001",
                               token=new_token)
        self.assertEqual((status, body), (200, self.truth.invoice.public_record()))

    def test_controls_are_repeatable_after_reset(self):
        before = verify_lab(self.lab)
        for _ in range(2):
            self.lab.reset()
            self.assertEqual(before, verify_lab(self.lab))

    def test_logout_revokes_the_token(self):
        token = self.login("fixed", 1)
        server = self.lab.servers["fixed"]
        self.assertEqual(request(server, "POST", "/api/logout", token=token)[0], 200)
        self.assertEqual(request(server, "GET", "/api/me", token=token)[0], 401)

    def test_bad_credentials_and_invalid_login_shapes(self):
        server = self.lab.servers["fixed"]
        for body, expected in (
            ({"email": "unknown@example.test", "password": "wrong"}, 401),
            ({"email": self.truth.accounts[0].email, "password": "wrong"}, 401),
            ({"email": self.truth.accounts[0].email, "password": []}, 400),
            ([], 400),
            ({"email": "x", "password": "y", "extra": "z"}, 400),
        ):
            self.assertEqual(request(server, "POST", "/api/sessions", body)[0], expected)

    def test_oversized_body_and_wrong_content_type_are_rejected(self):
        server = self.lab.servers["fixed"]
        self.assertEqual(request(server, "POST", "/api/sessions",
                                 {"email": "x", "password": "x" * 5000})[0], 413)
        self.assertEqual(request(server, "POST", "/api/sessions",
                                 {"email": "x", "password": "y"},
                                 extra_headers={"Content-Type": "text/plain"})[0], 415)

    def test_host_and_browser_origin_boundaries(self):
        server = self.lab.servers["fixed"]
        self.assertEqual(request(server, "GET", "/health",
                                 extra_headers={"Host": "attacker.example"})[0], 421)
        self.assertEqual(request(server, "POST", "/api/sessions",
                                 {"email": "x", "password": "y"},
                                 extra_headers={"Origin": "https://attacker.example"})[0], 403)

    def test_no_evaluator_or_reset_http_endpoints(self):
        for server in self.lab.servers.values():
            for path in ("/reset", "/ground-truth", "/api/reset", "/api/ground-truth",
                         "/seed.py", "/control.py"):
                self.assertEqual(request(server, "GET", path)[0], 404)
            self.assertEqual(request(server, "POST", "/api/reset", {})[0], 404)

    def test_browser_assets_are_identical_and_restricted_to_same_origin(self):
        content = {}
        for label, server in self.lab.servers.items():
            content[label] = {}
            for path in ("/", "/app.js"):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
                try:
                    connection.request("GET", path)
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.getheader("Cache-Control"), "no-store")
                    self.assertIn("connect-src 'self'",
                                  response.getheader("Content-Security-Policy"))
                    content[label][path] = response.read()
                finally:
                    connection.close()
        self.assertEqual(content["vulnerable"], content["fixed"])
        self.assertIn(b'<script src="/app.js">', content["fixed"]["/"])

    def test_only_loopback_listeners_and_released_ports(self):
        for server in self.lab.servers.values():
            self.assertEqual(server.server_address[0], "127.0.0.1")
        ports = [server.server_port for server in self.lab.servers.values()]
        self.lab.close()
        self.lab.close()
        for port in ports:
            with self.assertRaises(OSError):
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    pass
        self.assertTrue(all(not thread.is_alive() for thread in self.lab.threads))

    def test_control_artifacts_exclude_credentials_and_ground_truth_metadata(self):
        serialized = json.dumps(verify_lab(self.lab))
        for account in self.truth.accounts:
            self.assertNotIn(account.password, serialized)
        for server in self.lab.servers.values():
            for token in server.store.sessions:
                self.assertNotIn(token, serialized)
        status, body = request(self.lab.servers["fixed"], "GET",
                               "/api/invoices/invoice-b-001",
                               token=self.login("fixed", 1))
        self.assertEqual(status, 200)
        self.assertNotIn("owner_id", body)
        self.assertNotIn("vulnerable", body)


if __name__ == "__main__":
    unittest.main()
