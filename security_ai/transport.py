"""Policy-gated HTTP collection for registered literal-IP lab targets."""

from dataclasses import dataclass
import http.client
import json
import re
import socket
from urllib.parse import urlsplit

from .policy import AssessmentError

MAX_RESPONSE_BYTES = 65536
SENSITIVE_KEYS = {"password", "token", "authorization", "cookie", "set-cookie",
                  "secret", "session", "email"}


class PinnedHTTPConnection(http.client.HTTPConnection):
    def connect(self):
        if self.host != "127.0.0.1" or self._tunnel_host is not None:
            raise AssessmentError("ACTION_OUT_OF_SCOPE", "Only direct loopback connections are allowed.")
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.settimeout(self.timeout)
            connection.connect(("127.0.0.1", self.port))
            self.sock = connection
        except BaseException:
            connection.close()
            raise


@dataclass(frozen=True)
class Observation:
    trace_id: str
    method: str
    path: str
    actor: str
    status: int
    body: object


class LabTransport:
    def __init__(self, policy, registry, budget, on_observation=None):
        self.policy = policy
        self.budget = budget
        self.registry = registry
        self.on_observation = on_observation
        self.observations = []
        self.tokens = {}
        self.protected = set()
        for account in policy.account_ids:
            credential = registry.credential(policy.grant, account)
            self.protected.update((credential.password, credential.email))

    def _redact(self, value, depth=0):
        if depth > 32:
            return "[omitted: nesting limit]"
        if isinstance(value, dict):
            return {
                self._redact(key, depth + 1): (
                    "[redacted]" if key.lower() in SENSITIVE_KEYS
                    else self._redact(item, depth + 1)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._redact(item, depth + 1) for item in value]
        if isinstance(value, str):
            for secret in sorted(self.protected, key=len, reverse=True):
                if secret:
                    value = value.replace(secret, "[redacted]")
        return value

    def _perform(self, method, path, actor=None, payload=None, login=False):
        url = self.policy.grant.origin + path
        self.policy.authorize(method, url, actor)
        headers = {"Content-Type": "application/json"}
        if actor is not None and not login:
            if actor not in self.tokens:
                raise AssessmentError("SESSION_UNAVAILABLE", "No approved session is available.")
            headers["Authorization"] = "Bearer " + self.tokens[actor]
        self.budget.reserve_request()
        port = urlsplit(self.policy.grant.origin).port
        connection = PinnedHTTPConnection(
            "127.0.0.1", port, timeout=min(3, self.budget.remaining)
        )
        try:
            # No hostname resolution, proxy configuration, or redirect following.
            connection.request(method, path, body=json.dumps(payload) if payload else None,
                               headers=headers)
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise AssessmentError("REDIRECT_BLOCKED", "Redirect responses are not followed.")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            self.budget.check()
            if len(raw) > MAX_RESPONSE_BYTES:
                raise AssessmentError("RESPONSE_TOO_LARGE", "Response exceeded the lab size limit.")
            if response.headers.get_content_type() != "application/json":
                raise AssessmentError("INVALID_RESPONSE", "The lab did not return a JSON response.")
            try:
                def reject_constant(value):
                    raise ValueError("Nonfinite JSON number")
                body = json.loads(raw, parse_constant=reject_constant)
            except (ValueError, UnicodeError, RecursionError):
                raise AssessmentError("INVALID_RESPONSE", "The lab returned invalid JSON.")
            if login:
                if response.status != 200 or not isinstance(body, dict):
                    raise AssessmentError("LOGIN_FAILED", "A test session could not be established.",
                                          "prepare")
                token = body.get("token")
                if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", token):
                    raise AssessmentError("INVALID_SESSION", "The lab returned an invalid session.",
                                          "prepare")
                self.tokens[actor] = token
                self.protected.add(token)
                body = {"session_established": True}
            cleaned = self._redact(body)
            observation = Observation(
                "trace-{:04d}".format(len(self.observations) + 1),
                method, path, actor or "anonymous", response.status, cleaned
            )
            self.observations.append(observation)
            if self.on_observation is not None:
                self.on_observation({
                    "stage": "collect",
                    "trace_id": observation.trace_id,
                    "method": observation.method,
                    "path": observation.path,
                    "actor": observation.actor,
                    "status": observation.status,
                    "requests": self.budget.requests,
                })
            return observation
        except (OSError, http.client.HTTPException):
            # Exception messages can include target-controlled values.
            raise AssessmentError("NETWORK_ERROR", "The approved lab request failed.",
                                  retryable=True)
        finally:
            connection.close()

    def login(self, account_id):
        credential = self.registry.credential(self.policy.grant, account_id)
        return self._perform("POST", "/api/sessions", account_id, {
            "email": credential.email, "password": credential.password
        }, login=True)

    def get(self, path, account_id=None):
        return self._perform("GET", path, account_id)

    def evidence(self):
        # Redact again with all sessions learned during this run.
        return self._redact([
            {
                "trace_id": item.trace_id,
                "request": {"method": item.method,
                            "url": self.policy.grant.origin + item.path,
                            "actor": item.actor},
                "response": {"status": item.status, "body": item.body},
            }
            for item in self.observations
        ])

    def close(self):
        self.tokens.clear()
        self.protected.clear()
