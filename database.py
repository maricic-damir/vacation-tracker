"""SQLite schema, connection, and DB path resolution (find or create)."""
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from config import get_db_path, get_saved_db_path_raw, set_db_path


DB_FILENAME = "vacation.db"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
-- Employees
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jmbg TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    contract_type TEXT NOT NULL CHECK (contract_type IN ('fixed_term', 'open_ended')),
    contract_end_date DATE NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Per-employee per-year balance: days at start of year/period and transferred
CREATE TABLE IF NOT EXISTS employee_year_balance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    days_at_start INTEGER NOT NULL DEFAULT 0,
    days_transferred INTEGER NOT NULL DEFAULT 0,
    UNIQUE(employee_id, year)
);

-- Earned days (blood donation, overtime, etc.) – free text notes
CREATE TABLE IF NOT EXISTS earned_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    earned_date DATE NOT NULL,
    number_of_days INTEGER NOT NULL,
    reason_notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Vacation / day-off records (scheduled and used)
CREATE TABLE IF NOT EXISTS vacation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    booking_date DATE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_vacation_employee ON vacation_records(employee_id);
CREATE INDEX IF NOT EXISTS ix_vacation_dates ON vacation_records(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_earned_employee ON earned_days(employee_id);
CREATE INDEX IF NOT EXISTS ix_earned_date ON earned_days(earned_date);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


# ---------------------------------------------------------------------------
# DB path: first run vs find
# ---------------------------------------------------------------------------

def resolve_db_path(choose_or_create_callback, locate_callback) -> Optional[str]:
    """
    Use saved path if valid. If no path or file missing:
    - First time (no config): call choose_or_create_callback() -> user picks where to store new DB.
    - Config existed but file missing: call locate_callback() -> user locates vacation.db.
    Returns None if user cancelled.
    """
    saved = get_db_path()
    if saved:
        return saved
    # App was run before on this machine if we have a saved path (even invalid)
    had_saved_path = get_saved_db_path_raw() is not None
    if had_saved_path:
        path = locate_callback()
    else:
        path = choose_or_create_callback()
    if path:
        set_db_path(path)
    return path


def ensure_year_balance(conn: sqlite3.Connection, employee_id: int, year: int, contract_type: str) -> None:
    """Create employee_year_balance for this year if missing. Open-ended gets 20 days_at_start."""
    cur = conn.execute(
        "SELECT 1 FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    if cur.fetchone():
        return
    days_at_start = 20 if contract_type == "open_ended" else 0
    conn.execute(
        "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, ?, 0)",
        (employee_id, year, days_at_start),
    )
    conn.commit()


def run_completion_job(conn: sqlite3.Connection) -> None:
    """Mark vacation_records as completed where end_date < today and update updated_at."""
    today = date.today().isoformat()
    conn.execute(
        "UPDATE vacation_records SET is_completed = 1 WHERE is_completed = 0 AND end_date < ?",
        (today,),
    )
    conn.commit()
