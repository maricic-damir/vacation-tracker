#!/usr/bin/env python3
"""
Script to recalculate all existing vacation records using the new 6-day work week algorithm.
This should be run after implementing the new algorithm to update historical data.
"""

import sys
import sqlite3
from datetime import date

# Add parent directory to path
sys.path.insert(0, '/Users/d.maricic/vacation_tracker')

from database import get_connection, recalculate_all_vacation_records_with_working_days
from config import get_db_path


def backup_database(db_path: str) -> str:
    """Create a backup of the database before recalculation."""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        raise


def show_records_summary(conn: sqlite3.Connection) -> dict:
    """Show summary of vacation records before/after recalculation."""
    cur = conn.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN is_completed = 1 THEN 1 END) as completed_records,
            SUM(CASE WHEN is_completed = 1 THEN days_from_transferred + days_from_at_start + days_from_earned ELSE 0 END) as total_days_used
        FROM vacation_records
    """)
    
    result = cur.fetchone()
    summary = {
        'total_records': result[0],
        'completed_records': result[1], 
        'total_days_used': result[2] or 0
    }
    
    print(f"  Total vacation records: {summary['total_records']}")
    print(f"  Completed records: {summary['completed_records']}")
    print(f"  Total days used: {summary['total_days_used']}")
    
    return summary


def show_sample_records(conn: sqlite3.Connection, limit: int = 5):
    """Show sample vacation records with their deduction details."""
    cur = conn.execute("""
        SELECT 
            vr.id,
            e.first_name || ' ' || e.last_name as employee_name,
            vr.start_date,
            vr.end_date,
            vr.days_from_transferred,
            vr.days_from_at_start,
            vr.days_from_earned,
            (vr.days_from_transferred + vr.days_from_at_start + vr.days_from_earned) as total_days
        FROM vacation_records vr
        JOIN employees e ON e.id = vr.employee_id
        WHERE vr.is_completed = 1
        ORDER BY vr.start_date DESC
        LIMIT ?
    """, (limit,))
    
    records = cur.fetchall()
    
    if records:
        print(f"\n  Sample records (showing {len(records)} most recent):")
        print("  " + "="*80)
        for record in records:
            print(f"  ID {record[0]}: {record[1]}")
            print(f"    Date range: {record[2]} to {record[3]}")
            print(f"    Days used: {record[7]} (transferred: {record[4]}, at_start: {record[5]}, earned: {record[6]})")
            print()


def main():
    """Main recalculation process."""
    print("🔄 VACATION RECORDS RECALCULATION")
    print("=" * 60)
    print("This script will recalculate all completed vacation records")
    print("using the new 6-day work week algorithm.")
    print()
    
    # Get database path
    db_path = get_db_path()
    if not db_path:
        # Try the default path in the workspace
        db_path = "/Users/d.maricic/vacation_tracker/vacationTracker.db"
    
    print(f"Database: {db_path}")
    
    # Check if database exists
    import os
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the application first to create it.")
        return
    
    # Create backup
    print("\n1. Creating backup...")
    try:
        backup_path = backup_database(db_path)
    except Exception as e:
        print(f"❌ Cannot proceed without backup: {e}")
        return
    
    # Connect to database
    print("\n2. Connecting to database...")
    try:
        conn = get_connection(db_path)
        print("✓ Connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Show current state
    print("\n3. Current state:")
    print("-" * 30)
    before_summary = show_records_summary(conn)
    show_sample_records(conn, 3)
    
    if before_summary['completed_records'] == 0:
        print("\n✓ No completed vacation records found. Nothing to recalculate.")
        conn.close()
        return
    
    # Ask for confirmation
    print("\n4. Confirmation:")
    print("-" * 30)
    print(f"About to recalculate {before_summary['completed_records']} completed vacation records.")
    print("This will update the deduction breakdown (days_from_transferred, days_from_at_start, days_from_earned)")
    print("using the new 6-day work week algorithm.")
    print()
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Recalculation cancelled.")
        conn.close()
        return
    
    # Perform recalculation
    print("\n5. Recalculating records...")
    print("-" * 30)
    try:
        recalculate_all_vacation_records_with_working_days(conn)
        print("✓ Recalculation completed successfully")
    except Exception as e:
        print(f"❌ Recalculation failed: {e}")
        print(f"Database backup is available at: {backup_path}")
        conn.close()
        return
    
    # Show updated state
    print("\n6. Updated state:")
    print("-" * 30)
    after_summary = show_records_summary(conn)
    show_sample_records(conn, 3)
    
    # Show changes
    days_difference = after_summary['total_days_used'] - before_summary['total_days_used']
    print(f"\n7. Summary of changes:")
    print("-" * 30)
    print(f"  Records recalculated: {before_summary['completed_records']}")
    print(f"  Total days before: {before_summary['total_days_used']}")
    print(f"  Total days after: {after_summary['total_days_used']}")
    print(f"  Difference: {days_difference:+d} days")
    
    if days_difference != 0:
        print(f"\n  Note: The difference of {days_difference:+d} days is expected due to the")
        print("  algorithm change from 5-day + weekend logic to 6-day work week logic.")
    else:
        print("\n  Note: No change in total days - this may happen if the specific")
        print("  date ranges in your data produce the same results with both algorithms.")
    
    print(f"\n✅ RECALCULATION COMPLETE")
    print(f"Backup saved at: {backup_path}")
    
    conn.close()


if __name__ == "__main__":
    main()