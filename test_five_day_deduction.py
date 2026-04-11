#!/usr/bin/env python3
"""Sanity checks: 5-day employees deduct only Mon–Fri working days, not Sat/Sun."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import get_connection
from db_helpers import insert_employee, count_total_deductible_days, get_employee, count_working_days_in_range


def main():
    conn = get_connection(":memory:")
    eid = insert_employee(
        conn,
        jmbg="1234567890123",
        first_name="Five",
        last_name="Day",
        contract_type="open_ended",
        contract_end_date=None,
        religion="orthodox",
        start_contract_date="2026-01-01",
        working_days_per_week=5,
    )
    emp = get_employee(conn, eid)
    assert emp is not None
    assert emp["working_days_per_week"] == 5, "get_employee must return working_days_per_week"

    # Mon–Fri: 5 days
    assert count_working_days_in_range(conn, "2026-01-05", "2026-01-09", eid) == 5
    assert count_total_deductible_days(conn, "2026-01-05", "2026-01-09", eid) == 5

    # Mon–Sun: still 5 (weekend not deducted)
    assert count_total_deductible_days(conn, "2026-01-05", "2026-01-11", eid) == 5

    # Sat–Sun only: 0
    assert count_total_deductible_days(conn, "2026-01-10", "2026-01-11", eid) == 0

    conn.close()
    print("test_five_day_deduction: OK")


if __name__ == "__main__":
    main()
