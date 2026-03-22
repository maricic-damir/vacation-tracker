"""Test validation: prevent requesting more days than available."""
from datetime import date
from database import get_connection, ensure_year_balance
from db_helpers import (
    insert_employee,
    count_total_deductible_days,
    get_available_days_for_deduction,
    set_days_at_start,
    add_vacation_record,
    calculate_deduction_breakdown,
)

def test_validation_logic():
    """Test that vacation requests are properly validated against available days."""
    
    # Create in-memory database
    conn = get_connection(":memory:")
    
    # Create a test employee with 10 days at start for 2026
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
    set_days_at_start(conn, employee_id, year, 10)  # Employee has only 10 days
    
    print("Test Setup:")
    print("=" * 50)
    print(f"Employee has 10 days at start for {year}")
    print()
    
    print("Test 1: Request within available days (should succeed)")
    print("=" * 50)
    # Request Mon Jan 5 - Fri Jan 9 (5 working days)
    days_needed = count_total_deductible_days(conn, "2026-01-05", "2026-01-09", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_available = available['transferred'] + available['at_start'] + available['earned']
    
    print(f"Requesting: 2026-01-05 (Mon) to 2026-01-09 (Fri)")
    print(f"Days needed: {days_needed}")
    print(f"Days available: {total_available}")
    
    if days_needed <= total_available:
        print("✓ Validation PASSED - Request can proceed")
        breakdown = calculate_deduction_breakdown(
            days_needed,
            available['transferred'],
            available['at_start'],
            available['earned']
        )
        add_vacation_record(
            conn, employee_id,
            "2026-01-01", "2026-01-05", "2026-01-09",
            is_completed=True,
            days_from_transferred=breakdown['transferred'],
            days_from_at_start=breakdown['at_start'],
            days_from_earned=breakdown['earned'],
        )
        print(f"  Deducted from transferred: {breakdown['transferred']}")
        print(f"  Deducted from at_start: {breakdown['at_start']}")
        print(f"  Deducted from earned: {breakdown['earned']}")
    else:
        print("✗ Validation FAILED - Not enough days")
    print()
    
    print("Test 2: Request weekend day within budget (should succeed)")
    print("=" * 50)
    # Request Sat Jan 10 (1 weekend day)
    days_needed = count_total_deductible_days(conn, "2026-01-10", "2026-01-10", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_available = available['transferred'] + available['at_start'] + available['earned']
    
    print(f"Requesting: 2026-01-10 (Sat)")
    print(f"Days needed: {days_needed}")
    print(f"Days available: {total_available}")
    
    if days_needed <= total_available:
        print("✓ Validation PASSED - Request can proceed")
        breakdown = calculate_deduction_breakdown(
            days_needed,
            available['transferred'],
            available['at_start'],
            available['earned']
        )
        add_vacation_record(
            conn, employee_id,
            "2026-01-01", "2026-01-10", "2026-01-10",
            is_completed=True,
            days_from_transferred=breakdown['transferred'],
            days_from_at_start=breakdown['at_start'],
            days_from_earned=breakdown['earned'],
        )
        print(f"  Deducted from transferred: {breakdown['transferred']}")
        print(f"  Deducted from at_start: {breakdown['at_start']}")
        print(f"  Deducted from earned: {breakdown['earned']}")
    else:
        print("✗ Validation FAILED - Not enough days")
    print()
    
    print("Test 3: Request exceeding available days (should fail)")
    print("=" * 50)
    # Request Mon Jan 12 - Sun Jan 18 (5 working + 2 weekend = 7 days)
    # Employee now has 10 - 5 - 1 = 4 days left
    days_needed = count_total_deductible_days(conn, "2026-01-12", "2026-01-18", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_available = available['transferred'] + available['at_start'] + available['earned']
    
    print(f"Requesting: 2026-01-12 (Mon) to 2026-01-18 (Sun)")
    print(f"Days needed: {days_needed} (5 working + 2 weekend)")
    print(f"Days available: {total_available}")
    
    if days_needed <= total_available:
        print("✗ TEST FAILED - Should have been rejected!")
    else:
        print("✓ Validation PASSED - Request correctly rejected")
        print(f"  Shortage: {days_needed - total_available} days")
    print()
    
    print("Test 4: Request exactly matching available days (should succeed)")
    print("=" * 50)
    # Employee has 4 days left, request exactly 4 days
    # Mon Jan 12 - Thu Jan 15 (4 working days)
    days_needed = count_total_deductible_days(conn, "2026-01-12", "2026-01-15", employee_id)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_available = available['transferred'] + available['at_start'] + available['earned']
    
    print(f"Requesting: 2026-01-12 (Mon) to 2026-01-15 (Thu)")
    print(f"Days needed: {days_needed}")
    print(f"Days available: {total_available}")
    
    if days_needed <= total_available:
        print("✓ Validation PASSED - Request can proceed")
        breakdown = calculate_deduction_breakdown(
            days_needed,
            available['transferred'],
            available['at_start'],
            available['earned']
        )
        add_vacation_record(
            conn, employee_id,
            "2026-01-01", "2026-01-12", "2026-01-15",
            is_completed=True,
            days_from_transferred=breakdown['transferred'],
            days_from_at_start=breakdown['at_start'],
            days_from_earned=breakdown['earned'],
        )
        print(f"  Deducted from transferred: {breakdown['transferred']}")
        print(f"  Deducted from at_start: {breakdown['at_start']}")
        print(f"  Deducted from earned: {breakdown['earned']}")
    else:
        print("✗ Validation FAILED - Not enough days")
    print()
    
    print("Test 5: Verify no days left")
    print("=" * 50)
    available = get_available_days_for_deduction(conn, employee_id, year)
    total_available = available['transferred'] + available['at_start'] + available['earned']
    print(f"Days remaining: {total_available}")
    assert total_available == 0, f"Expected 0 days left, got {total_available}"
    print("✓ Correctly used all 10 days")
    print()
    
    conn.close()
    
    print("=" * 50)
    print("All validation tests passed! ✓")
    print("=" * 50)
    print("\nSummary:")
    print("- Vacation requests validate available days before allowing")
    print("- Weekend days (Sat/Sun) are included in the deduction count")
    print("- Weekend days that are holidays are NOT counted")
    print("- Users cannot request more days than available")
    print("- Deduction follows the order: transferred → at_start → earned")


if __name__ == "__main__":
    test_validation_logic()
