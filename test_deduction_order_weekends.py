"""Test deduction order: transferred → at_start → earned with weekend days."""
from datetime import date
from database import get_connection, ensure_year_balance
from db_helpers import (
    insert_employee,
    count_total_deductible_days,
    get_available_days_for_deduction,
    set_days_at_start,
    set_transferred_days,
    add_earned_days,
    add_vacation_record,
    calculate_deduction_breakdown,
)

def test_deduction_order_with_weekends():
    """Test that deduction follows correct order even when including weekend days."""
    
    # Create in-memory database
    conn = get_connection(":memory:")
    
    # Create a test employee
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
    
    year = 2026
    ensure_year_balance(conn, employee_id, year, "open_ended")
    
    # Set up buckets: 3 transferred, 5 at_start, 2 earned
    set_transferred_days(conn, employee_id, year, 3)
    set_days_at_start(conn, employee_id, year, 5)
    add_earned_days(conn, employee_id, "2026-01-15", 2, "Test earned days")
    
    print("Test Setup:")
    print("=" * 50)
    print(f"Employee balance for {year}:")
    available = get_available_days_for_deduction(conn, employee_id, year)
    print(f"  Transferred from prev year: {available['transferred']} days")
    print(f"  At start of year: {available['at_start']} days")
    print(f"  Earned: {available['earned']} days")
    print(f"  TOTAL: {available['transferred'] + available['at_start'] + available['earned']} days")
    print()
    
    print("Test 1: Request 2 days (including weekend) - should use transferred only")
    print("=" * 50)
    # Request Sat-Sun Jan 10-11 (2 weekend days)
    days_needed = count_total_deductible_days(conn, "2026-01-10", "2026-01-11", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    
    print(f"Requesting: 2026-01-10 (Sat) to 2026-01-11 (Sun)")
    print(f"Days needed: {days_needed} (2 weekend days)")
    
    breakdown = calculate_deduction_breakdown(
        days_needed,
        available['transferred'],
        available['at_start'],
        available['earned']
    )
    
    print(f"Deduction breakdown:")
    print(f"  From transferred: {breakdown['transferred']} (expected: 2)")
    print(f"  From at_start: {breakdown['at_start']} (expected: 0)")
    print(f"  From earned: {breakdown['earned']} (expected: 0)")
    
    assert breakdown['transferred'] == 2, f"Expected 2 from transferred, got {breakdown['transferred']}"
    assert breakdown['at_start'] == 0, f"Expected 0 from at_start, got {breakdown['at_start']}"
    assert breakdown['earned'] == 0, f"Expected 0 from earned, got {breakdown['earned']}"
    
    add_vacation_record(
        conn, employee_id,
        "2026-01-01", "2026-01-10", "2026-01-11",
        is_completed=True,
        days_from_transferred=breakdown['transferred'],
        days_from_at_start=breakdown['at_start'],
        days_from_earned=breakdown['earned'],
    )
    print("✓ PASSED - Used transferred days first\n")
    
    print("Test 2: Request 4 days (work+weekend) - should use remaining transferred + at_start")
    print("=" * 50)
    # Request Mon-Thu Jan 5-8 (4 working days)
    days_needed = count_total_deductible_days(conn, "2026-01-05", "2026-01-08", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    
    print(f"Requesting: 2026-01-05 (Mon) to 2026-01-08 (Thu)")
    print(f"Days needed: {days_needed} (4 working days)")
    print(f"Available: transferred={available['transferred']}, at_start={available['at_start']}, earned={available['earned']}")
    
    breakdown = calculate_deduction_breakdown(
        days_needed,
        available['transferred'],
        available['at_start'],
        available['earned']
    )
    
    print(f"Deduction breakdown:")
    print(f"  From transferred: {breakdown['transferred']} (expected: 1 - remaining transferred)")
    print(f"  From at_start: {breakdown['at_start']} (expected: 3 - rest from at_start)")
    print(f"  From earned: {breakdown['earned']} (expected: 0)")
    
    assert breakdown['transferred'] == 1, f"Expected 1 from transferred, got {breakdown['transferred']}"
    assert breakdown['at_start'] == 3, f"Expected 3 from at_start, got {breakdown['at_start']}"
    assert breakdown['earned'] == 0, f"Expected 0 from earned, got {breakdown['earned']}"
    
    add_vacation_record(
        conn, employee_id,
        "2026-01-01", "2026-01-05", "2026-01-08",
        is_completed=True,
        days_from_transferred=breakdown['transferred'],
        days_from_at_start=breakdown['at_start'],
        days_from_earned=breakdown['earned'],
    )
    print("✓ PASSED - Used remaining transferred, then at_start\n")
    
    print("Test 3: Request 3 days (including weekend) - should use at_start + earned")
    print("=" * 50)
    # Request Fri-Sun Jan 16-18 (1 working + 2 weekend = 3 days)
    days_needed = count_total_deductible_days(conn, "2026-01-16", "2026-01-18", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    
    print(f"Requesting: 2026-01-16 (Fri) to 2026-01-18 (Sun)")
    print(f"Days needed: {days_needed} (1 working + 2 weekend)")
    print(f"Available: transferred={available['transferred']}, at_start={available['at_start']}, earned={available['earned']}")
    
    breakdown = calculate_deduction_breakdown(
        days_needed,
        available['transferred'],
        available['at_start'],
        available['earned']
    )
    
    print(f"Deduction breakdown:")
    print(f"  From transferred: {breakdown['transferred']} (expected: 0 - all used)")
    print(f"  From at_start: {breakdown['at_start']} (expected: 2 - remaining at_start)")
    print(f"  From earned: {breakdown['earned']} (expected: 1 - rest from earned)")
    
    assert breakdown['transferred'] == 0, f"Expected 0 from transferred, got {breakdown['transferred']}"
    assert breakdown['at_start'] == 2, f"Expected 2 from at_start, got {breakdown['at_start']}"
    assert breakdown['earned'] == 1, f"Expected 1 from earned, got {breakdown['earned']}"
    
    add_vacation_record(
        conn, employee_id,
        "2026-01-01", "2026-01-16", "2026-01-18",
        is_completed=True,
        days_from_transferred=breakdown['transferred'],
        days_from_at_start=breakdown['at_start'],
        days_from_earned=breakdown['earned'],
    )
    print("✓ PASSED - Used remaining at_start, then earned\n")
    
    print("Test 4: Verify remaining balance")
    print("=" * 50)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_remaining = available['transferred'] + available['at_start'] + available['earned']
    
    print(f"Remaining balance:")
    print(f"  Transferred: {available['transferred']} (expected: 0)")
    print(f"  At start: {available['at_start']} (expected: 0)")
    print(f"  Earned: {available['earned']} (expected: 1)")
    print(f"  TOTAL: {total_remaining} days (expected: 1)")
    
    assert available['transferred'] == 0, f"Expected 0 transferred left, got {available['transferred']}"
    assert available['at_start'] == 0, f"Expected 0 at_start left, got {available['at_start']}"
    assert available['earned'] == 1, f"Expected 1 earned left, got {available['earned']}"
    assert total_remaining == 1, f"Expected 1 day total remaining, got {total_remaining}"
    
    print("✓ PASSED - Balance correctly calculated\n")
    
    conn.close()
    
    print("=" * 50)
    print("All deduction order tests passed! ✓")
    print("=" * 50)
    print("\nSummary:")
    print("- Deduction order is strictly: transferred → at_start → earned")
    print("- Weekend days are included in all deduction calculations")
    print("- Order is maintained regardless of whether days are working or weekend")
    print("- Balance tracking correctly accounts for all deductions")


if __name__ == "__main__":
    test_deduction_order_with_weekends()
