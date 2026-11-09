"""A loopback-only fixture with a single switchable ownership check."""

import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .seed import SEED

HOST = "127.0.0.1"
MAX_BODY = 4096


class Store:
    def __init__(self, vulnerable: bool):
        self.vulnerable = vulnerable
        self.lock = threading.RLock()
        self.reset()

    def reset(self):
        with self.lock:
            self.accounts = {a.account_id: a for a in SEED.accounts}
            self.invoices = {SEED.invoice.invoice_id: SEED.invoice}
            self.sessions = {}

    def login(self, email, password):
        with self.lock:
            for account in self.accounts.values():
                if account.email == email and hmac.compare_digest(
                    account.password.encode(), password.encode()
                ):
                    token = secrets.token_urlsafe(32)
                    self.sessions[token] = account.account_id
                    return token
        return None


class LabServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, port: int, vulnerable: bool):
        self.store = Store(vulnerable)
        super().__init__((HOST, port), Handler)

    def verify_request(self, request, client_address):
        return client_address[0] == HOST


class Handler(BaseHTTPRequestHandler):
    server_version = "InvoiceLab"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(3)

    def log_message(self, format, *args):
        # Avoid recording URLs, credentials, sessions, or response contents.
        pass

    def _reply(self, status, body, content_type="application/json"):
        payload = json.dumps(body).encode() if content_type == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(payload)

    def _destination_allowed(self):
        expected = "{}:{}".format(HOST, self.server.server_port)
        if self.headers.get_all("Host", []) != [expected]:
            self._reply(421, {"error": "Unrecognized host"})
            return False
        # Reject cross-origin browser requests, including form POSTs to login.
        origin = self.headers.get("Origin")
        if origin is not None and origin != "http://" + expected:
            self._reply(403, {"error": "Origin not allowed"})
            return False
        try:
            target = urlsplit(self.path)
        except ValueError:
            self._reply(400, {"error": "Unsupported request target"})
            return False
        if target.scheme or target.netloc or target.query or target.fragment:
            self._reply(400, {"error": "Unsupported request target"})
            return False
        return True

    def _session(self):
        value = self.headers.get("Authorization", "")
        if not value.startswith("Bearer "):
            return None, None
        token = value[len("Bearer "):]
        return token, self.server.store.sessions.get(token)

    def do_GET(self):
        if not self._destination_allowed():
            return
        if self.path in ("/", "/app.js"):
            name = "page.html" if self.path == "/" else "app.js"
            kind = "text/html; charset=utf-8" if self.path == "/" else "text/javascript"
            self._reply(200, Path(__file__).with_name(name).read_bytes(), kind)
            return
        if self.path == "/health":
            self._reply(200, {"status": "ok"})
            return
        if self.path not in ("/api/me", "/api/invoices") and not self.path.startswith(
            "/api/invoices/"
        ):
            self._reply(404, {"error": "Not found"})
            return
        store = self.server.store
        with store.lock:
            _, account_id = self._session()
            if account_id is None:
                self._reply(401, {"error": "Authentication required"})
                return
            if self.path == "/api/me":
                account = store.accounts[account_id]
                self._reply(200, {"id": account.account_id, "email": account.email})
            elif self.path == "/api/invoices":
                self._reply(200, {"invoices": [
                    item.public_record() for item in store.invoices.values()
                    if item.owner_id == account_id
                ]})
            else:
                item = store.invoices.get(self.path[len("/api/invoices/"):])
                # Deliberate lab vulnerability: missing object ownership check.
                if item is None or (not store.vulnerable and item.owner_id != account_id):
                    self._reply(404, {"error": "Not found"})
                else:
                    self._reply(200, item.public_record())

    def do_POST(self):
        if not self._destination_allowed():
            return
        if self.path not in ("/api/sessions", "/api/logout"):
            self._reply(404, {"error": "Not found"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None:
            self._reply(400, {"error": "A single content length is required"})
            return
        try:
            length = int(lengths[0])
        except ValueError:
            self._reply(400, {"error": "Invalid content length"})
            return
        if length < 0 or length > MAX_BODY:
            self._reply(413, {"error": "Request too large"})
            return
        content = self.rfile.read(length)
        if len(content) != length:
            self._reply(400, {"error": "Incomplete request"})
            return
        if self.path == "/api/logout":
            with self.server.store.lock:
                token, _ = self._session()
                self.server.store.sessions.pop(token, None)
            self._reply(200, {"status": "signed_out"})
            return
        if self.headers.get_content_type() != "application/json":
            self._reply(415, {"error": "JSON required"})
            return
        try:
            data = json.loads(content)
        except (ValueError, UnicodeError):
            self._reply(400, {"error": "Invalid JSON"})
            return
        if (
            not isinstance(data, dict)
            or set(data) != {"email", "password"}
            or not all(isinstance(value, str) for value in data.values())
        ):
            self._reply(400, {"error": "Email and password strings required"})
            return
        token = self.server.store.login(data["email"], data["password"])
        if token is None:
            self._reply(401, {"error": "Invalid credentials"})
        else:
            self._reply(200, {"token": token})
