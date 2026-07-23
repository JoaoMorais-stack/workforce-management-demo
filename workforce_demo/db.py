from __future__ import annotations

from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    job_title TEXT NOT NULL,
    department TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    work_mode TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL,
    start_date TEXT NOT NULL,
    weekly_capacity INTEGER NOT NULL DEFAULT 40,
    skills TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS time_off (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_people_department ON people(department);
CREATE INDEX IF NOT EXISTS idx_people_status ON people(status);
CREATE INDEX IF NOT EXISTS idx_time_off_dates ON time_off(start_date, end_date);
"""


DEMO_PEOPLE = (
    ("Maya", "Chen", "maya.chen@example.com", "Product Designer", "Product", "Full-time", "Hybrid", "North Hub", "Active", "2024-02-12", 40, "Research, Prototyping, Design systems", "Supports the customer discovery program."),
    ("Lucas", "Bennett", "lucas.bennett@example.com", "Software Engineer", "Engineering", "Full-time", "Remote", "Remote", "Active", "2023-08-21", 40, "Python, JavaScript, SQLite", "Maintains internal workflow tools."),
    ("Priya", "Nair", "priya.nair@example.com", "Data Analyst", "Operations", "Full-time", "Hybrid", "Central Hub", "Active", "2024-05-06", 36, "SQL, Reporting, Forecasting", "Owns weekly operational reporting."),
    ("Noah", "Kim", "noah.kim@example.com", "Project Coordinator", "Operations", "Contract", "On-site", "South Hub", "Active", "2025-01-13", 32, "Planning, Facilitation, Documentation", "Coordinates cross-team delivery calendars."),
    ("Sofia", "Reyes", "sofia.reyes@example.com", "Customer Specialist", "Customer Success", "Full-time", "Remote", "Remote", "On leave", "2023-11-20", 40, "Onboarding, Support, Knowledge base", "Leads customer onboarding sessions."),
    ("Elias", "Carter", "elias.carter@example.com", "Quality Analyst", "Engineering", "Part-time", "Hybrid", "North Hub", "Active", "2025-03-03", 24, "Test design, Accessibility, Automation", "Focuses on release readiness."),
)


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(db_path: Path | str) -> None:
    with closing(connect(db_path)) as connection:
        with connection:
            connection.executescript(SCHEMA)
            total = connection.execute("SELECT COUNT(*) AS total FROM people").fetchone()["total"]
            if total == 0:
                seed_demo_data(connection)


def seed_demo_data(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO people (
            first_name, last_name, email, job_title, department,
            employment_type, work_mode, location, status, start_date,
            weekly_capacity, skills, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        DEMO_PEOPLE,
    )

    ids = {
        row["email"]: row["id"]
        for row in connection.execute("SELECT id, email FROM people").fetchall()
    }
    today = date.today()
    time_off = (
        (ids["sofia.reyes@example.com"], "Vacation", (today - timedelta(days=2)).isoformat(), (today + timedelta(days=3)).isoformat(), "Approved"),
        (ids["maya.chen@example.com"], "Personal", (today + timedelta(days=8)).isoformat(), (today + timedelta(days=9)).isoformat(), "Approved"),
        (ids["elias.carter@example.com"], "Vacation", (today + timedelta(days=18)).isoformat(), (today + timedelta(days=22)).isoformat(), "Pending"),
    )
    connection.executemany(
        "INSERT INTO time_off (person_id, category, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
        time_off,
    )
