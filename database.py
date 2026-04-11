"""SQLite schema, connection, and DB path resolution (find or create)."""
import sqlite3
from datetime import date
from pathlib import Path
from typing import Callable, Optional

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
    religion TEXT NOT NULL DEFAULT 'orthodox' CHECK (religion IN ('orthodox', 'catholic')),
    working_days_per_week INTEGER NOT NULL DEFAULT 6 CHECK (working_days_per_week IN (5, 6)),
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

-- Non-working days (public holidays)
CREATE TABLE IF NOT EXISTS non_working_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    name_sr TEXT NOT NULL,
    name_en TEXT,
    holiday_type TEXT NOT NULL CHECK (holiday_type IN ('state', 'orthodox', 'catholic', 'other_religious')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Special leave types (child birth, wedding, etc.)
CREATE TABLE IF NOT EXISTS special_leave_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_en TEXT NOT NULL,
    name_sr TEXT NOT NULL,
    days_entitled INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Special leave usage tracking
CREATE TABLE IF NOT EXISTS special_leave_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    special_leave_type_id INTEGER NOT NULL REFERENCES special_leave_types(id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,
    days_used INTEGER NOT NULL,
    reason_notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_vacation_employee ON vacation_records(employee_id);
CREATE INDEX IF NOT EXISTS ix_vacation_dates ON vacation_records(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_earned_employee ON earned_days(employee_id);
CREATE INDEX IF NOT EXISTS ix_earned_date ON earned_days(earned_date);
CREATE INDEX IF NOT EXISTS ix_non_working_date ON non_working_days(date);
CREATE INDEX IF NOT EXISTS ix_non_working_active ON non_working_days(is_active);
CREATE INDEX IF NOT EXISTS ix_special_leave_usage_employee ON special_leave_usage(employee_id);
CREATE INDEX IF NOT EXISTS ix_special_leave_usage_type ON special_leave_usage(special_leave_type_id);
CREATE INDEX IF NOT EXISTS ix_special_leave_usage_date ON special_leave_usage(usage_date);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    migrate_add_deduction_tracking(conn)
    migrate_add_non_working_days(conn)
    migrate_add_religion(conn)
    migrate_add_start_contract_date(conn)
    migrate_add_special_leave_tables(conn)
    migrate_add_working_days_per_week(conn)
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
    from db_helpers import count_days_in_range, calculate_deduction_breakdown, count_total_deductible_days
    
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
                
                days_needed = count_total_deductible_days(conn, start_date, end_date, employee_id)
                
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

def resolve_db_path(
    choose_or_create_callback,
    locate_callback,
    missing_saved_path_callback: Optional[Callable[[str], Optional[str]]] = None,
) -> Optional[str]:
    """
    Use saved path if valid. If no path or file missing:
    - First time (no saved db_path in config): choose_or_create_callback() -> user picks path for new DB.
    - Config had db_path but file missing: missing_saved_path_callback(saved_path) if provided,
      else locate_callback() -> user locates an existing file.
    Returns None if user cancelled.
    """
    saved = get_db_path()
    if saved:
        return saved
    # App was run before on this machine if we have a saved path (even invalid)
    raw_saved = get_saved_db_path_raw()
    had_saved_path = raw_saved is not None
    if had_saved_path:
        if missing_saved_path_callback and raw_saved:
            path = missing_saved_path_callback(raw_saved)
        else:
            path = locate_callback()
    else:
        path = choose_or_create_callback()
    if path:
        set_db_path(path)
    return path


def ensure_year_balance(conn: sqlite3.Connection, employee_id: int, year: int, contract_type: str) -> None:
    """Create employee_year_balance for this year if missing. Open-ended gets days based on working days per week."""
    cur = conn.execute(
        "SELECT 1 FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    if cur.fetchone():
        return
    
    # Get employee's working days per week to determine days_at_start for open-ended contracts
    if contract_type == "open_ended":
        cur = conn.execute("SELECT working_days_per_week FROM employees WHERE id = ?", (employee_id,))
        row = cur.fetchone()
        working_days_per_week = row[0] if row else 6  # Default to 6 for backwards compatibility
        days_at_start = 20 if working_days_per_week == 5 else 24
    else:
        days_at_start = 0
    
    conn.execute(
        "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, ?, 0)",
        (employee_id, year, days_at_start),
    )
    conn.commit()


def run_completion_job(conn: sqlite3.Connection) -> None:
    """Mark vacation_records as completed where end_date < today and calculate deduction breakdown."""
    from db_helpers import (get_available_days_for_deduction, calculate_deduction_breakdown, 
                           count_total_deductible_days, calculate_multi_year_vacation_requirements)
    
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
        
        # Handle multi-year vacations properly
        start_dt = date.fromisoformat(start_date)
        end_dt = date.fromisoformat(end_date)
        
        if start_dt.year == end_dt.year:
            # Single year vacation - use existing logic
            year = start_dt.year
            days_needed = count_total_deductible_days(conn, start_date, end_date, employee_id)
            
            available = get_available_days_for_deduction(conn, employee_id, year)
            breakdown = calculate_deduction_breakdown(
                days_needed,
                available['transferred'],
                available['at_start'],
                available['earned']
            )
        else:
            # Multi-year vacation - calculate breakdown across years
            # For now, we'll use a simplified approach: deduct from the start year
            # This could be enhanced to properly distribute across years in the future
            year = start_dt.year
            days_needed = count_total_deductible_days(conn, start_date, end_date, employee_id)
            
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
    
    IMPORTANT BUSINESS RULES:
    - Regular vacation days: Unused days are transferred to the new year
    - Special leave entitlements: RESET to full entitlement (no transfer)
    
    Special leave policy: Special leave entitlements are completely reset each year.
    Unused special leave days cannot be transferred and are lost at year-end.
    Each employee gets their full special leave entitlement renewed each January 1st.
    
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
    
    # Handle regular vacation days rollover (existing logic)
    balance = get_year_balance(conn, employee_id, from_year)
    
    unused_days = balance["transferred_left"] + balance["at_start_left"] + balance["earned_left"]
    
    days_at_start = prorated_vacation_entitlement_for_year(
        date(to_year, 1, 1),
        employee["contract_end_date"] if employee["contract_end_date"] else None,
        employee.get("working_days_per_week", 6)
    )
    
    conn.execute(
        "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, ?, ?)",
        (employee_id, to_year, days_at_start, unused_days),
    )
    
    # Handle special leave reset (NEW FUNCTIONALITY)
    # Special leave entitlements are reset each year - unused days are NOT transferred
    # This ensures employees get their full special leave entitlement renewed annually
    reset_special_leave_for_employee(conn, employee_id, from_year, to_year)
    
    conn.commit()
    return True


def rollover_all_employees(conn: sqlite3.Connection, from_year: int, to_year: int) -> int:
    """
    Rollover all active employees from one year to the next.
    
    This function handles both regular vacation rollover and special leave reset.
    Returns count of employees processed.
    """
    cur = conn.execute("SELECT id FROM employees WHERE is_active = 1")
    employee_ids = [row[0] for row in cur.fetchall()]
    
    processed_count = 0
    for emp_id in employee_ids:
        if rollover_year_for_employee(conn, emp_id, from_year, to_year):
            processed_count += 1
    
    return processed_count


def reset_special_leave_for_employee(conn: sqlite3.Connection, employee_id: int, from_year: int, to_year: int) -> None:
    """
    Reset special leave entitlements for an employee during year rollover.
    
    BUSINESS RULE: Special leave entitlements are completely reset each year.
    - Unused special leave days from the previous year are lost (not transferred)
    - Each employee gets their full special leave entitlement renewed for the new year
    - This is different from regular vacation days which can be transferred
    
    This function does NOT delete historical usage records - it simply ensures
    that the employee gets their full entitlement for the new year regardless
    of how much they used in the previous year.
    
    Args:
        conn: Database connection
        employee_id: ID of the employee
        from_year: Previous year (for logging/audit purposes)
        to_year: New year (when entitlements are reset)
    """
    # Note: We don't need to do anything special here because the special leave
    # system already works on a per-year basis. The get_special_leave_balance_for_employee()
    # function calculates available days by subtracting usage from entitlements
    # for each year independently.
    #
    # The "reset" happens naturally because:
    # 1. Each year's usage is tracked separately by date
    # 2. Entitlements are global (not year-specific)
    # 3. Available days = entitlement - usage_for_current_year
    #
    # So when we move to a new year, usage_for_current_year starts at 0,
    # giving the employee their full entitlement again.
    
    # Optional: Log the reset for audit purposes
    # This could be useful for tracking when rollovers occurred
    pass  # No action needed - reset happens automatically due to year-based calculations


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


def migrate_add_non_working_days(conn: sqlite3.Connection) -> None:
    """Add non_working_days table if it doesn't exist."""
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='non_working_days'")
    if cur.fetchone():
        return
    # Table will be created by SCHEMA, so just run recalculation
    recalculate_all_vacation_records_with_working_days(conn)


def migrate_add_religion(conn: sqlite3.Connection) -> None:
    """Add religion column to employees table if it doesn't exist."""
    cur = conn.execute("PRAGMA table_info(employees)")
    columns = {row[1] for row in cur.fetchall()}
    
    if "religion" not in columns:
        # Add religion column with default 'orthodox' for existing employees
        conn.execute("ALTER TABLE employees ADD COLUMN religion TEXT NOT NULL DEFAULT 'orthodox' CHECK (religion IN ('orthodox', 'catholic'))")
        conn.commit()
        # Recalculate all vacation records with new religion-based filtering
        recalculate_all_vacation_records_with_working_days(conn)


def migrate_add_start_contract_date(conn: sqlite3.Connection) -> None:
    """Add start_contract_date column to employees table if it doesn't exist."""
    cur = conn.execute("PRAGMA table_info(employees)")
    columns = {row[1] for row in cur.fetchall()}
    
    if "start_contract_date" not in columns:
        conn.execute("ALTER TABLE employees ADD COLUMN start_contract_date DATE NULL")
        conn.commit()


def migrate_add_special_leave_tables(conn: sqlite3.Connection) -> None:
    """Add special leave tables if they don't exist and populate with default types."""
    # Check if we already have data in the table
    cur = conn.execute("SELECT COUNT(*) FROM special_leave_types")
    count = cur.fetchone()[0]
    if count > 0:
        return  # Data already exists
    
    # Populate with default types
    default_types = [
        {"name_en": "Child birth", "name_sr": "Рођење детета", "days_entitled": 7},
        {"name_en": "Wedding", "name_sr": "Венчање", "days_entitled": 7},
        {"name_en": "Moving", "name_sr": "Селидба", "days_entitled": 2},
        {"name_en": "Death of a member of a wider family", "name_sr": "Смрт члана шире породице", "days_entitled": 1},
        {"name_en": "Deaths of a member of the immediate family and members of the household", "name_sr": "Смрт члана уже породице и домаћинства", "days_entitled": 3},
    ]
    
    for leave_type in default_types:
        conn.execute("""
            INSERT INTO special_leave_types (name_en, name_sr, days_entitled, is_active)
            VALUES (?, ?, ?, 1)
        """, (leave_type["name_en"], leave_type["name_sr"], leave_type["days_entitled"]))
    
    conn.commit()


def migrate_add_working_days_per_week(conn: sqlite3.Connection) -> None:
    """Add working_days_per_week column to employees table if it doesn't exist."""
    cur = conn.execute("PRAGMA table_info(employees)")
    columns = {row[1] for row in cur.fetchall()}
    
    if "working_days_per_week" not in columns:
        # Add working_days_per_week column with default 6 for existing employees
        conn.execute("ALTER TABLE employees ADD COLUMN working_days_per_week INTEGER NOT NULL DEFAULT 6 CHECK (working_days_per_week IN (5, 6))")
        conn.commit()


def recalculate_all_vacation_records_with_working_days(conn: sqlite3.Connection) -> None:
    """
    Recalculate all completed vacation records using working days logic.
    This is run during migration to update existing data.
    """
    from db_helpers import count_working_days_in_range, calculate_deduction_breakdown, count_total_deductible_days
    
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
                
                days_needed = count_total_deductible_days(conn, start_date, end_date, employee_id)
                
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


# ---------------------------------------------------------------------------
# Non-working days CRUD
# ---------------------------------------------------------------------------

def get_non_working_days(conn: sqlite3.Connection, year: Optional[int] = None) -> list[dict]:
    """
    Get non-working days for a specific year or all years.
    Returns list of dicts with keys: id, date, name_sr, name_en, holiday_type, is_active
    """
    if year:
        cur = conn.execute("""
            SELECT id, date, name_sr, name_en, holiday_type, is_active, created_at, updated_at
            FROM non_working_days
            WHERE strftime('%Y', date) = ? AND is_active = 1
            ORDER BY date
        """, (str(year),))
    else:
        cur = conn.execute("""
            SELECT id, date, name_sr, name_en, holiday_type, is_active, created_at, updated_at
            FROM non_working_days
            WHERE is_active = 1
            ORDER BY date
        """)
    return [dict(row) for row in cur.fetchall()]


def is_non_working_day(conn: sqlite3.Connection, check_date: str) -> bool:
    """Check if a date is a non-working day (holiday)."""
    cur = conn.execute(
        "SELECT 1 FROM non_working_days WHERE date = ? AND is_active = 1",
        (check_date,)
    )
    return cur.fetchone() is not None


def is_non_working_day_for_employee(conn: sqlite3.Connection, check_date: str, employee_id: int) -> bool:
    """
    Check if a date is a non-working day for a specific employee.
    State holidays apply to everyone.
    Religious holidays (orthodox/catholic) only apply to employees of that religion.
    """
    # Get employee's religion
    cur = conn.execute("SELECT religion FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    if not row:
        return False
    
    employee_religion = row[0]
    
    # Check if date is a holiday
    cur = conn.execute(
        "SELECT holiday_type FROM non_working_days WHERE date = ? AND is_active = 1",
        (check_date,)
    )
    row = cur.fetchone()
    
    if not row:
        return False
    
    holiday_type = row[0]
    
    # State holidays apply to everyone
    if holiday_type == 'state':
        return True
    
    # Religious holidays only apply if they match employee's religion
    if holiday_type == 'orthodox' and employee_religion == 'orthodox':
        return True
    
    if holiday_type == 'catholic' and employee_religion == 'catholic':
        return True
    
    # 'other_religious' holidays don't apply to orthodox or catholic employees
    return False


def save_non_working_days(conn: sqlite3.Connection, holidays: list[dict]) -> int:
    """
    Bulk insert/update holidays.
    Each dict should have: date, name_sr, name_en, holiday_type
    Returns count of holidays saved.
    """
    count = 0
    for holiday in holidays:
        cur = conn.execute(
            "SELECT id FROM non_working_days WHERE date = ?",
            (holiday['date'],)
        )
        existing = cur.fetchone()
        
        if existing:
            conn.execute("""
                UPDATE non_working_days 
                SET name_sr = ?, name_en = ?, holiday_type = ?, is_active = 1, updated_at = datetime('now')
                WHERE date = ?
            """, (holiday['name_sr'], holiday.get('name_en', ''), holiday['holiday_type'], holiday['date']))
        else:
            conn.execute("""
                INSERT INTO non_working_days (date, name_sr, name_en, holiday_type, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (holiday['date'], holiday['name_sr'], holiday.get('name_en', ''), holiday['holiday_type']))
        count += 1
    
    conn.commit()
    return count


def delete_non_working_day(conn: sqlite3.Connection, holiday_id: int) -> None:
    """Delete a holiday by ID."""
    conn.execute("DELETE FROM non_working_days WHERE id = ?", (holiday_id,))
    conn.commit()


def clear_non_working_days(conn: sqlite3.Connection, year: int) -> int:
    """
    Clear all holidays for a specific year.
    Returns count of holidays deleted.
    """
    cur = conn.execute("""
        DELETE FROM non_working_days 
        WHERE strftime('%Y', date) = ?
    """, (str(year),))
    count = cur.rowcount
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Special leave CRUD
# ---------------------------------------------------------------------------

def get_special_leave_types(conn: sqlite3.Connection) -> list[dict]:
    """
    Get all active special leave types.
    
    IMPORTANT: Special leave entitlements are reset annually and cannot be transferred.
    Unlike regular vacation days, unused special leave days are lost at year-end.
    
    Returns list of dicts with keys: id, name_en, name_sr, days_entitled
    """
    cur = conn.execute("""
        SELECT id, name_en, name_sr, days_entitled
        FROM special_leave_types
        WHERE is_active = 1
        ORDER BY id
    """)
    return [dict(row) for row in cur.fetchall()]


def get_special_leave_usage_for_employee(conn: sqlite3.Connection, employee_id: int, year: Optional[int] = None) -> list[dict]:
    """
    Get special leave usage for an employee, optionally filtered by year.
    Returns list of dicts with keys: id, special_leave_type_id, usage_date, days_used, reason_notes, type_name_en, type_name_sr
    """
    if year:
        cur = conn.execute("""
            SELECT slu.id, slu.special_leave_type_id, slu.usage_date, slu.days_used, slu.reason_notes,
                   slt.name_en as type_name_en, slt.name_sr as type_name_sr
            FROM special_leave_usage slu
            JOIN special_leave_types slt ON slu.special_leave_type_id = slt.id
            WHERE slu.employee_id = ? AND strftime('%Y', slu.usage_date) = ?
            ORDER BY slu.usage_date DESC
        """, (employee_id, str(year)))
    else:
        cur = conn.execute("""
            SELECT slu.id, slu.special_leave_type_id, slu.usage_date, slu.days_used, slu.reason_notes,
                   slt.name_en as type_name_en, slt.name_sr as type_name_sr
            FROM special_leave_usage slu
            JOIN special_leave_types slt ON slu.special_leave_type_id = slt.id
            WHERE slu.employee_id = ?
            ORDER BY slu.usage_date DESC
        """, (employee_id,))
    return [dict(row) for row in cur.fetchall()]


def get_special_leave_balance_for_employee(conn: sqlite3.Connection, employee_id: int, year: int) -> dict:
    """
    Calculate special leave balance for an employee for a specific year.
    
    BUSINESS RULE: Special leave entitlements reset annually (January 1st).
    - Each year, employees get their full special leave entitlement
    - Unused days from previous years are NOT carried over
    - Balance = full_entitlement - usage_in_current_year_only
    
    This is different from regular vacation days which can be transferred between years.
    
    Returns dict with leave type IDs as keys and balance info as values.
    Each value contains: 'entitled', 'used', 'remaining'
    """
    # Get all leave types
    leave_types = get_special_leave_types(conn)
    
    # Get usage for this year
    usage = get_special_leave_usage_for_employee(conn, employee_id, year)
    
    # Calculate balances
    balances = {}
    for leave_type in leave_types:
        type_id = leave_type['id']
        entitled = leave_type['days_entitled']
        
        # Sum usage for this type in this year
        used = sum(u['days_used'] for u in usage if u['special_leave_type_id'] == type_id)
        
        balances[type_id] = {
            'type_name_en': leave_type['name_en'],
            'type_name_sr': leave_type['name_sr'],
            'entitled': entitled,
            'used': used,
            'remaining': max(0, entitled - used)
        }
    
    return balances


def add_special_leave_usage(conn: sqlite3.Connection, employee_id: int, special_leave_type_id: int, 
                           usage_date: str, days_used: int, reason_notes: str = "") -> int:
    """
    Add special leave usage record.
    
    IMPORTANT: Special leave is tracked separately from regular vacation days.
    - Special leave does NOT reduce regular vacation balance
    - Special leave entitlements reset annually (no carryover)
    - Usage is tracked per year based on usage_date
    
    Returns the ID of the created record.
    """
    cur = conn.execute("""
        INSERT INTO special_leave_usage (employee_id, special_leave_type_id, usage_date, days_used, reason_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, special_leave_type_id, usage_date, days_used, reason_notes))
    
    record_id = cur.lastrowid
    conn.commit()
    return record_id


def delete_special_leave_usage(conn: sqlite3.Connection, usage_id: int) -> None:
    """Delete a special leave usage record by ID."""
    conn.execute("DELETE FROM special_leave_usage WHERE id = ?", (usage_id,))
    conn.commit()


def update_special_leave_entitlement(conn: sqlite3.Connection, type_id: int, days_entitled: int) -> None:
    """Update the days entitled for a special leave type."""
    conn.execute("""
        UPDATE special_leave_types 
        SET days_entitled = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (days_entitled, type_id))
    conn.commit()
