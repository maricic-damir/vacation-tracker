#!/usr/bin/env python3
"""
Test script for the new 6-day work week vacation days calculation algorithm.
Tests various scenarios including edge cases, holidays, and different date ranges.
"""

import sys
import sqlite3
from datetime import date

# Add parent directory to path
sys.path.insert(0, '/Users/d.maricic/vacation_tracker')

from database import get_connection, save_non_working_days
from db_helpers import (
    insert_employee,
    calculate_deduction_days_new_algorithm,
    count_total_deductible_days,
)


def setup_test_database():
    """Create in-memory database with test employee and some holidays."""
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
    
    # Add some test holidays
    holidays = [
        {"date": "2026-01-01", "name_sr": "Nova godina", "name_en": "New Year", "holiday_type": "state", "is_active": True},
        {"date": "2026-01-07", "name_sr": "Božić", "name_en": "Orthodox Christmas", "holiday_type": "orthodox", "is_active": True},
        {"date": "2026-01-12", "name_sr": "Nedeljni praznik", "name_en": "Sunday Holiday", "holiday_type": "state", "is_active": True},  # This is a Sunday
        {"date": "2026-05-01", "name_sr": "Praznik rada", "name_en": "Labor Day", "holiday_type": "state", "is_active": True},
        {"date": "2026-05-04", "name_sr": "Nedeljni praznik 2", "name_en": "Sunday Holiday 2", "holiday_type": "state", "is_active": True},  # This is a Sunday
    ]
    
    save_non_working_days(conn, holidays)
    
    return conn, employee_id


def test_basic_algorithm():
    """Test basic algorithm functionality."""
    print("=" * 60)
    print("TEST 1: Basic Algorithm Functionality")
    print("=" * 60)
    
    conn, employee_id = setup_test_database()
    
    # Test 1: Single day (Monday)
    print("\nTest 1a: Single Monday (2026-01-06)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-06", "2026-01-06", employee_id)
    print(f"  Date range: 2026-01-06 (Mon)")
    print(f"  Total days: 1, Full weeks: 0, Rest days: 0, Holidays: 0")
    print(f"  Expected: 1, Got: {result}")
    assert result == 1, f"Expected 1, got {result}"
    print("  ✓ PASSED")
    
    # Test 2: Single day (Sunday)
    print("\nTest 1b: Single Sunday (2026-01-05)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-05", "2026-01-05", employee_id)
    print(f"  Date range: 2026-01-05 (Sun)")
    print(f"  Total days: 1, Full weeks: 0, Rest days: 0, Holidays: 0")
    print(f"  Expected: 1, Got: {result}")
    assert result == 1, f"Expected 1, got {result}"
    print("  ✓ PASSED")
    
    # Test 3: Full week (Mon-Sun)
    print("\nTest 1c: Full week Mon-Sun (2026-01-06 to 2026-01-12)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-06", "2026-01-12", employee_id)
    print(f"  Date range: 2026-01-06 (Mon) to 2026-01-12 (Sun)")
    print(f"  Total days: 7, Full weeks: 1, Rest days: 1, Holidays: 1 (Jan 7 + Jan 12)")
    print(f"  Expected: 7 - 1 - 2 = 4, Got: {result}")
    assert result == 4, f"Expected 4, got {result}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL BASIC TESTS PASSED")


def test_multiple_weeks():
    """Test algorithm with multiple weeks."""
    print("\n" + "=" * 60)
    print("TEST 2: Multiple Weeks")
    print("=" * 60)
    
    conn, employee_id = setup_test_database()
    
    # Test 1: Two full weeks
    print("\nTest 2a: Two full weeks (2026-01-06 to 2026-01-19)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-06", "2026-01-19", employee_id)
    print(f"  Date range: 2026-01-06 (Mon) to 2026-01-19 (Sun)")
    print(f"  Total days: 14, Full weeks: 2, Rest days: 2, Holidays: 2 (Jan 7 + Jan 12)")
    print(f"  Expected: 14 - 2 - 2 = 10, Got: {result}")
    assert result == 10, f"Expected 10, got {result}"
    print("  ✓ PASSED")
    
    # Test 2: Partial weeks
    print("\nTest 2b: Partial weeks (2026-01-08 to 2026-01-15)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-08", "2026-01-15", employee_id)
    print(f"  Date range: 2026-01-08 (Wed) to 2026-01-15 (Wed)")
    print(f"  Total days: 8, Full weeks: 1, Rest days: 1, Holidays: 1 (Jan 12)")
    print(f"  Expected: 8 - 1 - 1 = 6, Got: {result}")
    assert result == 6, f"Expected 6, got {result}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL MULTIPLE WEEKS TESTS PASSED")


