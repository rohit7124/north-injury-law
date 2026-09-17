"""
SQLite storage for Northstar Injury Law leads.

Deliberately plain stdlib sqlite3 rather than an ORM — this is an MVP with
one table and a handful of queries, so a query builder or migration tool
would add complexity without adding value.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "leads.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    contact_method TEXT,
    accident_type TEXT NOT NULL,
    accident_date TEXT,
    description TEXT NOT NULL,
    consent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
status TEXT NOT NULL DEFAULT 'new',
notes TEXT NOT NULL DEFAULT ''
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA)

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(leads)").fetchall()
        }

        if "notes" not in columns:
            conn.execute(
                "ALTER TABLE leads ADD COLUMN notes TEXT NOT NULL DEFAULT ''"
            )

        if "contacted_at" not in columns:
            conn.execute(
                "ALTER TABLE leads ADD COLUMN contacted_at TEXT"
            )

def insert_lead(lead: dict) -> int:


    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads
                (first_name, last_name, phone, email, contact_method,
                 accident_type, accident_date, description, consent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["first_name"],
                lead["last_name"],
                lead["phone"],
                lead["email"],
                lead.get("contact_method"),
                lead["accident_type"],
                lead.get("accident_date"),
                lead["description"],
                1 if lead["consent"] else 0,
            ),
        )
        return cursor.lastrowid


def list_leads(limit: int = 200) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, first_name, last_name, phone, email, contact_method,
accident_type, accident_date, description,
created_at, status, notes, contacted_at
FROM leads
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
def update_lead_status(lead_id: int, status: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE leads
SET
    status = ?,
    contacted_at = CASE
        WHEN ? = 'contacted' AND contacted_at IS NULL
        THEN CURRENT_TIMESTAMP
        ELSE contacted_at
    END
WHERE id = ?
            """,
            (status, status, lead_id),
        )
        return cursor.rowcount > 0

def update_lead_notes(lead_id: int, notes: str) -> bool:
     with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE leads
            SET notes = ?
            WHERE id = ?
            """,
            (notes, lead_id),
        )
        return cursor.rowcount > 0
