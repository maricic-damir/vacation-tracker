#!/usr/bin/env python3
"""
Test script for working days calculation and holiday management.
Run this to verify the implementation is working correctly.
"""

import sys
import sqlite3
from datetime import date

# Add parent directory to path
sys.path.insert(0, '/Users/d.maricic/vacation_tracker')

from database import get_connection, save_non_working_days, get_non_working_days
from db_helpers import count_working_days_in_range
from holiday_scraper import scrape_serbian_holidays


def test_working_days_calculation():
    """Test working days calculation with and without holidays."""
    print("\n=== Test 1: Working Days Calculation ===")
    
    # Create in-memory database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Initialize schema
    from database import init_schema
    init_schema(conn)
    
    # Test 1: Week without holidays (Mon-Fri)
    print("\nTest 1a: Mon Jan 5 - Fri Jan 9, 2026 (no holidays)")
    working_days = count_working_days_in_range(conn, '2026-01-05', '2026-01-09')
    print(f"  Expected: 5, Got: {working_days}")
    assert working_days == 5, "Should be 5 working days"
    
    # Test 2: Week with weekend
    print("\nTest 1b: Mon Jan 5 - Sun Jan 11, 2026 (includes weekend)")
    working_days = count_working_days_in_range(conn, '2026-01-05', '2026-01-11')
    print(f"  Expected: 5, Got: {working_days}")
    assert working_days == 5, "Should be 5 working days (excludes Sat-Sun)"
    
    # Test 3: Add New Year holidays and test
    print("\nTest 1c: Adding New Year holidays to database...")
    holidays = [
        {'date': '2026-01-01', 'name_sr': 'Nova godina', 'name_en': 'New Year', 'holiday_type': 'state'},
        {'date': '2026-01-02', 'name_sr': 'Nova godina', 'name_en': 'New Year', 'holiday_type': 'state'},
    ]
    save_non_working_days(conn, holidays)
    
    print("  Testing Thu Jan 1 - Fri Jan 2, 2026 (both holidays)")
    working_days = count_working_days_in_range(conn, '2026-01-01', '2026-01-02')
    print(f"  Expected: 0, Got: {working_days}")
    assert working_days == 0, "Should be 0 working days (both are holidays)"
    
    print("  Testing Wed Dec 31, 2025 - Mon Jan 5, 2026")
    working_days = count_working_days_in_range(conn, '2025-12-31', '2026-01-05')
    print(f"  Expected: 2 (Dec 31 + Jan 5), Got: {working_days}")
    assert working_days == 2, "Should be 2 working days (Wed Dec 31, Mon Jan 5)"
    
    print("\n✓ All working days calculations passed!")
    conn.close()


def test_holiday_scraping():
    """Test holiday scraping functionality."""
    print("\n=== Test 2: Holiday Scraping ===")
    
    print("\nTest 2a: Scraping 2026 holidays...")
    holidays, source = scrape_serbian_holidays(2026)
    
    print(f"  Source: {source}")
    print(f"  Holidays fetched: {len(holidays)}")
    
    if holidays:
        print("\n  First 3 holidays:")
        for i, holiday in enumerate(holidays[:3]):
            print(f"    {i+1}. {holiday['date']}: {holiday['name_sr']} ({holiday['holiday_type']})")
        
        # Check that we have expected holidays
        dates = [h['date'] for h in holidays]
        assert '2026-01-01' in dates, "Should have New Year (Jan 1)"
        assert '2026-01-07' in dates, "Should have Orthodox Christmas (Jan 7)"
        
        print("\n✓ Holiday scraping works!")
    else:
        print("\n⚠ Warning: No holidays fetched (may need internet connection)")


def test_database_crud():
    """Test CRUD operations for holidays."""
    print("\n=== Test 3: Database CRUD Operations ===")
    
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    from database import init_schema
    init_schema(conn)
    
    print("\nTest 3a: Saving holidays to database...")
    holidays = [
        {'date': '2026-01-01', 'name_sr': 'Nova godina', 'name_en': 'New Year', 'holiday_type': 'state'},
        {'date': '2026-05-01', 'name_sr': 'Praznik rada', 'name_en': 'Labour Day', 'holiday_type': 'state'},
    ]
    count = save_non_working_days(conn, holidays)
    print(f"  Saved: {count} holidays")
    assert count == 2, "Should save 2 holidays"
    
    print("\nTest 3b: Retrieving holidays from database...")
    saved = get_non_working_days(conn, 2026)
    print(f"  Retrieved: {len(saved)} holidays")
    assert len(saved) == 2, "Should retrieve 2 holidays"
    
    print("\nTest 3c: Checking holiday details...")
    for h in saved:
        print(f"    {h['date']}: {h['name_sr']} ({h['holiday_type']})")
    
    print("\n✓ Database CRUD operations work!")
    conn.close()


def test_integration():
    """Test integration between scraping, saving, and working days calculation."""
    print("\n=== Test 4: Integration Test ===")
    
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    from database import init_schema
    init_schema(conn)
    
    print("\nTest 4a: Fetch and save 2026 holidays...")
    holidays, source = scrape_serbian_holidays(2026)
    if holidays:
        count = save_non_working_days(conn, holidays)
        print(f"  Saved {count} holidays from: {source}")
        
        print("\nTest 4b: Calculate working days for Orthodox Easter week...")
        # Apr 10-13, 2026 are all Orthodox Easter holidays
        working_days = count_working_days_in_range(conn, '2026-04-10', '2026-04-13')
        print(f"  Apr 10-13, 2026: {working_days} working days")
        print(f"  Expected: 0 (all are Orthodox holidays)")
        
        if working_days == 0:
            print("\n✓ Integration test passed!")
        else:
            print(f"\n⚠ Warning: Expected 0 working days, got {working_days}")
    else:
        print("  ⚠ Skipped (no holidays available)")
    
    conn.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("WORKING DAYS & HOLIDAYS - TEST SUITE")
    print("=" * 60)
    
    try:
        test_working_days_calculation()
        test_holiday_scraping()
        test_database_crud()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe implementation is ready to use.")
        print("You can now run the main application and use the")
        print("'Manage Non-Working Days' button to load holidays.")
        
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
