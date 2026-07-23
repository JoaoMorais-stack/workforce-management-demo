from __future__ import annotations

from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
import re
import sqlite3

from .db import connect


DEPARTMENTS = ("Product", "Engineering", "Operations", "Customer Success")
STATUSES = ("Active", "On leave", "Inactive")
EMPLOYMENT_TYPES = ("Full-time", "Part-time", "Contract")
WORK_MODES = ("On-site", "Hybrid", "Remote")
TIME_OFF_CATEGORIES = ("Vacation", "Personal", "Medical", "Other")
TIME_OFF_STATUSES = ("Pending", "Approved", "Declined")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


def _text(value: object, field: str, *, required: bool = False, limit: int = 240) -> str:
    result = re.sub(r"\s+", " ", str(value or "").strip())
    if required and not result:
        raise ValidationError(f"{field} is required.")
    if len(result) > limit:
        raise ValidationError(f"{field} must contain at most {limit} characters.")
    return result


def _choice(value: object, field: str, choices: tuple[str, ...]) -> str:
    result = _text(value, field, required=True, limit=80)
    if result not in choices:
        raise ValidationError(f"{field} has an unsupported value.")
    return result


def _date(value: object, field: str, *, required: bool = True) -> str:
    result = _text(value, field, required=required, limit=10)
    if not result:
        return ""
    try:
        date.fromisoformat(result)
    except ValueError as error:
        raise ValidationError(f"{field} must use YYYY-MM-DD format.") from error
    return result


def _person_payload(payload: dict) -> dict:
    email = _text(payload.get("email"), "Email", required=True, limit=160).lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Email must be valid.")
    try:
        capacity = int(payload.get("weekly_capacity", 40))
    except (TypeError, ValueError) as error:
        raise ValidationError("Weekly capacity must be a whole number.") from error
    if not 1 <= capacity <= 80:
        raise ValidationError("Weekly capacity must be between 1 and 80 hours.")

    return {
        "first_name": _text(payload.get("first_name"), "First name", required=True, limit=80),
        "last_name": _text(payload.get("last_name"), "Last name", required=True, limit=80),
        "email": email,
        "job_title": _text(payload.get("job_title"), "Job title", required=True, limit=120),
        "department": _choice(payload.get("department"), "Department", DEPARTMENTS),
        "employment_type": _choice(payload.get("employment_type"), "Employment type", EMPLOYMENT_TYPES),
        "work_mode": _choice(payload.get("work_mode"), "Work mode", WORK_MODES),
        "location": _text(payload.get("location"), "Location", required=True, limit=100),
        "status": _choice(payload.get("status"), "Status", STATUSES),
        "start_date": _date(payload.get("start_date"), "Start date"),
        "weekly_capacity": capacity,
        "skills": _text(payload.get("skills"), "Skills", limit=500),
        "notes": _text(payload.get("notes"), "Notes", limit=1200),
    }


def _time_off_payload(items: object) -> list[dict]:
    if items is None:
        return []
    if not isinstance(items, list) or len(items) > 20:
        raise ValidationError("Time off must be a list with at most 20 entries.")
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("Each time off entry must be an object.")
        start = _date(item.get("start_date"), "Time off start date")
        end = _date(item.get("end_date"), "Time off end date")
        if end < start:
            raise ValidationError("Time off end date cannot be before its start date.")
        cleaned.append({
            "category": _choice(item.get("category"), "Time off category", TIME_OFF_CATEGORIES),
            "start_date": start,
            "end_date": end,
            "status": _choice(item.get("status"), "Time off status", TIME_OFF_STATUSES),
        })
    return cleaned


