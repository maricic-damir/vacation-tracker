# Vacation Day Deduction Order Implementation

## Summary

Implemented a deduction order system that tracks which bucket (transferred, at_start, or earned) vacation days are consumed from when completing vacation records.

## Deduction Order

Days are deducted in the following priority:

1. **Transferred days** (from previous year) - used first
2. **Days at start** (this year's allocation) - used second
3. **Earned days** (blood donation, overtime, etc.) - used last

## Changes Made

### 1. Database Schema (database.py)

Added three new columns to the `vacation_records` table:
- `days_from_transferred` - tracks days deducted from transferred bucket
- `days_from_at_start` - tracks days deducted from at_start bucket
- `days_from_earned` - tracks days deducted from earned bucket

**Migration**: Automatic migration runs on first connection to add columns to existing databases.

### 2. Deduction Calculator (db_helpers.py)

Added new helper functions:

- `calculate_deduction_breakdown()` - determines how many days to deduct from each bucket
- `get_available_days_for_deduction()` - calculates remaining available days per bucket
- Updated `get_year_balance()` - now returns breakdown showing remaining days per bucket:
  - `transferred_left`
  - `at_start_left`
  - `earned_left`

### 3. Completion Logic (database.py)

Updated `run_completion_job()`:
- Calculates deduction breakdown when marking records as completed
- Stores breakdown in the vacation_records table

### 4. Vacation Saving (ui/screen_employees.py, ui/screen_employee_detail.py)

Updated vacation scheduling:
- When saving a vacation with past end date (immediately completed), calculates deduction breakdown
- Passes breakdown to `add_vacation_record()`

### 5. UI Display (ui/screen_employee_detail.py)

Updated employee detail screen to show remaining days per bucket:
- Days at start: 20 (15 left)
- Transferred: 5 (0 left)
- Earned: 3 (3 left)

### 6. Retroactive Migration (database.py)

Added `recalculate_existing_vacation_deductions()`:
- Automatically runs when columns are first added
- Processes all existing completed vacation records in chronological order
- Calculates and stores deduction breakdown for historical records

### 7. Year Rollover (database.py)

Updated `rollover_year_for_employee()`:
- Uses per-bucket tracking to calculate unused days
- Rolls over: `transferred_left + at_start_left + earned_left`

## Testing

All edge cases tested:
- ✓ Deducting only from transferred days
- ✓ Deducting across buckets (transferred → at_start)
- ✓ Deducting across all three buckets (transferred → at_start → earned)
- ✓ Transferred days after December 31 (correctly excluded from available balance)
- ✓ Year rollover with per-bucket tracking

## Files Modified

1. `database.py` - schema, migration, completion job, rollover
2. `db_helpers.py` - deduction calculator, balance functions
3. `ui/screen_employees.py` - vacation saving logic
4. `ui/screen_employee_detail.py` - vacation saving and UI display

## Backward Compatibility

- Fully backward compatible with existing databases
- Automatic migration adds columns with default values (0)
- Retroactive calculation fills in breakdown for existing completed records
- No data loss or manual intervention required

## Usage

The system now automatically:
1. Tracks which bucket days come from when vacations are completed
2. Shows remaining days per bucket in the UI
3. Deducts in the correct priority order
4. Preserves historical records even after December 31 (when transferred days expire from available balance)
