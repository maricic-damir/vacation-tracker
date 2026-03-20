# Vacation Tracker

Desktop app for tracking employee vacation days (Windows). Uses **PyQt6** and **SQLite**; database file can be stored in a **OneDrive** folder for sharing between two users (non-concurrent use).

## Features

- **Screen 1 – Employee list**: JMBG, name, contract type (fixed term / open-ended), total vacation days left. Double-click a row to open employee details. Buttons: Add employee, Schedule vacation/day off, All scheduled/used days.
- **Screen 2 – Employee details**: Properties, year balance (days at start, transferred from previous year, earned, used, left), tables of used days off and earned days. Buttons: Contract date/type, Set transferred days, Schedule vacation/day off, Add earned days.
- **Screen 3 – All schedules**: Table of all vacation/day-off records (JMBG, name, booking date, start/end). Back to list.

Business rules:

- **Open-ended contract**: 20 days at start of each calendar year (by law).
- **Transferred days** from previous year count only until **June** of the current year; after that they are not included in “days left”.
- **Past start date**: Saving a vacation with start date in the past shows a warning; on confirm, the record is saved and marked as used.
- **Completion job**: On startup, any record with `end_date < today` is marked completed (used days are already counted in balance).

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
