from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import unittest

from workforce_demo.server import create_server


class WorkforceServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.server = create_server("127.0.0.1", 0, Path(self.temp_dir.name) / "api-test.db")
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def fetch_json(self, path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        with urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())

    def test_health_dashboard_and_static_interface(self) -> None:
        status, health = self.fetch_json("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health, {"status": "ok"})

        status, dashboard = self.fetch_json("/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(dashboard["summary"]["total"], 6)

        with urlopen(f"{self.base_url}/", timeout=2) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Workforce Management", html)
            self.assertIn("Content-Security-Policy", response.headers)

    def test_create_and_retrieve_through_api(self) -> None:
        payload = {
            "first_name": "Jordan",
            "last_name": "Taylor",
            "email": "jordan.taylor@example.com",
            "job_title": "Portfolio Coordinator",
            "department": "Product",
            "employment_type": "Contract",
            "work_mode": "Remote",
            "location": "Remote",
            "status": "Active",
            "start_date": "2026-04-06",
            "weekly_capacity": 30,
            "skills": "Planning, Communication",
            "notes": "Synthetic API test record.",
            "time_off": [],
        }
        status, created = self.fetch_json("/api/people", "POST", payload)
        self.assertEqual(status, 201)
        person_id = created["person"]["id"]

        status, fetched = self.fetch_json(f"/api/people/{person_id}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["person"]["email"], payload["email"])

    def test_rejects_invalid_json_payload(self) -> None:
        request = Request(
            f"{self.base_url}/api/people",
            data=b"[]",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)
        self.assertEqual(context.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
