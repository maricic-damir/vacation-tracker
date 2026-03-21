"""Query helpers: employee list, details, balances, vacation and earned days."""
import sqlite3
from datetime import date
from typing import Any, Optional


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row) if row else {}


def _rows_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [_row_dict(r) for r in cursor.fetchall()]


# ---------- Employees ----------


def list_employees(conn: sqlite3.Connection) -> list[dict]:
    """All employees with computed total vacation days left (current year)."""
    from database import ensure_year_balance
    cur = conn.execute("""
        SELECT id, jmbg, first_name, last_name, contract_type, contract_end_date, is_active, created_at, updated_at
        FROM employees
        ORDER BY last_name, first_name
    """)
    rows = _rows_dicts(cur)
    year = date.today().year
    for r in rows:
        ensure_year_balance(conn, r["id"], year, r["contract_type"])
        r["contract_end_date"] = r["contract_end_date"] or ""
        r["total_vacation_left"] = total_vacation_left(conn, r["id"], year)
    return rows


def get_employee(conn: sqlite3.Connection, employee_id: int) -> Optional[dict]:
    cur = conn.execute(
        "SELECT id, jmbg, first_name, last_name, contract_type, contract_end_date, is_active, created_at, updated_at FROM employees WHERE id = ?",
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    d = _row_dict(row)
    d["contract_end_date"] = d["contract_end_date"] or ""
    return d


def insert_employee(
    conn: sqlite3.Connection,
    jmbg: str,
    first_name: str,
    last_name: str,
    contract_type: str,
    contract_end_date: Optional[str],
) -> int:
    cur = conn.execute(
        """INSERT INTO employees (jmbg, first_name, last_name, contract_type, contract_end_date, is_active)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (jmbg.strip(), first_name.strip(), last_name.strip(), contract_type, contract_end_date or None),
    )
    eid = cur.lastrowid
    conn.execute("UPDATE employees SET updated_at = datetime('now') WHERE id = ?", (eid,))
    conn.commit()
    return eid


def update_employee_contract(
    conn: sqlite3.Connection,
    employee_id: int,
    contract_type: str,
    contract_end_date: Optional[str],
) -> None:
    conn.execute(
        "UPDATE employees SET contract_type = ?, contract_end_date = ?, updated_at = datetime('now') WHERE id = ?",
        (contract_type, contract_end_date or None, employee_id),
    )
    conn.commit()


def set_employee_active(conn: sqlite3.Connection, employee_id: int, is_active: bool) -> None:
    conn.execute(
        "UPDATE employees SET is_active = ?, updated_at = datetime('now') WHERE id = ?",
        (1 if is_active else 0, employee_id),
    )
    conn.commit()


# ---------- Balance (transferred only until June) ----------


def calculate_deduction_breakdown(
    days_needed: int,
    transferred_available: int,
    at_start_available: int,
    earned_available: int
) -> dict[str, int]:
    """
    Calculate how to deduct days in order: transferred -> at_start -> earned.
    Returns dict with keys: 'transferred', 'at_start', 'earned'
    """
    remaining = days_needed
    from_transferred = min(remaining, transferred_available)
    remaining -= from_transferred
    
    from_at_start = min(remaining, at_start_available)
    remaining -= from_at_start
    
    from_earned = min(remaining, earned_available)
    
    return {
        'transferred': from_transferred,
        'at_start': from_at_start,
        'earned': from_earned
    }


def get_available_days_for_deduction(
    conn: sqlite3.Connection,
    employee_id: int,
    year: int
) -> dict[str, int]:
    """
    Get available days in each bucket for a specific year, accounting for what's already been used.
    Returns dict with keys: 'transferred', 'at_start', 'earned'
    """
    cur = conn.execute(
        "SELECT days_at_start, days_transferred FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    row = cur.fetchone()
    at_start_total = row[0] if row else 0
    transferred_total = row[1] if row else 0
    
    cur = conn.execute(
        "SELECT COALESCE(SUM(number_of_days), 0) FROM earned_days WHERE employee_id = ? AND strftime('%Y', earned_date) = ?",
        (employee_id, str(year)),
    )
    earned_total = cur.fetchone()[0]
    
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    cur = conn.execute(
        """SELECT COALESCE(SUM(days_from_transferred), 0), 
                  COALESCE(SUM(days_from_at_start), 0), 
                  COALESCE(SUM(days_from_earned), 0)
           FROM vacation_records
           WHERE employee_id = ? AND is_completed = 1
           AND (strftime('%Y', start_date) = ? OR strftime('%Y', end_date) = ? OR (start_date <= ? AND end_date >= ?))""",
        (employee_id, str(year), str(year), year_start, year_end)
    )
    used_row = cur.fetchone()
    used_transferred = used_row[0] if used_row else 0
    used_at_start = used_row[1] if used_row else 0
    used_earned = used_row[2] if used_row else 0
    
    return {
        'transferred': max(0, transferred_total - used_transferred),
        'at_start': max(0, at_start_total - used_at_start),
        'earned': max(0, earned_total - used_earned)
    }


def total_vacation_left(conn: sqlite3.Connection, employee_id: int, year: int) -> int:
    """(days_at_start + (transferred if month<=6 else 0) + earned) - used."""
    cur = conn.execute(
        "SELECT days_at_start, days_transferred FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    row = cur.fetchone()
    at_start = row[0] if row else 0
    transferred = row[1] if row else 0
    today = date.today()
    if today.month > 6:
        transferred = 0
    cur = conn.execute(
        "SELECT COALESCE(SUM(number_of_days), 0) FROM earned_days WHERE employee_id = ? AND strftime('%Y', earned_date) = ?",
        (employee_id, str(year)),
    )
    earned = cur.fetchone()[0]
    used = _used_days_in_year(conn, employee_id, year)
    return max(0, at_start + transferred + earned - used)


def _used_days_in_year(conn: sqlite3.Connection, employee_id: int, year: int) -> int:
    """Sum calendar days of completed vacation records overlapping the given year."""
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    cur = conn.execute(
        """SELECT start_date, end_date FROM vacation_records
           WHERE employee_id = ? AND is_completed = 1
           AND (strftime('%Y', start_date) = ? OR strftime('%Y', end_date) = ? OR (start_date <= ? AND end_date >= ?))""",
        (employee_id, str(year), str(year), year_start, year_end),
    )
    total = 0
    y_start = date(year, 1, 1)
    y_end = date(year, 12, 31)
    for start_s, end_s in cur.fetchall():
        start = date.fromisoformat(start_s)
        end = date.fromisoformat(end_s)
        overlap_start = max(start, y_start)
        overlap_end = min(end, y_end)
        if overlap_start <= overlap_end:
            total += (overlap_end - overlap_start).days + 1
    return total


def set_days_at_start(conn: sqlite3.Connection, employee_id: int, year: int, days: int) -> None:
    """Set days at start for the given employee and year (e.g. for fixed-term contracts)."""
    cur = conn.execute(
        "UPDATE employee_year_balance SET days_at_start = ? WHERE employee_id = ? AND year = ?",
        (days, employee_id, year),
    )
    if cur.rowcount == 0:
        conn.execute(
            "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, ?, 0)",
            (employee_id, year, days),
        )
    conn.commit()


def set_transferred_days(conn: sqlite3.Connection, employee_id: int, year: int, days: int) -> None:
    """Set days transferred from previous year for the given employee and year."""
    cur = conn.execute(
        "UPDATE employee_year_balance SET days_transferred = ? WHERE employee_id = ? AND year = ?",
        (days, employee_id, year),
    )
    if cur.rowcount == 0:
        conn.execute(
            "INSERT INTO employee_year_balance (employee_id, year, days_at_start, days_transferred) VALUES (?, ?, 0, ?)",
            (employee_id, year, days),
        )
    conn.commit()


def get_year_balance(conn: sqlite3.Connection, employee_id: int, year: int) -> dict:
    cur = conn.execute(
        "SELECT days_at_start, days_transferred FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    row = cur.fetchone()
    at_start = row[0] if row else 0
    transferred = row[1] if row else 0
    cur = conn.execute(
        "SELECT COALESCE(SUM(number_of_days), 0) FROM earned_days WHERE employee_id = ? AND strftime('%Y', earned_date) = ?",
        (employee_id, str(year)),
    )
    earned = cur.fetchone()[0]
    
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    cur = conn.execute(
        """SELECT COALESCE(SUM(days_from_transferred), 0), 
                  COALESCE(SUM(days_from_at_start), 0), 
                  COALESCE(SUM(days_from_earned), 0)
           FROM vacation_records
           WHERE employee_id = ? AND is_completed = 1
           AND (strftime('%Y', start_date) = ? OR strftime('%Y', end_date) = ? OR (start_date <= ? AND end_date >= ?))""",
        (employee_id, str(year), str(year), year_start, year_end)
    )
    used_row = cur.fetchone()
    used_transferred = used_row[0] if used_row else 0
    used_at_start = used_row[1] if used_row else 0
    used_earned = used_row[2] if used_row else 0
    
    used_total = used_transferred + used_at_start + used_earned
    
    transferred_left = max(0, transferred - used_transferred)
    at_start_left = max(0, at_start - used_at_start)
    earned_left = max(0, earned - used_earned)
    
    if date.today().month > 6:
        days_left = at_start_left + earned_left
    else:
        days_left = transferred_left + at_start_left + earned_left
    
    return {
        "year": year,
        "days_at_start": at_start,
        "days_transferred": transferred,
        "days_earned": earned,
        "days_used": used_total,
        "days_left": days_left,
        "transferred_left": transferred_left,
        "at_start_left": at_start_left,
        "earned_left": earned_left,
    }


# ---------- Earned days ----------


def list_earned_days(conn: sqlite3.Connection, employee_id: int) -> list[dict]:
    cur = conn.execute(
        "SELECT id, earned_date, number_of_days, reason_notes, created_at FROM earned_days WHERE employee_id = ? ORDER BY earned_date DESC",
        (employee_id,),
    )
    return _rows_dicts(cur)


def add_earned_days(
    conn: sqlite3.Connection,
    employee_id: int,
    earned_date: str,
    number_of_days: int,
    reason_notes: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO earned_days (employee_id, earned_date, number_of_days, reason_notes) VALUES (?, ?, ?, ?)",
        (employee_id, earned_date, number_of_days, (reason_notes or "").strip()),
    )
    conn.commit()
    return cur.lastrowid


# ---------- Vacation records ----------


def list_vacation_records_employee(conn: sqlite3.Connection, employee_id: int) -> list[dict]:
    cur = conn.execute(
        """SELECT id, booking_date, start_date, end_date, is_completed, created_at
           FROM vacation_records WHERE employee_id = ? ORDER BY start_date DESC""",
        (employee_id,),
    )
    return _rows_dicts(cur)


def list_vacation_records_all(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute("""
        SELECT v.id, e.jmbg, e.first_name, e.last_name, v.booking_date, v.start_date, v.end_date, v.is_completed, v.created_at
        FROM vacation_records v
        JOIN employees e ON e.id = v.employee_id
        ORDER BY v.start_date DESC
    """)
    return _rows_dicts(cur)


def add_vacation_record(
    conn: sqlite3.Connection,
    employee_id: int,
    booking_date: str,
    start_date: str,
    end_date: str,
    is_completed: bool = False,
    days_from_transferred: int = 0,
    days_from_at_start: int = 0,
    days_from_earned: int = 0,
) -> int:
    cur = conn.execute(
        """INSERT INTO vacation_records (employee_id, booking_date, start_date, end_date, is_completed,
                                          days_from_transferred, days_from_at_start, days_from_earned)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (employee_id, booking_date, start_date, end_date, 1 if is_completed else 0,
         days_from_transferred, days_from_at_start, days_from_earned),
    )
    conn.commit()
    return cur.lastrowid


def count_days_in_range(start_date: str, end_date: str) -> int:
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    return (e - s).days + 1