def test_holiday_scenarios():
    """Test various holiday scenarios."""
    print("\n" + "=" * 60)
    print("TEST 3: Holiday Scenarios")
    print("=" * 60)
    
    conn, employee_id = setup_test_database()
    
    # Test 1: Holiday on working day
    print("\nTest 3a: Holiday on working day (2026-01-01 to 2026-01-03)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-01", "2026-01-03", employee_id)
    print(f"  Date range: 2026-01-01 (Wed, New Year) to 2026-01-03 (Fri)")
    print(f"  Total days: 3, Full weeks: 0, Rest days: 0, Holidays: 1 (Jan 1)")
    print(f"  Expected: 3 - 0 - 1 = 2, Got: {result}")
    assert result == 2, f"Expected 2, got {result}"
    print("  ✓ PASSED")
    
    # Test 2: Holiday on Sunday (should not double count)
    print("\nTest 3b: Holiday on Sunday (2026-01-12 to 2026-01-12)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-12", "2026-01-12", employee_id)
    print(f"  Date range: 2026-01-12 (Sun, Holiday)")
    print(f"  Total days: 1, Full weeks: 0, Rest days: 0, Holidays: 1 (Jan 12)")
    print(f"  Expected: 1 - 0 - 1 = 0, Got: {result}")
    assert result == 0, f"Expected 0, got {result}"
    print("  ✓ PASSED")
    
    # Test 3: Multiple holidays
    print("\nTest 3c: Multiple holidays (2026-01-01 to 2026-01-07)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-01", "2026-01-07", employee_id)
    print(f"  Date range: 2026-01-01 (Wed, New Year) to 2026-01-07 (Tue, Orthodox Christmas)")
    print(f"  Total days: 7, Full weeks: 1, Rest days: 1, Holidays: 2 (Jan 1 + Jan 7)")
    print(f"  Expected: 7 - 1 - 2 = 4, Got: {result}")
    assert result == 4, f"Expected 4, got {result}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL HOLIDAY TESTS PASSED")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "=" * 60)
    print("TEST 4: Edge Cases")
    print("=" * 60)
    
    conn, employee_id = setup_test_database()
    
    # Test 1: Same start and end date
    print("\nTest 4a: Same start and end date (2026-01-15)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-15", "2026-01-15", employee_id)
    print(f"  Date range: 2026-01-15 (Wed) to 2026-01-15 (Wed)")
    print(f"  Total days: 1, Full weeks: 0, Rest days: 0, Holidays: 0")
    print(f"  Expected: 1, Got: {result}")
    assert result == 1, f"Expected 1, got {result}"
    print("  ✓ PASSED")
    
    # Test 2: Cross month boundary
    print("\nTest 4b: Cross month boundary (2026-01-30 to 2026-02-05)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-01-30", "2026-02-05", employee_id)
    print(f"  Date range: 2026-01-30 (Fri) to 2026-02-05 (Thu)")
    print(f"  Total days: 7, Full weeks: 1, Rest days: 1, Holidays: 0")
    print(f"  Expected: 7 - 1 - 0 = 6, Got: {result}")
    assert result == 6, f"Expected 6, got {result}"
    print("  ✓ PASSED")
    
    # Test 3: Long period with multiple Sundays and holidays
    print("\nTest 4c: Long period (2026-05-01 to 2026-05-10)")
    result = calculate_deduction_days_new_algorithm(conn, "2026-05-01", "2026-05-10", employee_id)
    print(f"  Date range: 2026-05-01 (Fri, Labor Day) to 2026-05-10 (Sat)")
    print(f"  Total days: 10, Full weeks: 1, Rest days: 1, Holidays: 2 (May 1 + May 4)")
    print(f"  Expected: 10 - 1 - 2 = 7, Got: {result}")
    assert result == 7, f"Expected 7, got {result}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL EDGE CASE TESTS PASSED")


