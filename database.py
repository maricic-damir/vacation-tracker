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
    days_from_transferred INTEGER NOT NULL DEFAULT 0,
    days_from_at_start INTEGER NOT NULL DEFAULT 0,
    days_from_earned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_vacation_employee ON vacation_records(employee_id);
CREATE INDEX IF NOT EXISTS ix_vacation_dates ON vacation_records(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_earned_employee ON earned_days(employee_id);
CREATE INDEX IF NOT EXISTS ix_earned_date ON earned_days(earned_date);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    migrate_add_deduction_tracking(conn)
    conn.commit()


def migrate_add_deduction_tracking(conn: sqlite3.Connection) -> None:
    """Add deduction tracking columns to vacation_records table if they don't exist."""
    cur = conn.execute("PRAGMA table_info(vacation_records)")
    columns = {row[1] for row in cur.fetchall()}
    
    if "days_from_transferred" not in columns:
        conn.execute("ALTER TABLE vacation_records ADD COLUMN days_from_transferred INTEGER NOT NULL DEFAULT 0")
        conn.execute("ALTER TABLE vacation_records ADD COLUMN days_from_at_start INTEGER NOT NULL DEFAULT 0")
        conn.execute("ALTER TABLE vacation_records ADD COLUMN days_from_earned INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        recalculate_existing_vacation_deductions(conn)


def recalculate_existing_vacation_deductions(conn: sqlite3.Connection) -> None:
    """
    Retroactively calculate deduction breakdown for existing completed vacation records.
    Processes records in chronological order (by start_date) for each employee.
    """
    from db_helpers import count_days_in_range, calculate_deduction_breakdown
    
    cur = conn.execute("SELECT DISTINCT employee_id FROM vacation_records WHERE is_completed = 1 ORDER BY employee_id")
    employee_ids = [row[0] for row in cur.fetchall()]
    
    for employee_id in employee_ids:
        cur = conn.execute("""
            SELECT DISTINCT strftime('%Y', start_date) as year 
            FROM vacation_records 
            WHERE employee_id = ? AND is_completed = 1
            ORDER BY year
        """, (employee_id,))
        years = [int(row[0]) for row in cur.fetchall()]
        
        for year in years:
            cur = conn.execute(
                "SELECT days_at_start, days_transferred FROM employee_year_balance WHERE employee_id = ? AND year = ?",
                (employee_id, year),
            )
            row = cur.fetchone()
            at_start_available = row[0] if row else 0
            transferred_available = row[1] if row else 0
            
            cur = conn.execute(
                "SELECT COALESCE(SUM(number_of_days), 0) FROM earned_days WHERE employee_id = ? AND strftime('%Y', earned_date) = ?",
                (employee_id, str(year)),
            )
            earned_available = cur.fetchone()[0]
            
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            cur = conn.execute("""
                SELECT id, start_date, end_date 
                FROM vacation_records 
                WHERE employee_id = ? AND is_completed = 1
                AND (strftime('%Y', start_date) = ? OR strftime('%Y', end_date) = ? OR (start_date <= ? AND end_date >= ?))
                ORDER BY start_date, id
            """, (employee_id, str(year), str(year), year_start, year_end))
            
            records = cur.fetchall()
            
            for record in records:
                record_id = record[0]
                start_date = record[1]
                end_date = record[2]
                
                days_needed = count_days_in_range(start_date, end_date)
                
                breakdown = calculate_deduction_breakdown(
                    days_needed,
                    transferred_available,
                    at_start_available,
                    earned_available
                )
                
                conn.execute("""
                    UPDATE vacation_records 
                    SET days_from_transferred = ?,
                        days_from_at_start = ?,
                        days_from_earned = ?
                    WHERE id = ?
                """, (breakdown['transferred'], breakdown['at_start'], breakdown['earned'], record_id))
                
                transferred_available -= breakdown['transferred']
                at_start_available -= breakdown['at_start']
                earned_available -= breakdown['earned']
    
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
    """Mark vacation_records as completed where end_date < today and calculate deduction breakdown."""
    from db_helpers import get_available_days_for_deduction, calculate_deduction_breakdown, count_days_in_range
    
    today = date.today().isoformat()
    
    cur = conn.execute(
        """SELECT id, employee_id, start_date, end_date 
           FROM vacation_records 
           WHERE is_completed = 0 AND end_date < ?""",
        (today,)
    )
    records_to_complete = cur.fetchall()
    
    for record in records_to_complete:
        record_id = record[0]
        employee_id = record[1]
        start_date = record[2]
        end_date = record[3]
        
        year = date.fromisoformat(start_date).year
        days_needed = count_days_in_range(start_date, end_date)
        
        available = get_available_days_for_deduction(conn, employee_id, year)
        breakdown = calculate_deduction_breakdown(
            days_needed,
            available['transferred'],
            available['at_start'],
            available['earned']
        )
        
        conn.execute(
            """UPDATE vacation_records 
               SET is_completed = 1,
                   days_from_transferred = ?,
                   days_from_at_start = ?,
                   days_from_earned = ?
               WHERE id = ?""",
            (breakdown['transferred'], breakdown['at_start'], breakdown['earned'], record_id)
        )
    
    conn.commit()


def rollover_year_for_employee(conn: sqlite3.Connection, employee_id: int, from_year: int, to_year: int) -> bool:
    """
    Rollover an employee's balance from one year to the next.
    Returns True if rollover was performed, False if skipped (already exists or no balance).
    """
    from entitlement import prorated_vacation_entitlement_for_year
    from db_helpers import get_year_balance, get_employee
    
    cur = conn.execute(
        "SELECT 1 FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, to_year),
    )
    if cur.fetchone():
        return False
    
    employee = get_employee(conn, employee_id)
    if not employee:
        return False
    
    balance = get_year_balance(conn, employee_id, from_year)
    
    unused_days = balance["transferred_left"] + balance["at_start_left"] + balance["earned_left"]
    
    days_at_start = prorated_vacation_entitlement_for_year(
        date(to_year, 1, 1),
        employee["contract_end_date"] if employee["contract_end_date"] else None
    )
    
    conn.execute(
        "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, ?, ?)",
        (employee_id, to_year, days_at_start, unused_days),
    )
    conn.commit()
    return True


def rollover_all_employees(conn: sqlite3.Connection, from_year: int, to_year: int) -> int:
    """
    Rollover all active employees from one year to the next.
    Returns count of employees processed.
    """
    cur = conn.execute("SELECT id FROM employees WHERE is_active = 1")
    employee_ids = [row[0] for row in cur.fetchall()]
    
    processed_count = 0
    for emp_id in employee_ids:
        if rollover_year_for_employee(conn, emp_id, from_year, to_year):
            processed_count += 1
    
    return processed_count


def is_rollover_complete(conn: sqlite3.Connection, year: int) -> bool:
    """
    Check if all active employees have a year balance record for the given year.
    Returns True if rollover is complete, False otherwise.
    """
    cur = conn.execute("""
        SELECT COUNT(*) FROM employees 
        WHERE is_active = 1 
        AND id NOT IN (
            SELECT employee_id FROM employee_year_balance WHERE year = ?
        )
    """, (year,))
    missing_count = cur.fetchone()[0]
    return missing_count == 0
