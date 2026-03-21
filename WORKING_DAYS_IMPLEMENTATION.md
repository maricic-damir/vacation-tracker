# Working Days & Non-Working Days Implementation

## Overview

This implementation adds support for **working days calculation** (excluding weekends and public holidays) and a **holiday management system** for Serbian public holidays.

## Key Changes

### 1. Database Schema (`database.py`)

**New Table: `non_working_days`**
```sql
CREATE TABLE IF NOT EXISTS non_working_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    name_sr TEXT NOT NULL,           -- Serbian name
    name_en TEXT,                    -- English name (optional)
    holiday_type TEXT NOT NULL,      -- 'state', 'orthodox', 'other_religious'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

**Migration Function: `migrate_add_non_working_days()`**
- Automatically runs on database initialization
- Recalculates all existing vacation records using working days logic

**CRUD Functions:**
- `get_non_working_days(conn, year)` - Fetch holidays for a year
- `is_non_working_day(conn, date)` - Check if date is a holiday
- `save_non_working_days(conn, holidays)` - Bulk insert/update
- `delete_non_working_day(conn, id)` - Delete single holiday
- `clear_non_working_days(conn, year)` - Delete all for a year

### 2. Working Days Calculation (`db_helpers.py`)

**New Function: `count_working_days_in_range(conn, start_date, end_date)`**
- Counts only Monday-Friday
- Excludes public holidays from database
- Replaces calendar days logic in vacation calculations

**Updated Function: `_used_days_in_year()`**
- Now uses `count_working_days_in_range()` instead of counting all calendar days
- Automatically considers weekends and holidays

### 3. Holiday Scraper (`holiday_scraper.py`)

**Main Function: `scrape_serbian_holidays(year)`**
Returns: `(holidays_list, source_info)`

**Data Sources (in order):**
1. **Tallyfy API** - `https://tallyfy.com/national-holidays/api/RS/{year}.json`
   - No authentication required
   - Reliable and well-maintained
   - Fallback if scraping fails

2. **Hardcoded 2026 Data** - Based on official Serbian Ministry
   - 13 holidays for 2026
   - State holidays: New Year, Statehood Day, Labour Day, Armistice Day
   - Orthodox holidays: Christmas, Easter (4 days)

**Helper Functions:**
- `_fetch_from_tallyfy(year)` - API call implementation
- `_infer_serbian_name_and_type(name_en, date)` - Map English to Serbian names
- `_get_hardcoded_2026_holidays()` - Fallback data
- `parse_custom_holiday(...)` - Validate custom entries

### 4. Holiday Management Dialog (`ui/dialogs.py`)

**Class: `ManageNonWorkingDaysDialog`**

**Features:**
- Year selector (current year ± 7 years)
- "Fetch from Ministry Website" button
- Editable table with columns:
  - Include checkbox
  - Date (YYYY-MM-DD)
  - Name (Serbian) - editable
  - Name (English) - editable
  - Type dropdown (state/orthodox/other_religious)
- "Add Custom Holiday" - insert new row
- "Delete Selected" - remove rows
- "Save" - write to database and recalculate all records

**Validation:**
- Date format (YYYY-MM-DD)
- Required fields (date, Serbian name)
- Type must be valid enum value

**User Flow:**
1. Select year
2. Click "Fetch from Ministry Website"
3. Review scraped holidays in table
4. Edit names, dates, types as needed
5. Add custom holidays if needed
6. Uncheck any holidays to exclude
7. Click "Save"
8. Confirmation dialog shows count
9. System recalculates all vacation records
10. Success message

### 5. UI Integration (`ui/screen_employees.py`)

**New Button: "Manage Non-Working Days"**
- Positioned next to "Roll over to [Year]" button
- Opens `ManageNonWorkingDaysDialog`
- Refreshes employee list after save

**Handler: `_manage_holidays()`**
- Gets database connection
- Opens dialog
- Refreshes UI if changes saved

### 6. Vacation Scheduling Updates

**Updated in:**
- `ui/screen_employee_detail.py` - `_schedule_vacation()`
- `ui/screen_employees.py` - `_save_vacation()`

**Changes:**
- Import `count_working_days_in_range` instead of `count_days_in_range`
- Use working days for deduction calculation
- Applies to past-dated vacations (marked as completed)

## Business Logic

### Working Days Rules

**Excluded Days:**
1. **Weekends:** Saturday (5) and Sunday (6)
2. **Public Holidays:** From `non_working_days` table where `is_active = 1`

**Example Calculation:**
```
Vacation: Monday Jan 1 to Friday Jan 5, 2026
- Jan 1 (Thu): Holiday (New Year) → excluded
- Jan 2 (Fri): Holiday (New Year) → excluded
- Jan 3 (Sat): Weekend → excluded
- Jan 4 (Sun): Weekend → excluded
- Jan 5 (Mon): Working day → counted

Result: 1 working day deducted from balance
```

### Deduction Order (unchanged)

