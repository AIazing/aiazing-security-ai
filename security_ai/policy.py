"""Trusted lab authorization and per-action policy; no model can issue grants."""

from dataclasses import dataclass, field
import math
import re
import threading
import time
from types import MappingProxyType
from urllib.parse import urlsplit

from .contracts import valid


class AssessmentError(Exception):
    def __init__(self, code, message, stage="execute", retryable=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.stage = stage
        self.retryable = retryable

    def record(self):
        return {"code": self.code, "message": self.message, "stage": self.stage,
                "retryable": self.retryable}


def reject(code, message):
    raise AssessmentError(code, message, stage="validate")


def parse_url(value):
    if not isinstance(value, str) or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise ValueError("Invalid URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
        or parsed.username is not None or parsed.password is not None
        or parsed.port is None or not 1 <= parsed.port <= 65535
        or parsed.query or parsed.fragment
    ):
        raise ValueError("Unsupported URL")
    origin = "http://127.0.0.1:{}".format(parsed.port)
    path = parsed.path or "/"
    if value != origin + (parsed.path or "") or "%" in path or "//" in path:
        raise ValueError("Noncanonical URL")
    return origin, path


@dataclass(frozen=True)
class Context:
    tenant_id: str
    project_id: str


@dataclass(frozen=True)
class Credential:
    account_id: str
    email: str
    password: str


@dataclass(frozen=True)
class LabGrant:
    reference: str
    context: Context
    origin: str
    # Account handle -> credential reference. The broker holds actual credentials.
    accounts: tuple
    expires_at: float
    revoked: threading.Event = field(default_factory=threading.Event, compare=False)

    def check_active(self):
        if self.revoked.is_set() or time.monotonic() >= self.expires_at:
            raise AssessmentError(
                "AUTHORIZATION_INACTIVE", "Lab authorization expired or was revoked."
            )


class LabRegistry:
    def __init__(self, grants, credentials):
        self.grants = MappingProxyType({grant.reference: grant for grant in grants})
        self.credentials = MappingProxyType(dict(credentials))

    def resolve(self, reference, context):
        grant = self.grants.get(reference)
        if grant is None or grant.context != context:
            reject("AUTHORIZATION_NOT_FOUND", "No authorization exists for this project.")
        try:
            grant.check_active()
        except AssessmentError:
            reject("AUTHORIZATION_INACTIVE", "Lab authorization expired or was revoked.")
        return grant

    def credential(self, grant, account_id):
        reference = dict(grant.accounts).get(account_id)
        key = (grant.context.tenant_id, grant.context.project_id, reference)
        credential = self.credentials.get(key)
        if credential is None or credential.account_id != account_id:
            raise AssessmentError("CREDENTIAL_UNAVAILABLE",
                                  "Approved test credentials are unavailable.", "prepare")
        return credential


@dataclass(frozen=True)
class Policy:
    grant: LabGrant
    account_ids: tuple
    excluded_paths: tuple
    max_requests: int
    requests_per_second: float
    duration_seconds: int
    model_tokens: int

    def authorize(self, method, url, actor=None):
        self.grant.check_active()
        try:
            origin, path = parse_url(url)
        except (ValueError, TypeError):
            raise AssessmentError("ACTION_OUT_OF_SCOPE", "Action URL is outside lab scope.")
        if origin != self.grant.origin or actor not in (None, *self.account_ids):
            raise AssessmentError("ACTION_OUT_OF_SCOPE", "Action is outside approved scope.")
        if any(path.startswith(prefix) for prefix in self.excluded_paths):
            raise AssessmentError("ACTION_EXCLUDED", "Action matches an excluded path.")
        allowed = (
            method == "POST" and path == "/api/sessions" and actor is not None
        ) or (
            method == "GET" and (
                path in ("/api/me", "/api/invoices")
                or re.fullmatch(r"/api/invoices/[A-Za-z0-9_-]{1,100}", path)
            )
        )
        if not allowed:
            raise AssessmentError("ACTION_NOT_SUPPORTED",
                                  "This action is not supported by the lab assessment.")
        return path


def compile_policy(document, context, registry):
    if not valid(document, "assessment-request.schema.json"):
        reject("INVALID_REQUEST", "Assessment request does not satisfy its contract.")
    if document["environment"] != "isolated_lab" or document["mode"] != "account_based":
        reject("UNSUPPORTED_ASSESSMENT", "Only account-based controlled lab jobs are supported.")
    grant = registry.resolve(document["authorization_ref"], context)
    try:
        origin, path = parse_url(document["target"]["entry_url"])
        granted_origin, granted_path = parse_url(grant.origin)
    except (ValueError, TypeError):
        reject("TARGET_OUT_OF_SCOPE", "Only a registered canonical loopback target is supported.")
    if (
        origin != granted_origin or granted_path != "/" or path != "/"
        or list(document["scope"]["allowed_origins"]) != [granted_origin]
    ):
        reject("TARGET_OUT_OF_SCOPE", "Target and allowed origins must match this lab grant.")
    accounts = document["test_accounts"]
    approved = dict(grant.accounts)
    if (
        len(accounts) != 2 or len({a["account_id"] for a in accounts}) != 2
        or any(approved.get(a["account_id"]) != a["credential_ref"] or a["role"] != "customer"
               for a in accounts)
    ):
        reject("ACCOUNT_SCOPE_MISMATCH", "Exactly two approved customer accounts are required.")
    excluded = document["scope"]["excluded_path_prefixes"]
    if any("%" in value or "?" in value or "#" in value or "//" in value
           or any(ord(c) <= 32 for c in value) for value in excluded):
        reject("INVALID_SCOPE", "Excluded path prefixes must be canonical paths.")
    limits = document["limits"]
    try:
        finite_rate = math.isfinite(limits["max_requests_per_second"])
    except OverflowError:
        finite_rate = False
    if not finite_rate:
        reject("INVALID_LIMITS", "Rate limits must be finite.")
    return Policy(
        grant, tuple(a["account_id"] for a in accounts), tuple(excluded),
        min(limits["max_requests"], 100), min(limits["max_requests_per_second"], 100),
        min(limits["max_duration_seconds"], 60), min(limits["max_model_tokens"], 10000),
    )


class Budget:
    def __init__(self, policy, cancellation=None, clock=time.monotonic):
        self.policy = policy
        self.cancellation = cancellation if cancellation is not None else threading.Event()
        self.clock = clock
        self.started = clock()
        self.requests = 0
        self.last_request = None

    def check(self):
        if self.cancellation.is_set():
            raise AssessmentError("CANCELLED", "Assessment was cancelled.")
        self.policy.grant.check_active()
        if self.remaining <= 0:
            raise AssessmentError("TIME_BUDGET_EXHAUSTED", "Assessment time budget was exhausted.",
                                  retryable=True)

    @property
    def remaining(self):
        return self.policy.duration_seconds - (self.clock() - self.started)

    def reserve_request(self):
        self.check()
        if self.requests >= self.policy.max_requests:
            raise AssessmentError("REQUEST_BUDGET_EXHAUSTED",
                                  "Assessment request budget was exhausted.", retryable=True)
        if self.last_request is not None:
            delay = max(0, 1 / self.policy.requests_per_second
                        - (self.clock() - self.last_request))
            # Revocation is separate from cancellation; recheck during long waits.
            while delay > 0:
                self.cancellation.wait(min(0.1, delay, max(0, self.remaining)))
                self.check()
                delay = max(0, 1 / self.policy.requests_per_second
                            - (self.clock() - self.last_request))
        self.requests += 1  # Count attempts, including network and response failures.
        self.last_request = self.clock()
