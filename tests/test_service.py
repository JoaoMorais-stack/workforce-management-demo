from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from workforce_demo.db import initialize
from workforce_demo.service import (
    NotFoundError,
    ValidationError,
    create_person,
    dashboard,
    delete_person,
    get_person,
    list_people,
    update_person,
)


def valid_person() -> dict:
    return {
        "first_name": "Avery",
        "last_name": "Morgan",
        "email": "avery.morgan@example.com",
        "job_title": "Business Analyst",
        "department": "Product",
        "employment_type": "Full-time",
        "work_mode": "Hybrid",
        "location": "Central Hub",
        "status": "Active",
        "start_date": "2026-01-12",
        "weekly_capacity": 40,
        "skills": "Discovery, Process mapping",
        "notes": "Fictional record used by automated tests.",
        "time_off": [
            {
                "category": "Personal",
                "start_date": "2026-09-10",
                "end_date": "2026-09-11",
                "status": "Approved",
            }
        ],
    }


class WorkforceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        initialize(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_demo_database_and_dashboard(self) -> None:
        people = list_people(self.db_path)
        summary = dashboard(self.db_path)
        self.assertEqual(len(people), 6)
        self.assertEqual(summary["summary"]["total"], 6)
        self.assertEqual(summary["summary"]["active"], 5)

    def test_create_update_and_delete_person(self) -> None:
        created = create_person(self.db_path, valid_person())
        self.assertEqual(created["full_name"], "Avery Morgan")
        self.assertEqual(len(created["time_off"]), 1)

        payload = valid_person()
        payload["job_title"] = "Senior Business Analyst"
        payload["time_off"] = []
        updated = update_person(self.db_path, created["id"], payload)
        self.assertEqual(updated["job_title"], "Senior Business Analyst")
        self.assertEqual(updated["time_off"], [])

        delete_person(self.db_path, created["id"])
        with self.assertRaises(NotFoundError):
            get_person(self.db_path, created["id"])

    def test_filters(self) -> None:
        engineering = list_people(self.db_path, department="Engineering")
        remote = list_people(self.db_path, query="Remote")
        self.assertEqual(len(engineering), 2)
        self.assertGreaterEqual(len(remote), 1)

    def test_rejects_invalid_input_and_duplicate_email(self) -> None:
        payload = valid_person()
        payload["weekly_capacity"] = 100
        with self.assertRaises(ValidationError):
            create_person(self.db_path, payload)

        payload = valid_person()
        create_person(self.db_path, payload)
        with self.assertRaises(ValidationError):
            create_person(self.db_path, payload)


if __name__ == "__main__":
    unittest.main()
