  # Vacation Tracker

Desktop app for tracking employee vacation days (Windows). Uses **PyQt6** and **SQLite**; database file can be stored in a **OneDrive** folder for sharing between two users (non-concurrent use).

## Features

- **Screen 1 – Employee list**: JMBG, name, contract type (fixed term / open-ended), total vacation days left. Double-click a row to open employee details. Buttons: Add employee, Schedule vacation/day off, All scheduled/used days.
- **Screen 2 – Employee details**: Properties, year balance (days at start, transferred from previous year, earned, used, left), tables of used days off and earned days. Buttons: Contract date/type, Set transferred days, Schedule vacation/day off, Add earned days.
- **Screen 3 – All schedules**: Table of all vacation/day-off records (JMBG, name, booking date, start/end). Back to list.

Business rules:

- **Open-ended contract**: 24 days at start of each calendar year (by law).
- **Transferred days** from previous year count only until **June** of the current year; after that they are not included in “days left”.
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

## Run

```bash
python main.py
```

**First run:** You will be asked where to store the database (e.g. a folder that syncs with OneDrive). The file is created as `vacation.db` (or the name you choose).

**Later runs:** If the app was run before on this machine but the database file is missing (e.g. moved or not yet synced), you will be asked to **locate** the existing `vacation.db` file.

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

**Vacation days now count working days + requested weekend days!**

- **Working days counted**: Monday-Friday (excluding holidays)
- **Weekend days counted**: Saturday-Sunday **are now deducted** unless they are holidays
- **Holidays excluded**: Serbian public holidays are never deducted
- **Religion-based filtering**: Orthodox employees get Orthodox holidays off, Catholic employees get Catholic holidays off, state holidays apply to everyone
- **Validation**: System prevents booking more days than available
- **"Manage Non-Working Days" button**: Fetch holidays from web or enter manually
- **Automatic recalculation**: Existing vacation records are updated when holidays change
- **2026 holidays included**: 17 holidays pre-configured (8 state, 5 Orthodox, 4 Catholic)

**Quick start:**
1. Run the app
2. Click "Manage Non-Working Days" button
3. Select year 2026
4. Click "Fetch from Ministry Website"
5. Review and click "Save"

**Example:** Request Saturday-Sunday off (no holidays on these dates)
- **Deducted: 2 days** from your vacation bucket

**Example:** Orthodox employee books Dec 29, 2025 - Jan 5, 2026 (8 calendar days)
- Old behavior: 8 days deducted
- New behavior: 4 working days deducted (excludes Jan 1-2 state holidays + Jan 7 Orthodox Christmas + weekend)

**Example:** Request Monday-Sunday (7 days, no holidays)
- **Deducted: 7 days** (5 working + 2 weekend)

**Example:** Request Saturday-Sunday where Sunday is a holiday
- **Deducted: 1 day** (only Saturday; Sunday is holiday)

Catholic employee booking same dates: 5 working days deducted (Jan 7 is a working day for them)

See `WEEKEND_DEDUCTION_QUICK_REFERENCE.md`, `QUICK_START.md`, `IMPLEMENTATION_SUMMARY.md`, and `RELIGION_IMPLEMENTATION.md` for detailed documentation.
