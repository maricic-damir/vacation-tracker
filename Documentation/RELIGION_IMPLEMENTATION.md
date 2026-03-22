# Religion-Based Holiday Filtering Implementation

## Summary

Successfully implemented religion-based holiday filtering so that Orthodox and Catholic employees only have their respective religious holidays counted as non-working days. State holidays apply to everyone.

## What Was Implemented

### 1. Database Schema Updates

**Added `religion` field to `employees` table:**
```sql
ALTER TABLE employees ADD COLUMN religion TEXT NOT NULL DEFAULT 'orthodox' 
CHECK (religion IN ('orthodox', 'catholic'));
```

**Updated `non_working_days` table constraint:**
```sql
holiday_type TEXT CHECK (holiday_type IN ('state', 'orthodox', 'catholic', 'other_religious'))
```

### 2. Migration Function

**`migrate_add_religion()`** in `database.py`:
- Adds `religion` column to existing employees table
- Defaults all existing employees to 'orthodox'
- Recalculates all vacation records with new filtering

### 3. Holiday Filtering Logic

**New function: `is_non_working_day_for_employee()`** in `database.py`:
- Checks employee's religion
- State holidays (`'state'`) → apply to **everyone**
- Orthodox holidays (`'orthodox'`) → apply only to **Orthodox employees**
- Catholic holidays (`'catholic'`) → apply only to **Catholic employees**
- Other religious holidays → don't apply to Orthodox or Catholic

**Updated: `count_working_days_in_range()`** in `db_helpers.py`:
- Now accepts `employee_id` parameter
- Uses `is_non_working_day_for_employee()` instead of `is_non_working_day()`
- Filters holidays based on employee's religion

### 4. UI Changes

**AddEmployeeDialog** (`ui/dialogs.py`):
- Added **"Religion"** dropdown with options: Orthodox, Catholic
- Returns `religion` in dialog data
- Default: Orthodox

**ContractDialog** (`ui/dialogs.py`):
- Added **"Religion"** dropdown
- Allows changing employee religion
- Positioned at top of dialog for visibility

**ManageNonWorkingDaysDialog** (`ui/dialogs.py`):
- Added **"Applies To"** column showing:
  - "Everyone" for state holidays
  - "Orthodox only" for Orthodox holidays
  - "Catholic only" for Catholic holidays
- Updated to support 'catholic' holiday type in dropdowns

### 5. Data Updates

**Updated `holiday_scraper.py`:**
- Added 4 Catholic holidays for 2026:
  - Catholic Good Friday (Apr 3)
  - Catholic Easter Sunday (Apr 5)
  - Catholic Easter Monday (Apr 6)
  - Catholic Christmas (Dec 25)
- Total: 17 holidays (8 state, 5 Orthodox, 4 Catholic)

### 6. Database Function Updates

**`insert_employee()`** - added `religion` parameter
**`update_employee_contract()`** - added optional `religion` parameter
**Recalculation functions** - now pass `employee_id` to working days calculation

## Test Results

### ✅ All Religion-Based Tests Passed

```
Test 1: Orthodox Christmas (Jan 7)
  Orthodox: 4 working days (excluded)
  Catholic: 5 working days (counted)
  
Test 2: Catholic Christmas (Dec 25)
  Orthodox: 5 working days (counted)
  Catholic: 4 working days (excluded)

Test 3: Labour Day (May 1 - state holiday)
  Orthodox: 4 working days (excluded)
  Catholic: 4 working days (excluded)
  
Test 4: Orthodox Easter (Apr 10-13)
  Orthodox: 0 working days (all excluded)
  Catholic: 2 working days (Fri + Mon counted)

Test 5: Catholic Easter (Apr 3-6)
  Orthodox: 2 working days (Fri + Mon counted)
  Catholic: 0 working days (all excluded)
```

## Business Rules

### Holiday Application Rules

1. **State Holidays** - Apply to ALL employees regardless of religion:
   - New Year (Jan 1-2)
   - Statehood Day (Feb 15-17)
   - Labour Day (May 1-2)
   - Armistice Day (Nov 11)

