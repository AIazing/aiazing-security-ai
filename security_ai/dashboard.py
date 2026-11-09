"""Loopback dashboard for controller-owned lab assessments and local reports."""

import argparse
from copy import deepcopy
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import threading
import uuid

from labs.invoice.assessment import prepare_assessment
from labs.invoice.control import InvoiceLab

from .contracts import valid
from .runner import AssessmentRunner, LocalArtifacts, timestamp

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).with_name("ui")
REPORT_ID = re.compile(r"assessment-[a-f0-9]{32}")
MAX_FILE_BYTES = 2 * 1024 * 1024


class JobBusy(Exception):
    pass


class Dashboard:
    def __init__(self, output):
        self.output = Path(output)
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.jobs = []
        self.active = None
        self.worker = None
        self.cancellation = None
        self.closed = False

    def _file(self, identifier, kind):
        if REPORT_ID.fullmatch(identifier) is None or kind not in ("report", "evidence"):
            raise FileNotFoundError()
        directory = self.output / identifier
        path = directory / (kind + ".json")
        if directory.is_symlink() or path.is_symlink() or not path.is_file():
            raise FileNotFoundError()
        if path.stat().st_size > MAX_FILE_BYTES:
            raise FileNotFoundError()
        return path

    def read(self, identifier, kind):
        path = self._file(identifier, kind)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            raise FileNotFoundError()
        if not isinstance(value, dict) or value.get("assessment_id") != identifier:
            raise FileNotFoundError()
        if kind == "report" and not valid(value, "assessment-result.schema.json"):
            raise FileNotFoundError()
        return value

    def reports(self):
        items = []
        if self.output.is_dir():
            # Only the configured report root is indexed; never a browser-supplied path.
            directories = [
                path for path in self.output.iterdir()
                if REPORT_ID.fullmatch(path.name) and not path.is_symlink() and path.is_dir()
            ]
            for directory in sorted(directories, key=lambda p: p.stat().st_mtime,
                                    reverse=True)[:200]:
                try:
                    result = self.read(directory.name, "report")
                except FileNotFoundError:
                    continue
                items.append({
                    "assessment_id": result["assessment_id"],
                    "target_url": result["target_url"],
                    "status": result["status"],
                    "finished_at": result["finished_at"],
                    "findings": len(result["findings"]),
                    "requests": result["usage"]["requests"],
                    "duration_seconds": result["usage"]["duration_seconds"],
                })
        return sorted(items, key=lambda item: item["finished_at"], reverse=True)[:30]

    def snapshot(self):
        project = json.loads((ROOT / "project-status.json").read_text(encoding="utf-8"))
        with self.lock:
            jobs = deepcopy(self.jobs)
            active = self.active
        return {
            "project": project,
            "csrf_token": self.token,
            "active_job": active,
            "jobs": jobs,
            "reports": self.reports(),
        }

    def start(self, fixture, max_requests):
        if fixture not in ("vulnerable", "fixed", "both"):
            raise ValueError("Unsupported fixture")
        if type(max_requests) is not int or not 1 <= max_requests <= 100:
            raise ValueError("Request limit must be between 1 and 100")
        with self.lock:
            if self.closed or self.active is not None:
                raise JobBusy()
            identifier = "job-" + uuid.uuid4().hex
            labels = ("vulnerable", "fixed") if fixture == "both" else (fixture,)
            job = {
                "id": identifier, "fixture": fixture, "status": "running",
                "stage": "queued", "current_fixture": None, "started_at": timestamp(),
                "finished_at": None, "runs": [], "events": [], "total_runs": len(labels),
                "max_requests": max_requests,
            }
            self.jobs = self.jobs[-9:] + [job]
            self.active = identifier
            self.cancellation = threading.Event()
            self.worker = threading.Thread(
                target=self._run, args=(job, labels, max_requests, self.cancellation), daemon=True
            )
            self.worker.start()
            return identifier

    def _progress(self, job, event):
        with self.lock:
            job["stage"] = event["stage"]
            job["events"].append({"at": timestamp(), "fixture": job["current_fixture"], **event})
            job["events"] = job["events"][-120:]

    def _run(self, job, labels, max_requests, cancellation):
        final_status = "failed"
        try:
            with InvoiceLab() as lab:
                for label in labels:
                    if cancellation.is_set():
                        break
                    with self.lock:
                        job["current_fixture"] = label
                    registry, context, expected, document = prepare_assessment(lab, label)
                    document["limits"]["max_requests"] = max_requests
                    runner = AssessmentRunner(registry, context, expected, LocalArtifacts(self.output))
                    result = runner.run(
                        document, cancellation,
                        on_progress=lambda event: self._progress(job, event),
                    )
                    with self.lock:
                        job["runs"].append({
                            "fixture": label, "assessment_id": result["assessment_id"],
                            "status": result["status"], "findings": len(result["findings"]),
                            "requests": result["usage"]["requests"],
                        })
                with self.lock:
                    statuses = [item["status"] for item in job["runs"]]
                    if cancellation.is_set() or "cancelled" in statuses:
                        final_status = "cancelled"
                    elif len(statuses) == len(labels) and all(s == "completed" for s in statuses):
                        final_status = "completed"
                    elif any(s in ("completed", "partial") for s in statuses):
                        final_status = "partial"
                    else:
                        final_status = "failed"
        except Exception:
            # Do not expose exception strings or credentials to the browser.
            with self.lock:
                final_status = "failed"
                job["events"].append({
                    "at": timestamp(), "stage": "error",
                    "message": "Local assessment could not finish. Review the saved reports, if any.",
                })
        finally:
            with self.lock:
                job["status"] = final_status
                job["finished_at"] = timestamp()
                job["stage"] = "finished"
                self.active = None

    def cancel(self, identifier):
        with self.lock:
            if self.active != identifier or self.cancellation is None:
                raise FileNotFoundError()
            self.cancellation.set()

    def close(self):
        with self.lock:
            self.closed = True
            if self.cancellation is not None:
                self.cancellation.set()
            worker = self.worker
        if worker is not None:
            worker.join(timeout=5)
            if worker.is_alive():
                raise RuntimeError("Assessment worker has not stopped")


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port, dashboard):
        self.dashboard = dashboard
        super().__init__(("127.0.0.1", port), Handler)

    @property
    def origin(self):
        return "http://127.0.0.1:{}".format(self.server_port)