def test_religion_filtering():
    """Test that religion-based holiday filtering still works."""
    print("\n" + "=" * 60)
    print("TEST 5: Religion-based Holiday Filtering")
    print("=" * 60)
    
    conn = get_connection(":memory:")
    
    # Create Orthodox employee
    orthodox_id = insert_employee(
        conn,
        jmbg="1111111111111",
        first_name="Orthodox",
        last_name="Employee",
        contract_type="open_ended",
        contract_end_date=None,
        religion="orthodox",
        start_contract_date="2026-01-01"
    )
    
    # Create Catholic employee
    catholic_id = insert_employee(
        conn,
        jmbg="2222222222222",
        first_name="Catholic",
        last_name="Employee",
        contract_type="open_ended",
        contract_end_date=None,
        religion="catholic",
        start_contract_date="2026-01-01"
    )
    
    # Add religious holidays
    holidays = [
        {"date": "2026-01-07", "name_sr": "Božić", "name_en": "Orthodox Christmas", "holiday_type": "orthodox", "is_active": True},
        {"date": "2026-12-25", "name_sr": "Katolički Božić", "name_en": "Catholic Christmas", "holiday_type": "catholic", "is_active": True},
        {"date": "2026-05-01", "name_sr": "Praznik rada", "name_en": "Labor Day", "holiday_type": "state", "is_active": True},
    ]
    
    save_non_working_days(conn, holidays)
    
    # Test Orthodox employee with Orthodox holiday
    print("\nTest 5a: Orthodox employee with Orthodox Christmas")
    result_orthodox = calculate_deduction_days_new_algorithm(conn, "2026-01-07", "2026-01-07", orthodox_id)
    print(f"  Orthodox employee on 2026-01-07 (Orthodox Christmas)")
    print(f"  Expected: 0 (holiday applies), Got: {result_orthodox}")
    assert result_orthodox == 0, f"Expected 0, got {result_orthodox}"
    print("  ✓ PASSED")
    
    # Test Catholic employee with Orthodox holiday (should not apply)
    print("\nTest 5b: Catholic employee with Orthodox Christmas")
    result_catholic = calculate_deduction_days_new_algorithm(conn, "2026-01-07", "2026-01-07", catholic_id)
    print(f"  Catholic employee on 2026-01-07 (Orthodox Christmas)")
    print(f"  Expected: 1 (holiday doesn't apply), Got: {result_catholic}")
    assert result_catholic == 1, f"Expected 1, got {result_catholic}"
    print("  ✓ PASSED")
    
    # Test both employees with state holiday
    print("\nTest 5c: Both employees with state holiday")
    result_orthodox_state = calculate_deduction_days_new_algorithm(conn, "2026-05-01", "2026-05-01", orthodox_id)
    result_catholic_state = calculate_deduction_days_new_algorithm(conn, "2026-05-01", "2026-05-01", catholic_id)
    print(f"  Both employees on 2026-05-01 (Labor Day - state holiday)")
    print(f"  Orthodox expected: 0, Got: {result_orthodox_state}")
    print(f"  Catholic expected: 0, Got: {result_catholic_state}")
    assert result_orthodox_state == 0, f"Orthodox expected 0, got {result_orthodox_state}"
    assert result_catholic_state == 0, f"Catholic expected 0, got {result_catholic_state}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL RELIGION FILTERING TESTS PASSED")


def test_integration_with_main_function():
    """Test that the main function uses the new algorithm."""
    print("\n" + "=" * 60)
    print("TEST 6: Integration with Main Function")
    print("=" * 60)
    
    conn, employee_id = setup_test_database()
    
    # Test that count_total_deductible_days uses the new algorithm
    print("\nTest 6a: Main function integration")
    new_result = calculate_deduction_days_new_algorithm(conn, "2026-01-06", "2026-01-12", employee_id)
    main_result = count_total_deductible_days(conn, "2026-01-06", "2026-01-12", employee_id)
    
    print(f"  New algorithm result: {new_result}")
    print(f"  Main function result: {main_result}")
    print(f"  Expected: Both should be equal")
    assert new_result == main_result, f"Results should be equal: {new_result} != {main_result}"
    print("  ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ INTEGRATION TEST PASSED")


def run_all_tests():
    """Run all test suites."""
    print("🧪 RUNNING NEW ALGORITHM COMPREHENSIVE TESTS")
    print("=" * 80)
    
    try:
        test_basic_algorithm()
        test_multiple_weeks()
        test_holiday_scenarios()
        test_edge_cases()
        test_religion_filtering()
        test_integration_with_main_function()
        
        print("\n" + "🎉" * 20)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
        print("🎉" * 20)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()