Vacation days are still deducted in priority order:
1. Transferred days (from previous year)
2. Days at start (this year's allocation)
3. Earned days (blood donation, overtime, etc.)

**But now:** Each "day" is a **working day**, not a calendar day.

### Automatic Recalculation

**When holidays are saved:**
- Function `recalculate_all_vacation_records_with_working_days()` runs
- Processes all completed vacation records
- Recalculates deduction breakdown using working days
- Updates `days_from_transferred`, `days_from_at_start`, `days_from_earned`

**Migration:**
- On first run with new schema, all existing records are recalculated
- Ensures historical data is consistent with new logic

## Testing Checklist

### Phase 1: Database & Working Days
- [x] Schema migration runs without errors
- [ ] Non-working days table is created
- [ ] Existing vacation records are recalculated
- [ ] Working days calculation excludes weekends
- [ ] Working days calculation excludes holidays

### Phase 2: Holiday Scraping
- [ ] Tallyfy API fetches 2026 holidays successfully
- [ ] Hardcoded 2026 data is available as fallback
- [ ] Serbian names are correctly mapped
- [ ] Holiday types are correctly assigned

### Phase 3: UI Dialog
- [ ] Dialog opens without errors
- [ ] Year selector shows correct range
- [ ] Fetch button loads holidays
- [ ] Table displays all columns correctly
- [ ] Checkboxes work for include/exclude
- [ ] Add custom holiday creates editable row
- [ ] Delete selected removes rows
- [ ] Validation catches invalid dates
- [ ] Save triggers recalculation
- [ ] Success message shows count

### Phase 4: Integration
- [ ] Button appears on employee list screen
- [ ] Button opens dialog correctly
- [ ] Save refreshes employee list
- [ ] New vacation scheduling uses working days
- [ ] Past vacation records show correct days used

### Phase 5: End-to-End
- [ ] Load 2026 holidays from API
- [ ] Save to database
- [ ] Create vacation record spanning weekend + holiday
- [ ] Verify only working days are deducted
- [ ] Check employee balance is correct

## Example Scenarios

### Scenario 1: New Year 2026
**Employee schedules vacation: Dec 29, 2025 (Mon) - Jan 5, 2026 (Mon)**

Calendar days: 8 days
Working days calculation:
- Dec 29 (Mon): Working → 1
- Dec 30 (Tue): Working → 1
- Dec 31 (Wed): Working → 1
- Jan 1 (Thu): Holiday → 0
- Jan 2 (Fri): Holiday → 0
- Jan 3 (Sat): Weekend → 0
- Jan 4 (Sun): Weekend → 0
- Jan 5 (Mon): Working → 1

**Result: 4 working days deducted** (instead of 8)

### Scenario 2: Orthodox Easter 2026
**Employee schedules vacation: Apr 10-13, 2026**

Calendar days: 4 days
Working days calculation:
- Apr 10 (Fri): Holiday (Good Friday) → 0
- Apr 11 (Sat): Weekend → 0
- Apr 12 (Sun): Holiday (Easter) → 0
- Apr 13 (Mon): Holiday (Easter Monday) → 0

**Result: 0 working days deducted** (all holidays/weekend)

## Files Modified

**New Files:**
- `holiday_scraper.py` - Web scraping and data fetching
- `WORKING_DAYS_IMPLEMENTATION.md` - This documentation

**Modified Files:**
- `database.py` - Schema, migration, CRUD functions
- `db_helpers.py` - Working days calculation
- `ui/dialogs.py` - Holiday management dialog
- `ui/screen_employees.py` - Button and handler
- `ui/screen_employee_detail.py` - Working days in scheduling

## Dependencies

**No new dependencies required!**
- Uses Python standard library `urllib` for HTTP requests
- Uses Python standard library `json` for parsing
- Uses existing PyQt6 for UI

## Usage Instructions

### For End Users

1. **First Time Setup (if needed):**
   - Click "Manage Non-Working Days" button
   - Select current year (e.g., 2026)
   - Click "Fetch from Ministry Website"
   - Review holidays, make any edits
   - Click "Save"
   - Wait for recalculation to complete

2. **Annual Maintenance:**
   - At start of each year:
     - Click "Manage Non-Working Days"
     - Select new year
     - Click "Fetch from Ministry Website"
     - Save holidays for new year

3. **Custom Holidays:**
   - Open "Manage Non-Working Days"
   - Click "Add Custom Holiday"
   - Enter date (YYYY-MM-DD), names, type
   - Click "Save"

### For Developers

**Adding New Data Sources:**
1. Create function in `holiday_scraper.py`
2. Return format: `(list[dict], str)` where dict has: `date, name_sr, name_en, holiday_type`
3. Add to `scrape_serbian_holidays()` chain
4. Test with various years

**Extending Holiday Types:**
1. Update schema CHECK constraint in `database.py`
2. Update combo box in `ManageNonWorkingDaysDialog`
3. Add new type to `_infer_serbian_name_and_type()` logic

## Known Limitations

1. **No official Ministry API:** We rely on third-party API (Tallyfy) or hardcoded data
2. **Year range:** Hardcoded data only available for 2026
3. **No automatic updates:** Users must manually fetch holidays each year
4. **Single country:** Currently only Serbia is supported

## Future Enhancements

- [ ] BeautifulSoup scraping from official Ministry website
- [ ] Multi-year bulk import
- [ ] Export holidays to CSV/JSON
- [ ] Holiday templates for common years
- [ ] Email reminders to update holidays
- [ ] Support for multiple countries
- [ ] Integration with iCal/Google Calendar

## Troubleshooting

**Issue: "No data available for year XXXX"**
- Solution: Add holidays manually or use 2026 as reference

**Issue: Vacation days not recalculating**
- Check that `recalculate_all_vacation_records_with_working_days()` ran
- Check database logs
- Manually trigger by saving holidays again

**Issue: Weekend still counted as working day**
- Check date format (must be YYYY-MM-DD)
- Verify `count_working_days_in_range()` logic
- Check if date is actually weekend (use Python's weekday())

**Issue: Tallyfy API fails**
- Check internet connection
- Check URL format
- Falls back to hardcoded 2026 data automatically
- Can add holidays manually

## Support

For issues or questions:
1. Check this documentation
2. Review code comments in modified files
3. Check terminal output for error messages
4. Add holidays manually if API fails
