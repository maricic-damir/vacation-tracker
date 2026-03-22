# Weekend Day Deduction Implementation

## Overview

This implementation adds logic to deduct weekend days (Saturday and Sunday) from the vacation bucket when they are requested as day-offs, **excluding** days that are already defined as public holidays.

## Changes Made

### 1. New Functions in `db_helpers.py`

#### `count_weekend_days_excluding_holidays(conn, start_date, end_date, employee_id)`
- Counts Saturday and Sunday days in a date range
- **Excludes** weekend days that are already public holidays
- Uses employee-specific holiday filtering (respects religion-based holidays)

#### `count_total_deductible_days(conn, start_date, end_date, employee_id)`
- Combines working days and weekend days (excluding holidays)
- This is the total number of days that will be deducted from vacation bucket
- Returns: working days + non-holiday weekend days

### 2. Updated Validation Logic

Modified in both `ui/screen_employee_detail.py` and `ui/screen_employees.py`:

- **Before scheduling**: Calculates total deductible days using `count_total_deductible_days()`
- **Validation**: Checks if employee has enough days in their bucket
- **Error message**: Shows shortage if insufficient days available
- **Deduction order**: Still follows transferred → at_start → earned

Example validation:
```python
days_needed = count_total_deductible_days(conn, start_date, end_date, employee_id)
available = get_available_days_for_deduction(conn, employee_id, year)
total_available = available['transferred'] + available['at_start'] + available['earned']

if days_needed > total_available:
    # Show error message and prevent scheduling
    QMessageBox.warning(...)
    return
```

### 3. Updated Completion and Recalculation Logic

Modified in `database.py`:

- `run_completion_job()`: Uses `count_total_deductible_days()` instead of just working days
- `recalculate_existing_vacation_deductions()`: Updated to include weekend days
- `recalculate_all_vacation_records_with_working_days()`: Updated to include weekend days

Modified in `db_helpers.py`:

- `_used_days_in_year()`: Uses `count_total_deductible_days()` for accurate balance calculation

## Behavior

### What Gets Deducted

✅ **Deducted from bucket:**
- Monday-Friday (working days) that are NOT holidays
- Saturday-Sunday (weekend days) that are NOT holidays

❌ **NOT deducted from bucket:**
- Any day that is a defined public holiday (regardless of day of week)
- Example: If Easter Sunday is a holiday, it won't be deducted

### Examples

#### Example 1: Weekend Request
- Request: Saturday Jan 10 - Sunday Jan 11, 2026
- Holidays: None on these dates
- **Deducted: 2 days** (both weekend days count)

#### Example 2: Weekend with Holiday
- Request: Saturday Feb 14 - Sunday Feb 15, 2026
- Holidays: Feb 15 is Serbian Statehood Day (state holiday)
- **Deducted: 1 day** (only Saturday; Sunday is holiday)

#### Example 3: Full Week
- Request: Monday Jan 5 - Sunday Jan 11, 2026
- Holidays: None on these dates
- **Deducted: 7 days** (5 working + 2 weekend)

#### Example 4: Insufficient Days
- Employee has 5 days available
- Requests: Monday Jan 5 - Sunday Jan 11, 2026 (7 days needed)
- **Result: Request REJECTED** with error message showing shortage

### Deduction Order

The deduction order remains unchanged:
1. **Transferred days** (from previous year) - used first
2. **At start days** (current year allowance) - used second
3. **Earned days** (blood donation, overtime, etc.) - used last

This order applies to ALL deductions, whether they are working days or weekend days.

## Testing

Three comprehensive test files were created:

### `test_weekend_deduction.py`
- Tests basic weekend counting logic
- Verifies holidays are excluded from weekend count
- Confirms working days calculation unchanged

### `test_validation_weekend.py`
- Tests validation logic prevents over-booking
- Verifies rejection when insufficient days
- Confirms acceptance when exactly enough days

### `test_deduction_order_weekends.py`
- Tests correct deduction order with weekend days
- Verifies transferred → at_start → earned order maintained
- Confirms balance tracking accuracy

All tests pass successfully.

## User Impact

### Before This Change
- Weekend days were free (not counted)
- Users could take weekends without deducting from bucket
- Only working days (Mon-Fri) were deducted

### After This Change
- Weekend days are deducted from bucket (unless they are holidays)
- Users must have sufficient days to cover entire requested period
- More accurate tracking of actual time off
- Validation prevents booking if insufficient days

### UI Changes

When a user tries to request more days than available, they will see:

**English:**
```
Cannot schedule vacation.

Days needed: 7
Days available: 5

Shortage: 2 days
```

**Serbian:**
```
Не може се заказати одсуство.

Потребно дана: 7
Доступно дана: 5

Недостаје: 2 дана
```

## Database Migration

No database schema changes are required. The existing schema supports this functionality:

- `vacation_records` table already tracks deductions by bucket
- `non_working_days` table defines holidays
- Existing completed records will be recalculated automatically on next app launch

## Backward Compatibility

- Existing vacation records are automatically recalculated
- No manual intervention required
- Old data is updated to reflect new counting logic
- Balance calculations adjusted accordingly

## Technical Notes

### Weekend Detection
- Uses Python's `date.weekday()`: Monday=0, Sunday=6
- Saturday: `weekday() == 5`
- Sunday: `weekday() == 6`

### Holiday Filtering
- Respects employee religion for religious holidays
- State holidays apply to everyone
- Orthodox holidays apply only to Orthodox employees
- Catholic holidays apply only to Catholic employees

### Performance
- All functions iterate day-by-day through date range
- Efficient for typical vacation periods (days to weeks)
- Uses database queries for holiday lookups
