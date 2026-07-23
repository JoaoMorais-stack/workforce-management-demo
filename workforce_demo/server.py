from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import json
import mimetypes
import os
import re

from .db import initialize
from .service import (
    NotFoundError,
    ValidationError,
    create_person,
    dashboard,
    delete_person,
    get_person,
    list_people,
    update_person,
)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DEFAULT_DB_PATH = BASE_DIR / "data" / "workforce_demo.db"
MAX_BODY_BYTES = 1_000_000
PERSON_ROUTE = re.compile(r"^/api/people/(\d+)$")


class ApplicationHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB_PATH
    server_version = "WorkforceDemo/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                self.send_json({"status": "ok"})
            elif parsed.path == "/api/dashboard":
                self.send_json(dashboard(self.db_path))
            elif parsed.path == "/api/people":
                query = parse_qs(parsed.query)
                people = list_people(
                    self.db_path,
                    query.get("query", [""])[0],
                    query.get("department", [""])[0],
                    query.get("status", [""])[0],
                )
                self.send_json({"people": people})
            elif match := PERSON_ROUTE.match(parsed.path):
                self.send_json({"person": get_person(self.db_path, int(match.group(1)))})
            else:
                self.serve_static(parsed.path)
        except Exception as error:
            self.handle_application_error(error)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/people":
                person = create_person(self.db_path, self.read_json())
                self.send_json({"person": person}, status=201)
            else:
                self.send_json({"error": "Route not found."}, status=404)
        except Exception as error:
            self.handle_application_error(error)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        try:
            match = PERSON_ROUTE.match(parsed.path)
            if not match:
                self.send_json({"error": "Route not found."}, status=404)
                return
            person = update_person(self.db_path, int(match.group(1)), self.read_json())
            self.send_json({"person": person})
        except Exception as error:
            self.handle_application_error(error)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            match = PERSON_ROUTE.match(parsed.path)
            if not match:
                self.send_json({"error": "Route not found."}, status=404)
                return
            delete_person(self.db_path, int(match.group(1)))
            self.send_json({"deleted": True})
        except Exception as error:
            self.handle_application_error(error)

    def read_json(self) -> dict:
        if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
            raise ValidationError("Content-Type must be application/json.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValidationError("Content-Length is invalid.") from error
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValidationError("Request body size is invalid.")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("Request body must contain valid JSON.") from error
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object.")
        return payload

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else unquote(request_path).lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_json({"error": "Route not found."}, status=404)
            return
        if not candidate.is_file():
            self.send_json({"error": "Route not found."}, status=404)
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        body = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'")

    def handle_application_error(self, error: Exception) -> None:
        if isinstance(error, ValidationError):
            self.send_json({"error": str(error)}, status=400)
        elif isinstance(error, NotFoundError):
            self.send_json({"error": str(error)}, status=404)
        else:
            self.log_error("Unhandled application error: %s", error)
            self.send_json({"error": "Unexpected application error."}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def create_server(host: str = "127.0.0.1", port: int = 5000, db_path: Path | str = DEFAULT_DB_PATH) -> ThreadingHTTPServer:
    initialize(db_path)
    handler = type("ConfiguredApplicationHandler", (ApplicationHandler,), {"db_path": Path(db_path)})
    return ThreadingHTTPServer((host, port), handler)


def run() -> None:
    host = os.environ.get("WORKFORCE_HOST", "127.0.0.1")
    port = int(os.environ.get("WORKFORCE_PORT", "5000"))
    db_path = Path(os.environ.get("WORKFORCE_DB_PATH", str(DEFAULT_DB_PATH)))
    server = create_server(host, port, db_path)
    print(f"Workforce Management Demo is available at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