2. **Orthodox Holidays** - Apply ONLY to Orthodox employees:
   - Orthodox Christmas (Jan 7)
   - Orthodox Easter (4 days: Good Friday through Easter Monday)

3. **Catholic Holidays** - Apply ONLY to Catholic employees:
   - Catholic Easter (3 days: Good Friday, Easter Sunday, Easter Monday)
   - Catholic Christmas (Dec 25)

### Working Days Calculation

For each employee, working days = weekdays **minus**:
- All weekends (Sat/Sun)
- State holidays
- **Only** their religion's holidays

### Example Scenarios

**Scenario 1: Orthodox employee books Jan 5-9**
- Jan 5 (Mon): Working ✓
- Jan 6 (Tue): Working ✓
- Jan 7 (Wed): Orthodox Christmas ✗
- Jan 8 (Thu): Working ✓
- Jan 9 (Fri): Working ✓
**Result: 4 working days**

**Scenario 2: Catholic employee books Jan 5-9**
- Jan 5 (Mon): Working ✓
- Jan 6 (Tue): Working ✓
- Jan 7 (Wed): Working ✓ (Orthodox Christmas doesn't apply)
- Jan 8 (Thu): Working ✓
- Jan 9 (Fri): Working ✓
**Result: 5 working days**

## Files Modified

### Database Layer
- `database.py` - Schema, migration, filtering function
- `db_helpers.py` - Working days calculation with employee context

### UI Layer
- `ui/dialogs.py` - Religion selector in dialogs, holiday type display
- `ui/screen_employees.py` - Pass religion when creating employee
- `ui/screen_employee_detail.py` - Pass religion when updating contract

### Data Layer
- `holiday_scraper.py` - Added Catholic holidays

### Tests
- `test_religion_filtering.py` - Comprehensive religion-based tests

## Migration Impact

### For Existing Databases

When opening an existing database:
1. `migrate_add_religion()` runs automatically
2. All existing employees default to `religion = 'orthodox'`
3. All vacation records are recalculated with religion-based filtering
4. No data loss, fully backward compatible

### For Existing Employees

Users can update employee religion via:
1. **Contract Dialog** - "Contract date / type" button
2. Change **"Religion"** dropdown
3. Save - vacation records auto-recalculate

## User Workflow

### Adding New Employee
1. Click "Add employee"
2. Fill JMBG, names
3. Select **Religion**: Orthodox or Catholic
4. Select contract type and dates
5. Save

### Changing Employee Religion
1. Open employee details
2. Click "Contract date / type"
3. Change **Religion** dropdown
4. Save - all vacation balances recalculate automatically

### Managing Holidays
1. Click "Manage Non-Working Days"
2. Fetch or add holidays
3. See "Applies To" column showing who each holiday affects
4. Save

## Future Extensions

Potential additions:
- [ ] Support for other religions (Muslim, Jewish)
- [ ] Custom per-employee holiday overrides
- [ ] Holiday calendar preview per employee
- [ ] Bulk religion update for multiple employees

## Key Insights

### Why This Matters

In Serbia:
- **State law** mandates state holidays for everyone
- **Labor law** allows employees to take days off for their religious holidays
- Orthodox and Catholic calendars differ significantly
- Proper tracking ensures fair treatment and legal compliance

### Design Decisions

1. **Default to Orthodox**: Serbia is predominantly Orthodox (~85%)
2. **Two religions only**: Covers 99%+ of employees (user can add more later)
3. **State holidays universal**: Legal requirement
4. **Automatic recalculation**: Ensures data consistency
5. **UI prominence**: Religion selector at top of dialogs

## Testing

Run religion-based tests:
```bash
python3 test_religion_filtering.py
```

Expected: All 7 tests pass ✓

## Documentation

- **Technical**: This file
- **User Guide**: See updated README.md
- **Quick Start**: QUICK_START.md includes religion info

---

**Implementation Date:** 2026-03-22  
**Status:** ✅ Complete and Tested  
**Backward Compatible:** Yes  
**Migration Required:** Automatic on first run
