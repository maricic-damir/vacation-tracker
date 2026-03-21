#!/usr/bin/env python3
"""
Test script for religion-based holiday filtering.
Tests that Orthodox and Catholic employees get different holidays.
"""

import sys
import sqlite3
from datetime import date

sys.path.insert(0, '/Users/d.maricic/vacation_tracker')

from database import get_connection, save_non_working_days, init_schema
from db_helpers import count_working_days_in_range, insert_employee
from holiday_scraper import scrape_serbian_holidays


def test_religion_based_filtering():
    """Test that holidays are correctly filtered by employee religion."""
    print("\n=== Test: Religion-Based Holiday Filtering ===")
    
    # Create in-memory database
    conn = sqlite3.Connection(':memory:')
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    
    # Create two employees: one Orthodox, one Catholic
    print("\n1. Creating employees...")
    orthodox_emp_id = insert_employee(conn, "1234567890123", "Petar", "Petrović", "open_ended", None, "orthodox")
    catholic_emp_id = insert_employee(conn, "9876543210987", "Ana", "Kovač", "open_ended", None, "catholic")
    print(f"   Orthodox employee ID: {orthodox_emp_id}")
    print(f"   Catholic employee ID: {catholic_emp_id}")
    
    # Load all 2026 holidays (including both Orthodox and Catholic)
    print("\n2. Loading 2026 holidays...")
    holidays, source = scrape_serbian_holidays(2026)
    save_non_working_days(conn, holidays)
    print(f"   Loaded {len(holidays)} holidays")
    print(f"   Source: {source}")
    
    # Test 1: Orthodox Christmas (Jan 7, 2026) - Thu
    print("\n3. Test Orthodox Christmas (Jan 7, 2026)...")
    print("   Jan 5-9: Mon-Fri week")
    
    orthodox_days = count_working_days_in_range(conn, '2026-01-05', '2026-01-09', orthodox_emp_id)
    catholic_days = count_working_days_in_range(conn, '2026-01-05', '2026-01-09', catholic_emp_id)
    
    print(f"   Orthodox employee: {orthodox_days} working days (should be 4, Jan 7 excluded)")
    print(f"   Catholic employee: {catholic_days} working days (should be 5, Jan 7 is working day)")
    
    assert orthodox_days == 4, f"Orthodox employee should have 4 working days, got {orthodox_days}"
    assert catholic_days == 5, f"Catholic employee should have 5 working days, got {catholic_days}"
    
    # Test 2: Catholic Christmas (Dec 25, 2026) - Fri
    print("\n4. Test Catholic Christmas (Dec 25, 2026)...")
    print("   Dec 21-25: Mon-Fri week")
    
    orthodox_days = count_working_days_in_range(conn, '2026-12-21', '2026-12-25', orthodox_emp_id)
    catholic_days = count_working_days_in_range(conn, '2026-12-21', '2026-12-25', catholic_emp_id)
    
    print(f"   Orthodox employee: {orthodox_days} working days (should be 5, Dec 25 is working day)")
    print(f"   Catholic employee: {catholic_days} working days (should be 4, Dec 25 excluded)")
    
    assert orthodox_days == 5, f"Orthodox employee should have 5 working days, got {orthodox_days}"
    assert catholic_days == 4, f"Catholic employee should have 4 working days, got {catholic_days}"
    
    # Test 3: State holiday (May 1, Labour Day) - applies to both
    print("\n5. Test Labour Day (May 1, 2026) - state holiday...")
    print("   Apr 27 - May 1: Mon-Fri")
    
    orthodox_days = count_working_days_in_range(conn, '2026-04-27', '2026-05-01', orthodox_emp_id)
    catholic_days = count_working_days_in_range(conn, '2026-04-27', '2026-05-01', catholic_emp_id)
    
    print(f"   Orthodox employee: {orthodox_days} working days (should be 4, May 1 excluded)")
    print(f"   Catholic employee: {catholic_days} working days (should be 4, May 1 excluded)")
    
    assert orthodox_days == 4, f"Both should have 4 working days, Orthodox got {orthodox_days}"
    assert catholic_days == 4, f"Both should have 4 working days, Catholic got {catholic_days}"
    
    # Test 4: Orthodox Easter week (Apr 10-13, 2026)
    print("\n6. Test Orthodox Easter week (Apr 10-13, 2026)...")
    
    orthodox_days = count_working_days_in_range(conn, '2026-04-10', '2026-04-13', orthodox_emp_id)
    catholic_days = count_working_days_in_range(conn, '2026-04-10', '2026-04-13', catholic_emp_id)
    
    print(f"   Orthodox employee: {orthodox_days} working days (should be 0, all holidays/weekend)")
    print(f"   Catholic employee: {catholic_days} working days (should be 2, Fri+Mon)")
    
    assert orthodox_days == 0, f"Orthodox should have 0 working days, got {orthodox_days}"
    assert catholic_days == 2, f"Catholic should have 2 working days (Fri+Mon), got {catholic_days}"
    
    # Test 5: Catholic Easter week (Apr 3-6, 2026)
    print("\n7. Test Catholic Easter week (Apr 3-6, 2026)...")
    
    orthodox_days = count_working_days_in_range(conn, '2026-04-03', '2026-04-06', orthodox_emp_id)
    catholic_days = count_working_days_in_range(conn, '2026-04-03', '2026-04-06', catholic_emp_id)
    
    print(f"   Orthodox employee: {orthodox_days} working days (should be 2, Fri+Mon)")
    print(f"   Catholic employee: {catholic_days} working days (should be 0, all holidays/weekend)")
    
    assert orthodox_days == 2, f"Orthodox should have 2 working days (Fri+Mon), got {orthodox_days}"
    assert catholic_days == 0, f"Catholic should have 0 working days, got {catholic_days}"
    
    print("\n✓ All religion-based filtering tests passed!")
    conn.close()


def main():
    """Run religion-based holiday filtering tests."""
    print("=" * 70)
    print("RELIGION-BASED HOLIDAY FILTERING - TEST SUITE")
    print("=" * 70)
    
    try:
        test_religion_based_filtering()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nReligion-based filtering works correctly:")
        print("- Orthodox employees get Orthodox holidays off")
        print("- Catholic employees get Catholic holidays off")
        print("- State holidays apply to everyone")
        print("- Each employee only sees their relevant holidays")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
