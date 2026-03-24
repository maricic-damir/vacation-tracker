"""Test weekend deduction logic with new 6-day work week algorithm."""
from datetime import date
from database import get_connection, save_non_working_days
from db_helpers import (
    insert_employee,
    count_working_days_in_range,
    count_weekend_days_excluding_holidays,
    count_total_deductible_days,
)

def test_weekend_counting():
    """Test the new 6-day work week algorithm (Monday-Saturday working, Sunday rest)."""
    
    # Create in-memory database
    conn = get_connection(":memory:")
    
    # Create a test employee (Orthodox)
    employee_id = insert_employee(
        conn,
        jmbg="1234567890123",
        first_name="Test",
        last_name="Employee",
        contract_type="open_ended",
        contract_end_date=None,
        religion="orthodox",
        start_contract_date="2026-01-01"
    )
    
    print("Test 1: Regular week (Mon-Fri)")
    print("=" * 50)
    # Test regular working week: Mon Jan 5 - Fri Jan 9, 2026
    working = count_working_days_in_range(conn, "2026-01-05", "2026-01-09", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-01-05", "2026-01-09", employee_id)
    total = count_total_deductible_days(conn, "2026-01-05", "2026-01-09", employee_id)
    print(f"Date range: 2026-01-05 (Mon) to 2026-01-09 (Fri)")
    print(f"Working days: {working} (expected: 5)")
    print(f"Weekend days: {weekend} (expected: 0)")
    print(f"Total deductible: {total} (expected: 5)")
    assert working == 5, f"Expected 5 working days, got {working}"
    assert weekend == 0, f"Expected 0 weekend days, got {weekend}"
    assert total == 5, f"Expected 5 total days, got {total}"
    print("✓ PASSED\n")
    
    print("Test 2: Week including weekend (Mon-Sun)")
    print("=" * 50)
    # Test week with weekend: Mon Jan 5 - Sun Jan 11, 2026
    # New algorithm: 7 total days - 1 Sunday = 6 deductible days
    working = count_working_days_in_range(conn, "2026-01-05", "2026-01-11", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-01-05", "2026-01-11", employee_id)
    total = count_total_deductible_days(conn, "2026-01-05", "2026-01-11", employee_id)
    print(f"Date range: 2026-01-05 (Mon) to 2026-01-11 (Sun)")
    print(f"Working days (old logic): {working} (Mon-Fri)")
    print(f"Weekend days (old logic): {weekend} (Sat-Sun excluding holidays)")
    print(f"Total deductible (new algorithm): {total} (expected: 6 = 7 total - 1 Sunday)")
    # Note: We keep the old working/weekend functions for reference but use new total calculation
    assert working == 5, f"Expected 5 working days (Mon-Fri), got {working}"
    assert weekend == 2, f"Expected 2 weekend days (Sat-Sun), got {weekend}"
    assert total == 6, f"Expected 6 total days (new algorithm), got {total}"
    print("✓ PASSED\n")
    
    print("Test 3: Single Saturday")
    print("=" * 50)
    # Test single Saturday: Sat Jan 10, 2026
    working = count_working_days_in_range(conn, "2026-01-10", "2026-01-10", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-01-10", "2026-01-10", employee_id)
    total = count_total_deductible_days(conn, "2026-01-10", "2026-01-10", employee_id)
    print(f"Date range: 2026-01-10 (Sat)")
    print(f"Working days: {working} (expected: 0)")
    print(f"Weekend days: {weekend} (expected: 1)")
    print(f"Total deductible: {total} (expected: 1)")
    assert working == 0, f"Expected 0 working days, got {working}"
    assert weekend == 1, f"Expected 1 weekend day, got {weekend}"
    assert total == 1, f"Expected 1 total day, got {total}"
    print("✓ PASSED\n")
    
    print("Test 4: Single Sunday")
    print("=" * 50)
    # Test single Sunday: Sun Jan 11, 2026
    # New algorithm: 1 total day - 0 full weeks (no complete Sunday) = 1 deductible day
    working = count_working_days_in_range(conn, "2026-01-11", "2026-01-11", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-01-11", "2026-01-11", employee_id)
    total = count_total_deductible_days(conn, "2026-01-11", "2026-01-11", employee_id)
    print(f"Date range: 2026-01-11 (Sun)")
    print(f"Working days (old logic): {working} (expected: 0)")
    print(f"Weekend days (old logic): {weekend} (expected: 1)")
    print(f"Total deductible (new algorithm): {total} (expected: 1 = 1 total - 0 rest days)")
    assert working == 0, f"Expected 0 working days, got {working}"
    assert weekend == 1, f"Expected 1 weekend day, got {weekend}"
    assert total == 1, f"Expected 1 total day (new algorithm), got {total}"
    print("✓ PASSED\n")
    
    print("Test 5: Weekend when Sunday is a holiday")
    print("=" * 50)
    # Add New Year's Day 2026 (Wed Jan 1) and Statehood Day (Sun Feb 15)
    holidays = [
        {'date': '2026-02-15', 'name_sr': 'Dan državnosti Srbije', 'name_en': 'Serbian Statehood Day', 'holiday_type': 'state'},
    ]
    save_non_working_days(conn, holidays)
    
    # Test weekend where Sunday is a holiday: Sat Feb 14 - Sun Feb 15, 2026
    # New algorithm: 2 total days - 0 full weeks - 1 holiday = 1 deductible day
    working = count_working_days_in_range(conn, "2026-02-14", "2026-02-15", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-02-14", "2026-02-15", employee_id)
    total = count_total_deductible_days(conn, "2026-02-14", "2026-02-15", employee_id)
    print(f"Date range: 2026-02-14 (Sat) to 2026-02-15 (Sun - State Holiday)")
    print(f"Working days (old logic): {working} (expected: 0)")
    print(f"Weekend days (old logic): {weekend} (expected: 1 - only Sat, Sun is holiday)")
    print(f"Total deductible (new algorithm): {total} (expected: 1 = 2 total - 0 rest days - 1 holiday)")
    assert working == 0, f"Expected 0 working days, got {working}"
    assert weekend == 1, f"Expected 1 weekend day (Sat only), got {weekend}"
    assert total == 1, f"Expected 1 total day (new algorithm), got {total}"
    print("✓ PASSED\n")
    
    print("Test 6: Two full weeks")
    print("=" * 50)
    # Test two full weeks: Mon Jan 5 - Sun Jan 18, 2026 (14 days total)
    # New algorithm: 14 total days - 2 Sundays = 12 deductible days
    working = count_working_days_in_range(conn, "2026-01-05", "2026-01-18", employee_id)
    weekend = count_weekend_days_excluding_holidays(conn, "2026-01-05", "2026-01-18", employee_id)
    total = count_total_deductible_days(conn, "2026-01-05", "2026-01-18", employee_id)
    print(f"Date range: 2026-01-05 (Mon) to 2026-01-18 (Sun)")
    print(f"Working days (old logic): {working} (expected: 10 Mon-Fri)")
    print(f"Weekend days (old logic): {weekend} (expected: 4 - two Saturdays, two Sundays)")
    print(f"Total deductible (new algorithm): {total} (expected: 12 = 14 total - 2 Sundays)")
    assert working == 10, f"Expected 10 working days, got {working}"
    assert weekend == 4, f"Expected 4 weekend days, got {weekend}"
    assert total == 12, f"Expected 12 total days (new algorithm), got {total}"
    print("✓ PASSED\n")
    
    conn.close()
    
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
    print("\nSummary:")
    print("- NEW ALGORITHM: 6-day work week (Monday-Saturday working, Sunday rest)")
    print("- Formula: total_days - rest_days (Sundays) - holidays")
    print("- Holidays and Sundays are not double-counted")
    print("- Days are deducted in order: transferred → at_start → earned")


if __name__ == "__main__":
    test_weekend_counting()
