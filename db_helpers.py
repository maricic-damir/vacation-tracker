"""Query helpers: employee list, details, balances, vacation and earned days."""
import sqlite3
from datetime import date
from typing import Any, Optional, List, Dict


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row) if row else {}


def _rows_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [_row_dict(r) for r in cursor.fetchall()]


# ---------- Employees ----------


def list_employees(conn: sqlite3.Connection) -> list[dict]:
    """All employees with computed total vacation days left (current year)."""
    from database import ensure_year_balance
    cur = conn.execute("""
        SELECT id, jmbg, first_name, last_name, contract_type, contract_end_date, start_contract_date, is_active, created_at, updated_at
        FROM employees
        ORDER BY last_name, first_name
    """)
    rows = _rows_dicts(cur)
    year = date.today().year
    for r in rows:
        ensure_year_balance(conn, r["id"], year, r["contract_type"])
        r["contract_end_date"] = r["contract_end_date"] or ""
        r["start_contract_date"] = r.get("start_contract_date") or ""
        r["total_vacation_left"] = total_vacation_left(conn, r["id"], year)
    return rows


def get_employee(conn: sqlite3.Connection, employee_id: int) -> Optional[dict]:
    cur = conn.execute(
        """SELECT id, jmbg, first_name, last_name, contract_type, contract_end_date, religion,
                  start_contract_date, working_days_per_week, is_active, created_at, updated_at
           FROM employees WHERE id = ?""",
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    d = _row_dict(row)
    d["contract_end_date"] = d["contract_end_date"] or ""
    d["start_contract_date"] = d.get("start_contract_date") or ""
    return d


def insert_employee(
    conn: sqlite3.Connection,
    jmbg: str,
    first_name: str,
    last_name: str,
    contract_type: str,
    contract_end_date: Optional[str],
    religion: str = 'orthodox',
    start_contract_date: Optional[str] = None,
    working_days_per_week: int = 6,
) -> int:
    cur = conn.execute(
        """INSERT INTO employees (jmbg, first_name, last_name, contract_type, contract_end_date, religion, start_contract_date, working_days_per_week, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (jmbg.strip(), first_name.strip(), last_name.strip(), contract_type, contract_end_date or None, religion, start_contract_date or None, working_days_per_week),
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
    religion: Optional[str] = None,
    working_days_per_week: Optional[int] = None,
    start_contract_date: Optional[str] = None,
) -> None:
    # Use the original logic pattern but extend for start_contract_date
    base_fields = "contract_type = ?, contract_end_date = ?, updated_at = datetime('now')"
    base_params = [contract_type, contract_end_date or None]
    
    # Build query based on which optional parameters are provided (using original truthiness logic)
    if religion and working_days_per_week and start_contract_date:
        query = f"UPDATE employees SET {base_fields}, religion = ?, working_days_per_week = ?, start_contract_date = ? WHERE id = ?"
        params = base_params + [religion, working_days_per_week, start_contract_date, employee_id]
    elif religion and working_days_per_week:
        query = f"UPDATE employees SET {base_fields}, religion = ?, working_days_per_week = ? WHERE id = ?"
        params = base_params + [religion, working_days_per_week, employee_id]
    elif religion and start_contract_date:
        query = f"UPDATE employees SET {base_fields}, religion = ?, start_contract_date = ? WHERE id = ?"
        params = base_params + [religion, start_contract_date, employee_id]
    elif working_days_per_week and start_contract_date:
        query = f"UPDATE employees SET {base_fields}, working_days_per_week = ?, start_contract_date = ? WHERE id = ?"
        params = base_params + [working_days_per_week, start_contract_date, employee_id]
    elif religion:
        query = f"UPDATE employees SET {base_fields}, religion = ? WHERE id = ?"
        params = base_params + [religion, employee_id]
    elif working_days_per_week:
        query = f"UPDATE employees SET {base_fields}, working_days_per_week = ? WHERE id = ?"
        params = base_params + [working_days_per_week, employee_id]
    elif start_contract_date:
        query = f"UPDATE employees SET {base_fields}, start_contract_date = ? WHERE id = ?"
        params = base_params + [start_contract_date, employee_id]
    else:
        query = f"UPDATE employees SET {base_fields} WHERE id = ?"
        params = base_params + [employee_id]
    
    conn.execute(query, params)
    conn.commit()


def apply_prorated_days_from_contract_update(
    conn: sqlite3.Connection,
    employee_id: int,
    prorated_results: List[Dict[str, any]]
) -> None:
    """
    Apply prorated days calculations from contract update to employee year balances.
    
    Args:
        conn: Database connection
        employee_id: Employee ID
        prorated_results: List of prorated calculation results from entitlement module
    """
    for result in prorated_results:
        year = result["year"]
        additional_days = result["days"]
        
        if additional_days > 0:
            # Get current balance for the year
            current_balance = get_year_balance(conn, employee_id, year)
            current_days_at_start = current_balance.get("days_at_start", 0)
            
            # Add the prorated days to the current balance
            new_days_at_start = current_days_at_start + additional_days
            set_days_at_start(conn, employee_id, year, new_days_at_start)


def set_employee_active(conn: sqlite3.Connection, employee_id: int, is_active: bool) -> None:
    conn.execute(
        "UPDATE employees SET is_active = ?, updated_at = datetime('now') WHERE id = ?",
        (1 if is_active else 0, employee_id),
    )
    conn.commit()


# ---------- Balance (transferred until end of year) ----------


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


def get_available_days_for_scheduling(
    conn: sqlite3.Connection,
    employee_id: int,
    year: int,
    exclude_record_id: Optional[int] = None
) -> dict[str, int]:
    """
    Get available days for scheduling new vacation, accounting for both completed 
    and planned (not completed) vacation records that reserve days.
    Returns dict with keys: 'transferred', 'at_start', 'earned', 'reserved_days'
    """
    # Get base available days (only accounting for completed vacations)
    available = get_available_days_for_deduction(conn, employee_id, year)
    
    # Calculate reserved days from planned (not completed) vacations
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    
    query = """
        SELECT start_date, end_date 
        FROM vacation_records
        WHERE employee_id = ? AND is_completed = 0
        AND (strftime('%Y', start_date) = ? OR strftime('%Y', end_date) = ? OR (start_date <= ? AND end_date >= ?))
    """
    params = [employee_id, str(year), str(year), year_start, year_end]
    
    if exclude_record_id is not None:
        query += " AND id != ?"
        params.append(exclude_record_id)
    
    cur = conn.execute(query, params)
    
    total_reserved_days = 0
    for start_s, end_s in cur.fetchall():
        # Calculate overlap with the target year for multi-year periods
        start = date.fromisoformat(start_s)
        end = date.fromisoformat(end_s)
        y_start = date(year, 1, 1)
        y_end = date(year, 12, 31)
        
        overlap_start = max(start, y_start)
        overlap_end = min(end, y_end)
        
        if overlap_start <= overlap_end:
            reserved_days = count_total_deductible_days(conn, overlap_start.isoformat(), overlap_end.isoformat(), employee_id)
            total_reserved_days += reserved_days
    
    # Calculate how reserved days would be deducted using the same priority order
    reserved_breakdown = calculate_deduction_breakdown(
        total_reserved_days,
        available['transferred'],
        available['at_start'],
        available['earned']
    )
    
    # Subtract reserved days from available buckets
    result = {
        'transferred': max(0, available['transferred'] - reserved_breakdown['transferred']),
        'at_start': max(0, available['at_start'] - reserved_breakdown['at_start']),
        'earned': max(0, available['earned'] - reserved_breakdown['earned']),
        'reserved_days': total_reserved_days
    }
    
    return result


def total_vacation_left(conn: sqlite3.Connection, employee_id: int, year: int) -> int:
    """(days_at_start + (transferred if before end of year else 0) + earned) - used."""
    cur = conn.execute(
        "SELECT days_at_start, days_transferred FROM employee_year_balance WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    )
    row = cur.fetchone()
    at_start = row[0] if row else 0
    transferred = row[1] if row else 0
    today = date.today()
    # Transferred days are valid until December 31 of the year they belong to
    if today > date(year, 12, 31):
        transferred = 0
    cur = conn.execute(
        "SELECT COALESCE(SUM(number_of_days), 0) FROM earned_days WHERE employee_id = ? AND strftime('%Y', earned_date) = ?",
        (employee_id, str(year)),
    )
    earned = cur.fetchone()[0]
    used = _used_days_in_year(conn, employee_id, year)
    return max(0, at_start + transferred + earned - used)


def _used_days_in_year(conn: sqlite3.Connection, employee_id: int, year: int) -> int:
    """Sum deductible days (working days + weekend days excluding holidays) of completed vacation records overlapping the given year."""
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
            total += count_total_deductible_days(conn, overlap_start.isoformat(), overlap_end.isoformat(), employee_id)
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
    
    # Transferred days are valid until December 31 of the year they belong to
    today = date.today()
    if today > date(year, 12, 31):
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
        """SELECT id, booking_date, start_date, end_date, is_completed,
                  days_from_transferred, days_from_at_start, days_from_earned, created_at
           FROM vacation_records WHERE employee_id = ? ORDER BY start_date DESC""",
        (employee_id,),
    )
    return _rows_dicts(cur)


def vacation_days_for_used_table(conn: sqlite3.Connection, employee_id: int, row: dict) -> int:
    """Deducted days for completed records (stored breakdown); otherwise deductible days for the range."""
    if row.get("is_completed"):
        s = (
            int(row.get("days_from_transferred") or 0)
            + int(row.get("days_from_at_start") or 0)
            + int(row.get("days_from_earned") or 0)
        )
        if s > 0:
            return s
    return count_total_deductible_days(conn, row["start_date"], row["end_date"], employee_id)


def list_vacation_records_all(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute("""
        SELECT v.id, e.jmbg, e.first_name, e.last_name, v.booking_date, v.start_date, v.end_date, v.is_completed, v.created_at
        FROM vacation_records v
        JOIN employees e ON e.id = v.employee_id
        ORDER BY v.start_date DESC
    """)
    return _rows_dicts(cur)


def check_vacation_overlap(
    conn: sqlite3.Connection,
    employee_id: int,
    start_date: str,
    end_date: str,
    exclude_record_id: Optional[int] = None
) -> list[dict]:
    """
    Check for overlapping vacation records for the given employee and date range.
    Returns list of overlapping records with their details.
    """
    query = """
        SELECT id, start_date, end_date, is_completed, booking_date
        FROM vacation_records 
        WHERE employee_id = ? 
        AND (
            (start_date <= ? AND end_date >= ?) OR
            (start_date <= ? AND end_date >= ?) OR
            (start_date >= ? AND end_date <= ?)
        )
    """
    params = [employee_id, start_date, start_date, end_date, end_date, start_date, end_date]
    
    if exclude_record_id is not None:
        query += " AND id != ?"
        params.append(exclude_record_id)
    
    cur = conn.execute(query, params)
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


def delete_vacation_record(conn: sqlite3.Connection, record_id: int) -> bool:
    """
    Delete a vacation record by ID. Returns True if record was deleted, False if not found.
    Should only be used for scheduled (not completed) vacation records.
    """
    cur = conn.execute("DELETE FROM vacation_records WHERE id = ?", (record_id,))
    deleted = cur.rowcount > 0
    if deleted:
        conn.commit()
    return deleted


def can_cancel_vacation_record(vacation_record: dict) -> bool:
    """
    Check if a vacation record can be cancelled.
    Only scheduled (not completed) vacations that haven't started yet can be cancelled.
    """
    if vacation_record.get('is_completed'):
        return False
    
    start_date_str = vacation_record.get('start_date')
    if not start_date_str:
        return False
    
    start_date = date.fromisoformat(start_date_str)
    return start_date > date.today()


def count_days_in_range(start_date: str, end_date: str) -> int:
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    return (e - s).days + 1


def count_working_days_in_range(conn: sqlite3.Connection, start_date: str, end_date: str, employee_id: int) -> int:
    """
    Count working days between start and end dates (inclusive).
    Excludes weekends and non-working days from database based on employee's working schedule.
    
    For 5-day work week: Excludes Saturday and Sunday
    For 6-day work week: Excludes only Sunday
    
    Filters holidays based on employee's religion:
    - State holidays apply to everyone
    - Orthodox holidays apply only to Orthodox employees
    - Catholic holidays apply only to Catholic employees
    """
    from database import is_non_working_day_for_employee
    
    # Get employee's working days per week
    cur = conn.execute("SELECT working_days_per_week FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    working_days_per_week = row[0] if row else 6  # Default to 6 for backwards compatibility
    
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    
    working_days = 0
    current = s
    
    while current <= e:
        # Check if it's a weekend based on employee's working schedule
        is_weekend = False
        if working_days_per_week == 5:
            # 5-day work week: Saturday (5) and Sunday (6) are weekends
            is_weekend = current.weekday() >= 5
        else:
            # 6-day work week: Only Sunday (6) is weekend
            is_weekend = current.weekday() == 6
        
        if not is_weekend:
            # Check if it's a holiday for this employee
            if not is_non_working_day_for_employee(conn, current.isoformat(), employee_id):
                working_days += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    return working_days


def count_weekend_days_excluding_holidays(conn: sqlite3.Connection, start_date: str, end_date: str, employee_id: int) -> int:
    """
    Count weekend days that are NOT public holidays based on employee's working schedule.
    
    For 5-day work week: Counts Saturday and Sunday that are not holidays
    For 6-day work week: Counts only Sunday that is not a holiday
    
    When a weekend day is already a public holiday, it should not be counted.
    These days will be deducted from the vacation bucket.
    """
    from database import is_non_working_day_for_employee
    
    # Get employee's working days per week
    cur = conn.execute("SELECT working_days_per_week FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    working_days_per_week = row[0] if row else 6  # Default to 6 for backwards compatibility
    
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    
    weekend_days = 0
    current = s
    
    while current <= e:
        # Check if it's a weekend based on employee's working schedule
        is_weekend = False
        if working_days_per_week == 5:
            # 5-day work week: Saturday (5) and Sunday (6) are weekends
            is_weekend = current.weekday() >= 5
        else:
            # 6-day work week: Only Sunday (6) is weekend
            is_weekend = current.weekday() == 6
        
        if is_weekend:
            # Only count if it's NOT a public holiday
            if not is_non_working_day_for_employee(conn, current.isoformat(), employee_id):
                weekend_days += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    return weekend_days


def calculate_deduction_days_new_algorithm(conn: sqlite3.Connection, start_date: str, end_date: str, employee_id: int) -> int:
    """
    Calculate vacation days to be deducted using the new 6-day work week algorithm.
    
    Algorithm:
    1. total_days = number of calendar days between start and end (inclusive)
    2. full_weeks = floor(total_days / 7)
    3. rest_days = full_weeks (count of Sundays)
    4. holiday_count = number of official_holidays within range (respecting employee religion)
       IMPORTANT: if a holiday falls on Sunday, count it only once
    5. deduction_days = total_days - rest_days - holiday_count
    
    Working days per week: 6 (Monday-Saturday)
    Rest days: Sunday (1 per week)
    """
    from database import is_non_working_day_for_employee
    
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    
    # 1. Calculate total calendar days (inclusive)
    total_days = (e - s).days + 1
    
    # 2. Calculate full weeks
    full_weeks = total_days // 7
    
    # 3. Calculate rest days (Sundays)
    rest_days = full_weeks
    
    # 4. Count holidays in the range, avoiding double-counting with Sundays
    holiday_count = 0
    current = s
    
    while current <= e:
        if is_non_working_day_for_employee(conn, current.isoformat(), employee_id):
            holiday_count += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    # 5. Calculate deduction days
    deduction_days = total_days - rest_days - holiday_count
    
    return max(0, deduction_days)


def count_total_deductible_days(conn: sqlite3.Connection, start_date: str, end_date: str, employee_id: int) -> int:
    """
    Count total days to be deducted from vacation bucket.

    5-day week (Mon–Fri): only working days in the range count; Saturday and Sunday
    are never deducted (same rules as count_working_days_in_range).

    6-day week (Mon–Sat): uses calculate_deduction_days_new_algorithm (calendar-based
    with Sunday rest and religion-aware holidays).
    """
    cur = conn.execute("SELECT working_days_per_week FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    working_days_per_week = row[0] if row else 6
    if working_days_per_week == 5:
        return count_working_days_in_range(conn, start_date, end_date, employee_id)
    return calculate_deduction_days_new_algorithm(conn, start_date, end_date, employee_id)


def calculate_multi_year_vacation_requirements(
    conn: sqlite3.Connection,
    employee_id: int,
    start_date: str,
    end_date: str
) -> dict[int, dict[str, int]]:
    """
    Calculate vacation day requirements for a vacation period that may span multiple years.
    Returns dict mapping year -> {'days_needed': int, 'available': dict, 'sufficient': bool}
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    
    # Get all years this vacation spans
    years = list(range(start.year, end.year + 1))
    result = {}
    
    for year in years:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        # Calculate overlap with this year
        overlap_start = max(start, year_start)
        overlap_end = min(end, year_end)
        
        if overlap_start <= overlap_end:
            # Calculate days needed for this year's portion
            days_needed = count_total_deductible_days(
                conn, 
                overlap_start.isoformat(), 
                overlap_end.isoformat(), 
                employee_id
            )
            
            # Get available days for this year (including reservation check)
            available = get_available_days_for_scheduling(conn, employee_id, year)
            total_available = available['transferred'] + available['at_start'] + available['earned']
            
            result[year] = {
                'days_needed': days_needed,
                'available': available,
                'total_available': total_available,
                'sufficient': days_needed <= total_available,
                'overlap_start': overlap_start.isoformat(),
                'overlap_end': overlap_end.isoformat()
            }
    
    return result


def check_contract_eligibility(
    conn: sqlite3.Connection,
    employee_id: int,
    start_date: str,
    end_date: str
) -> dict[str, any]:
    """
    Check if employee is eligible to take vacation based on contract dates.
    
    Returns dict with:
    - 'eligible': bool
    - 'contract_end_date': str or None
    - 'invalid_dates': list of dates outside contract period
    """
    # Get employee contract information
    employee = get_employee(conn, employee_id)
    if not employee:
        return {'eligible': False, 'contract_end_date': None, 'invalid_dates': []}
    
    contract_end_date = employee.get('contract_end_date')
    
    # Open-ended contracts have no end date restriction
    if not contract_end_date:
        return {'eligible': True, 'contract_end_date': None, 'invalid_dates': []}
    
    # Check if vacation period extends beyond contract end date
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    contract_end = date.fromisoformat(contract_end_date)
    
    invalid_dates = []
    
    # Check if start date is after contract end
    if start > contract_end:
        invalid_dates.append(start_date)
    
    # Check if end date is after contract end
    if end > contract_end:
        invalid_dates.append(end_date)
    
    return {
        'eligible': len(invalid_dates) == 0,
        'contract_end_date': contract_end_date,
        'invalid_dates': invalid_dates
    }


def validate_vacation_scheduling(
    conn: sqlite3.Connection,
    employee_id: int,
    start_date: str,
    end_date: str,
    exclude_record_id: Optional[int] = None
) -> dict[str, any]:
    """
    Comprehensive validation for vacation scheduling including overlap detection,
    balance checking, multi-year handling, and contract eligibility.
    
    Returns dict with:
    - 'valid': bool
    - 'errors': list of error messages
    - 'overlaps': list of overlapping records
    - 'year_requirements': dict of per-year requirements
    - 'total_days_needed': int
    - 'contract_eligibility': dict with contract validation results
    """
    errors = []
    
    # Check contract eligibility
    contract_eligibility = check_contract_eligibility(conn, employee_id, start_date, end_date)
    if not contract_eligibility['eligible']:
        errors.append("contract_ineligible")
    
    # Check for overlapping vacations
    overlaps = check_vacation_overlap(conn, employee_id, start_date, end_date, exclude_record_id)
    if overlaps:
        errors.append("overlapping_vacation")
    
    # Calculate multi-year requirements
    year_requirements = calculate_multi_year_vacation_requirements(conn, employee_id, start_date, end_date)
    
    # Check if all years have sufficient balance
    insufficient_years = []
    total_days_needed = 0
    
    for year, req in year_requirements.items():
        total_days_needed += req['days_needed']
        if not req['sufficient']:
            insufficient_years.append({
                'year': year,
                'needed': req['days_needed'],
                'available': req['total_available'],
                'shortage': req['days_needed'] - req['total_available']
            })
    
    if insufficient_years:
        errors.append("insufficient_balance")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'overlaps': overlaps,
        'year_requirements': year_requirements,
        'total_days_needed': total_days_needed,
        'insufficient_years': insufficient_years,
        'contract_eligibility': contract_eligibility
    }
