  # Vacation Tracker

Desktop app for tracking employee vacation days (Windows). Uses **PyQt6** and **SQLite**; database file can be stored in a **OneDrive** folder for sharing between two users (non-concurrent use).

## Features

- **Screen 1 – Employee list**: JMBG, name, contract type (fixed term / open-ended), working days per week, total vacation days left. Double-click a row to open employee details. Buttons: Add employee, Schedule vacation/day off, All scheduled/used days, Manage Non-Working Days.
- **Screen 2 – Employee details**: Properties, year balance (days at start, transferred from previous year, earned, used, left), tables of used days off and earned days. Buttons: Contract date/type, Set transferred days, Schedule vacation/day off, Add earned days.
- **Screen 3 – All schedules**: Table of all vacation/day-off records (JMBG, name, booking date, start/end). Back to list.

Business rules:

- **Working Days Per Week**: Choose between 5-day (Mon-Fri) or 6-day work weeks
  - **5-day workers**: 20 vacation days per year, weekends (Sat-Sun) excluded from deductions
  - **6-day workers**: 24 vacation days per year, only Sundays excluded from deductions
- **Transferred days** from previous year count until **December 31** of the current year; after that they are not included in “days left”.
- **Past start date**: Saving a vacation with start date in the past shows a warning; on confirm, the record is saved and marked as used.
- **Completion job**: On startup, any record with `end_date < today` is marked completed (used days are already counted in balance).

**Note on deduction order**: When vacation days are used, they are deducted in priority order:
1. Transferred days (from previous year) - used first
2. Days at start (this year's allocation) - used second
3. Earned days (blood donation, overtime, etc.) - used last

The employee detail screen shows remaining days per bucket to track which buckets are being consumed.

## Requirements

- Python 3.10+
- PyQt6

## Setup

```bash
cd vacation_tracker
pip install -r requirements.txt
```

## Initial Configuration

After first run, configure your employees' working schedules:

1. **For new employees**: Select working days per week (5 or 6) when adding them
2. **For existing employees**: 
   - Click on employee → "Contract date/type" → Set working days per week
3. **Load holidays**: Click "Manage Non-Working Days" → Select year → "Fetch from Ministry Website" → Save

## Run

```bash
python main.py
```

**First run:** You'll be asked whether to create a new database or use an existing one:
- **Create New Database**: Choose where to store a new database file (e.g. OneDrive folder)  
- **Use Existing Database**: Browse and select an existing `vacation.db` file (recommended for shared setups)

**Later runs:** If the previously used database file is missing (e.g. moved or not yet synced), you'll be prompted to:
- **Find Existing Database** (recommended): Browse to locate the moved database file
- **Create New Database Here**: Create a fresh database at the previous location

**💡 Tip for Shared Databases:** Always choose "Use Existing Database" or "Find Existing Database" to avoid accidentally creating duplicate databases when the shared file is temporarily unavailable (OneDrive not synced, network drive disconnected, etc.)

## Build single EXE (Windows)

```bash
pip install pyinstaller
pyinstaller vacation_tracker.spec
```

The EXE will be in `dist/VacationTracker.exe`. Run it on the target Windows machine; first run will prompt for the database location (e.g. OneDrive folder).

## Database location

- Config (including last used DB path) is stored in:
  - **Windows:** `%APPDATA%\VacationTracker\config.ini`
  - **Other:** `~/.VacationTracker/config.ini`
- Put the SQLite file in a **OneDrive** (or shared) folder so both users open the same file. Use the app one at a time to avoid conflicts.

## New: Working Days & Holiday Management

**Vacation days now count working days only (excluding weekends and holidays)!**

- **5-day work week**: Monday-Friday are working days, weekends (Sat-Sun) excluded from deductions
- **6-day work week**: Monday-Saturday are working days, only Sundays excluded from deductions
- **Holidays excluded**: Serbian public holidays are never deducted from vacation balance
- **Flexible entitlements**: 20 days for 5-day workers, 24 days for 6-day workers
- **Validation**: System prevents booking more days than available
- **"Manage Non-Working Days" button**: Fetch holidays from web or enter manually
- **Automatic recalculation**: Existing vacation records are updated when holidays change
- **2026 holidays included**: 13 official Serbian holidays pre-configured

**Quick start:**
1. Run the app
2. Set working days per week for employees (5 or 6 days)
3. Click "Manage Non-Working Days" button
4. Select year 2026
5. Click "Fetch from Ministry Website"
6. Review and click "Save"

**Example:** 5-day worker requests Saturday-Sunday off (no holidays)
- **Deducted: 0 days** (weekends excluded for 5-day workers)

**Example:** 6-day worker requests Saturday-Sunday off (no holidays)
- **Deducted: 1 day** (Saturday is working day, Sunday excluded)

**Example:** 5-day worker books Dec 29, 2025 - Jan 5, 2026 (8 calendar days)
- Old behavior: 8 days deducted
- New behavior: 4 working days deducted (excludes Jan 1-2 state holidays + weekends)

**Example:** 6-day worker books same dates (Dec 29, 2025 - Jan 5, 2026)
- **Deducted: 5 working days** (includes Saturday Jan 4, excludes holidays and Sunday)

**Example:** Request Monday-Sunday (7 days, no holidays)
- **5-day worker: 5 days deducted** (Mon-Fri only)
- **6-day worker: 6 days deducted** (Mon-Sat only)

See `QUICK_START.md` and `Documentation/IMPLEMENTATION_SUMMARY.md` for detailed documentation.