def _serialize_person(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["full_name"] = f"{item['first_name']} {item['last_name']}"
    item["skills_list"] = [value.strip() for value in item["skills"].split(",") if value.strip()]
    return item


def list_people(db_path: Path | str, query: str = "", department: str = "", status: str = "") -> list[dict]:
    clauses = []
    values: list[str] = []
    query = _text(query, "Search", limit=120)
    if query:
        clauses.append("(first_name || ' ' || last_name || ' ' || email || ' ' || job_title || ' ' || department || ' ' || work_mode || ' ' || location LIKE ?)")
        values.append(f"%{query}%")
    if department:
        clauses.append("department = ?")
        values.append(_choice(department, "Department", DEPARTMENTS))
    if status:
        clauses.append("status = ?")
        values.append(_choice(status, "Status", STATUSES))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with closing(connect(db_path)) as connection:
        rows = connection.execute(
            f"SELECT * FROM people {where} ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE",
            values,
        ).fetchall()
    return [_serialize_person(row) for row in rows]


def get_person(db_path: Path | str, person_id: int) -> dict:
    with closing(connect(db_path)) as connection:
        row = connection.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if row is None:
            raise NotFoundError("Person not found.")
        person = _serialize_person(row)
        person["time_off"] = [
            dict(item)
            for item in connection.execute(
                "SELECT id, category, start_date, end_date, status FROM time_off WHERE person_id = ? ORDER BY start_date",
                (person_id,),
            ).fetchall()
        ]
    return person


def create_person(db_path: Path | str, payload: dict) -> dict:
    person = _person_payload(payload)
    time_off = _time_off_payload(payload.get("time_off"))
    columns = ", ".join(person)
    placeholders = ", ".join("?" for _ in person)
    try:
        with closing(connect(db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    f"INSERT INTO people ({columns}) VALUES ({placeholders})",
                    tuple(person.values()),
                )
                _replace_time_off(connection, cursor.lastrowid, time_off)
                person_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        raise ValidationError("Email is already in use.") from error
    return get_person(db_path, person_id)


def update_person(db_path: Path | str, person_id: int, payload: dict) -> dict:
    person = _person_payload(payload)
    time_off = _time_off_payload(payload.get("time_off"))
    assignments = ", ".join(f"{column} = ?" for column in person)
    try:
        with closing(connect(db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    f"UPDATE people SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (*person.values(), person_id),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError("Person not found.")
                _replace_time_off(connection, person_id, time_off)
    except sqlite3.IntegrityError as error:
        raise ValidationError("Email is already in use.") from error
    return get_person(db_path, person_id)


def _replace_time_off(connection: sqlite3.Connection, person_id: int, items: list[dict]) -> None:
    connection.execute("DELETE FROM time_off WHERE person_id = ?", (person_id,))
    connection.executemany(
        "INSERT INTO time_off (person_id, category, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
        [
            (person_id, item["category"], item["start_date"], item["end_date"], item["status"])
            for item in items
        ],
    )


def delete_person(db_path: Path | str, person_id: int) -> None:
    with closing(connect(db_path)) as connection:
        with connection:
            cursor = connection.execute("DELETE FROM people WHERE id = ?", (person_id,))
            if cursor.rowcount == 0:
                raise NotFoundError("Person not found.")


def dashboard(db_path: Path | str) -> dict:
    today = date.today()
    upcoming_limit = today + timedelta(days=30)
    with closing(connect(db_path)) as connection:
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN status = 'On leave' THEN 1 ELSE 0 END) AS on_leave,
                ROUND(AVG(weekly_capacity), 1) AS average_capacity
            FROM people
            """
        ).fetchone()
        departments = [
            dict(row)
            for row in connection.execute(
                "SELECT department AS label, COUNT(*) AS value FROM people GROUP BY department ORDER BY value DESC, label"
            ).fetchall()
        ]
        upcoming = [
            dict(row)
            for row in connection.execute(
                """
                SELECT t.id, t.person_id, p.first_name || ' ' || p.last_name AS person_name,
                       t.category, t.start_date, t.end_date, t.status
                FROM time_off t
                JOIN people p ON p.id = t.person_id
                WHERE t.end_date >= ? AND t.start_date <= ?
                ORDER BY t.start_date, person_name
                """,
                (today.isoformat(), upcoming_limit.isoformat()),
            ).fetchall()
        ]
    return {
        "as_of": today.isoformat(),
        "summary": dict(summary),
        "departments": departments,
        "upcoming_time_off": upcoming,
    }