class Handler(BaseHTTPRequestHandler):
    server_version = "SecurityDashboard"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(3)

    def log_message(self, *args):
        pass

    def reply(self, status, value, content_type="application/json", attachment=None):
        payload = (
            json.dumps(value, allow_nan=False).encode()
            if content_type == "application/json" else value
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        if attachment:
            self.send_header("Content-Disposition", 'attachment; filename="{}"'.format(attachment))
        self.end_headers()
        self.wfile.write(payload)

    def allowed(self, mutation=False):
        if self.headers.get_all("Host", []) != [self.server.origin[len("http://"):]]:
            self.reply(421, {"error": "Unrecognized dashboard host"})
            return False
        origins = self.headers.get_all("Origin", [])
        if (origins and origins != [self.server.origin]) or (
            self.headers.get("Sec-Fetch-Site") == "cross-site"
        ):
            self.reply(403, {"error": "Origin not allowed"})
            return False
        if mutation:
            tokens = self.headers.get_all("X-Dashboard-Token", [])
            if origins != [self.server.origin] or len(tokens) != 1 or not hmac.compare_digest(
                tokens[0].encode(), self.server.dashboard.token.encode()
            ):
                self.reply(403, {"error": "Dashboard authorization required"})
                return False
        return True

    def do_GET(self):
        if not self.allowed():
            return
        if self.path == "/favicon.ico":
            self.reply(204, b"", "image/x-icon")
            return
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.css": ("app.css", "text/css"),
            "/app.js": ("app.js", "text/javascript"),
        }
        if self.path in assets:
            name, kind = assets[self.path]
            self.reply(200, (ASSETS / name).read_bytes(), kind)
            return
        if self.path == "/api/state":
            self.reply(200, self.server.dashboard.snapshot())
            return
        match = re.fullmatch(r"/api/reports/(assessment-[a-f0-9]{32})/(report|evidence)(/download)?",
                             self.path)
        if match:
            identifier, kind, download = match.groups()
            try:
                document = self.server.dashboard.read(identifier, kind)
            except FileNotFoundError:
                self.reply(404, {"error": "Report not found"})
                return
            self.reply(200, document, attachment=identifier + "-" + kind + ".json"
                       if download else None)
            return
        self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if not self.allowed(mutation=True):
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None:
            self.reply(400, {"error": "A single content length is required"})
            return
        try:
            length = int(lengths[0])
            if not 0 <= length <= 2048:
                raise ValueError()
            if self.headers.get_content_type() != "application/json":
                raise ValueError()
            document = json.loads(self.rfile.read(length))
            if not isinstance(document, dict):
                raise ValueError()
        except (ValueError, UnicodeError, RecursionError):
            self.reply(400, {"error": "A small JSON object is required"})
            return
        if self.path == "/api/jobs":
            if set(document) != {"fixture", "max_requests"}:
                self.reply(400, {"error": "Fixture and request limit are required"})
                return
            try:
                identifier = self.server.dashboard.start(
                    document["fixture"], document["max_requests"]
                )
            except ValueError:
                self.reply(400, {"error": "Invalid fixture or request limit"})
                return
            except JobBusy:
                self.reply(409, {"error": "An assessment is already running"})
                return
            self.reply(202, {"job_id": identifier})
            return
        match = re.fullmatch(r"/api/jobs/(job-[a-f0-9]{32})/cancel", self.path)
        if match and not document:
            try:
                self.server.dashboard.cancel(match.group(1))
            except FileNotFoundError:
                self.reply(404, {"error": "Active assessment not found"})
                return
            self.reply(202, {"status": "cancellation_requested"})
            return
        self.reply(404, {"error": "Not found"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--output", type=Path, default=Path("artifacts/assessment-demo"))
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Port must be between 0 and 65535")
    dashboard = Dashboard(args.output)
    server = None
    try:
        server = DashboardServer(args.port, dashboard)
        print("Dashboard: " + server.origin, flush=True)
        print("Local lab assessments only. Press Ctrl-C to stop.", flush=True)
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    except OSError:
        parser.exit(1, "Could not start the local dashboard; the port may be occupied.\n")
    finally:
        if server is not None:
            server.server_close()
        dashboard.close()


if __name__ == "__main__":
    main()
