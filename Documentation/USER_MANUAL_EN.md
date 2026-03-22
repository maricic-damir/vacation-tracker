# Vacation Tracker - User Manual (English)

## Table of Contents
1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [First Run Configuration](#first-run-configuration)
4. [User Interface Overview](#user-interface-overview)
5. [Managing Employees](#managing-employees)
6. [Managing Vacation Days](#managing-vacation-days)
7. [Holiday Management](#holiday-management)
8. [Business Rules and Calculations](#business-rules-and-calculations)
9. [Reports and Printing](#reports-and-printing)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

**Vacation Tracker** is a desktop application designed to help you track employee vacation days in compliance with Serbian labor laws. The application is built for Windows and can be shared between two users by storing the database file in a synchronized folder (e.g., OneDrive).

### Key Features
- Track vacation days for multiple employees
- Automatic calculation of working days (excludes weekends and holidays)
- Support for different contract types (fixed-term and open-ended)
- Religion-based holiday filtering (Orthodox and Catholic)
- Automatic year-end rollover of unused vacation days
- Complete vacation history and reporting
- Bilingual interface (English and Serbian)

---

## Installation and Setup

### System Requirements
- **Operating System:** Windows 10 or later (can also run on macOS/Linux with Python)
- **Python:** 3.10 or higher (only if running from source)
- **Disk Space:** ~50 MB for application + database

### Installation Options

#### Option 1: Using the Standalone EXE (Recommended for Windows)
1. Download `VacationTracker.exe` from your distribution source
2. Place the EXE file in a folder of your choice
3. Double-click `VacationTracker.exe` to run
4. No Python installation required!

#### Option 2: Running from Source Code
1. Install Python 3.10 or higher from [python.org](https://python.org)
2. Extract the vacation_tracker folder to your desired location
3. Open Command Prompt or Terminal in the vacation_tracker folder
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python main.py
   ```

### Building the EXE Yourself (Advanced)
If you want to build the standalone EXE from source:
```bash
pip install pyinstaller
pyinstaller vacation_tracker.spec
```
The EXE will be created in the `dist/` folder.

---

## First Run Configuration

### Database Location Setup

When you run the application for the first time, you'll be asked to choose where to store the database file.

#### First-Time Setup (No Existing Database)
1. A dialog will appear: **"Choose database location"**
2. Click **Browse** to select a folder
3. **Important:** If sharing with another user, choose a synchronized folder (e.g., OneDrive, Google Drive)
4. Click **Save**
5. The file `vacation.db` will be created in the selected folder

#### Locating an Existing Database
If the application was previously configured but can't find the database (e.g., on a new computer or after moving files):
1. A dialog will appear: **"Locate database"**
2. Click **Browse** to find your existing `vacation.db` file
3. Navigate to where the file is stored (e.g., OneDrive folder)
4. Select the file and click **Open**

### Configuration File Location
The application remembers your database location in a configuration file:
- **Windows:** `C:\Users\YourName\AppData\Roaming\VacationTracker\config.ini`
- **macOS/Linux:** `~/.VacationTracker/config.ini`

This file contains only the path to your database - it does NOT contain the actual employee data.

---

## User Interface Overview

### Main Screens

The application has three main screens:

#### 1. Employee List Screen (Home Screen)
This is the main screen you see when you open the application.

**What You See:**
- Table showing all employees with columns:
  - **JMBG:** Employee's unique identification number
  - **Name:** Full name (First + Last)
  - **Contract:** Contract type (Fixed term / Open-ended)
  - **Contract Start:** Date when employment started
  - **Days Left:** Remaining vacation days for current year
  - **Status:** Active or Archived

**Actions You Can Take:**
- **Double-click a row:** Opens detailed view for that employee
- **Add Employee button:** Add a new employee to the system
- **All Schedules button:** View all scheduled and completed vacations
- **Holidays / Settings button:** Manage public holidays and non-working days

**Language Toggle:**
- Top-right corner: Switch between English and Serbian

#### 2. Employee Detail Screen
Opens when you double-click an employee from the list.

**What You See:**
- **Employee Details:** JMBG, name, contract information, religion
- **Year Balance Table:** Shows vacation day breakdown for the current year
  - Days at Start: Initial allocation for the year (20 for open-ended contracts)
  - Transferred: Days carried over from previous year (valid until June only)
  - Earned: Additional days earned (blood donation, overtime, etc.)
  - Used: Total days taken
  - Left: Remaining days available
- **Used Days Off Table:** All completed vacations with deduction details
- **Earned Days Table:** History of earned additional days

**Actions You Can Take:**
- **Back to List:** Return to employee list
- **Contract Date / Type button:** Edit contract information and religion
- **Set Transferred Days button:** Set how many days were transferred from previous year
- **Schedule Vacation / Day Off button:** Book new vacation period
- **Add Earned Days button:** Add extra days earned (blood donation, etc.)
- **Print button:** Generate a printable report for this employee

#### 3. All Schedules Screen
Shows all vacation records across all employees.

**What You See:**
- Table with columns:
  - **JMBG:** Employee identifier
  - **Name:** Employee name
  - **Booking Date:** When the vacation was scheduled
  - **Start:** Vacation start date
  - **End:** Vacation end date
  - **Days:** Number of working days deducted
  - **Status:** Completed or Scheduled

**Actions You Can Take:**
- **Back to List:** Return to employee list
- View all vacations in one place for planning purposes

---

## Managing Employees

### Adding a New Employee

1. From the **Employee List** screen, click **Add Employee**
2. Fill in the form:
   - **JMBG:** 13-digit unique identification number (required, must be unique)
   - **First Name:** Employee's first name (required)
   - **Last Name:** Employee's last name (required)
   - **Religion:** Orthodox or Catholic (affects which holidays apply)
   - **Contract Type:** 
     - **Open-ended:** Permanent employment (automatically gets 20 days per year)
     - **Fixed term:** Temporary contract
   - **Start Contract Date:** When employment began (optional, used for prorating)
   - **Contract End Date:** When contract expires (only for fixed-term contracts)
3. Click **Save**

**Important Notes:**
- Open-ended contracts automatically receive 20 vacation days at the start of each calendar year (Serbian law)
- Fixed-term contracts start with 0 days and must be manually configured
- Religion setting determines which religious holidays count as non-working days

### Editing Employee Contract Information

1. Open the employee's detail screen (double-click from list)
2. Click **Contract Date / Type**
3. Modify the information:
   - Change contract type (fixed-term ↔ open-ended)
   - Update contract end date
   - Update start contract date
   - Change religion (Orthodox ↔ Catholic)
4. Click **Save**

**Effect of Changes:**
- Changing from fixed-term to open-ended will grant 20 days for the current year
- Changing religion will recalculate existing vacation records based on the new holiday set

### Archiving Employees

Currently, employees cannot be deleted from the system (to preserve historical records). However, inactive employees can be marked with "Archived" status to hide them from active lists.

*Note: This feature may be added in a future version.*

---

## Managing Vacation Days

### Understanding Day Types

The application tracks three types of vacation days:

1. **Days at Start**
   - Allocated at the beginning of each year
   - 20 days for open-ended contracts
   - 0 days for fixed-term contracts (unless manually set)

2. **Transferred Days**
   - Unused days from previous year
   - **Important:** Only valid until June 30 of the current year
   - After June, transferred days are no longer counted in "Days Left"

3. **Earned Days**
   - Extra days earned during the year
   - Examples: blood donation, overtime compensation, special recognition
   - These days can be used any time

### Deduction Priority Order

When an employee takes vacation, days are deducted in this order:

1. **First:** Transferred days (from previous year)
2. **Second:** Days at start (this year's allocation)
3. **Third:** Earned days (blood donation, etc.)

This ensures transferred days are used before they expire in June.

### Scheduling a Vacation

1. Open the employee's detail screen
2. Click **Schedule Vacation / Day Off**
3. Enter vacation details:
   - **Booking Date:** Today's date (automatically filled)
   - **Start Date:** First day of vacation
   - **End Date:** Last day of vacation
4. Click **Save**

**What Happens:**
- The application calculates working days between start and end dates
- Weekends (Saturday/Sunday) are automatically excluded
- Public holidays are automatically excluded (based on employee's religion)
- Days are deducted according to priority order
- If start date is in the past, you'll see a warning (vacation is immediately marked as completed)

**Example:**
Employee books vacation from Monday, Jan 13, 2026 to Friday, Jan 17, 2026:
- Total calendar days: 5
- Working days: 5 (no weekends or holidays in this range)
- Days deducted: 5 working days

If the same period included a public holiday (e.g., Jan 15 is a holiday):
- Total calendar days: 5
- Working days: 4 (excluding Jan 15 holiday)
- Days deducted: 4 working days

### Adding Earned Days

When an employee earns extra vacation days:

1. Open the employee's detail screen
2. Click **Add Earned Days**
3. Fill in the form:
   - **Date Earned:** Date when the days were earned
   - **Number of Days:** How many days to add
   - **Reason/Notes:** Why these days were earned (e.g., "Blood donation", "Overtime compensation")
4. Click **Save**

**Common Reasons for Earned Days:**
- Blood donation (1 day per donation, typically)
- Overtime compensation (as per company policy)
- Special recognition or awards
- Other contractual obligations

### Setting Transferred Days

At the beginning of each year, you may need to set how many days an employee is transferring from the previous year:

1. Open the employee's detail screen
2. Click **Set Transferred Days**
3. Select the year (usually the current year)
4. Enter the number of transferred days
5. Click **Save**

**Important:**
- This should be done early in the year (January)
- Transferred days are only valid until June 30
- After June, these days no longer count in the "Days Left" calculation

### Automatic Completion of Vacations

The application automatically marks vacations as "completed" when their end date passes:

- **On Startup:** Any vacation with `end_date < today` is marked completed
- **Deductions Applied:** Working days are calculated and deducted from appropriate buckets
- **Status Changed:** From "Scheduled" to "Completed"

You don't need to do anything - this happens automatically!

---

## Holiday Management

### Understanding Working Days

**Vacation days now count only working days!**

The application automatically excludes:
- **Weekends:** Saturday and Sunday are NEVER counted
- **Public Holidays:** Serbian state and religious holidays

### Loading Public Holidays

#### Method 1: Automatic Fetch from Ministry Website (Recommended)

1. From the **Employee List** screen, click **Holidays / Settings**
2. In the dialog, select the year (e.g., 2026)
3. Click **Fetch from Ministry Website**
4. Review the loaded holidays in the table
5. Click **Save**
6. Wait for recalculation (existing vacation records will be updated)

**What Holidays Are Loaded:**
- State holidays (apply to everyone)
- Orthodox holidays (apply to Orthodox employees)
- Catholic holidays (apply to Catholic employees)

For 2026, this includes approximately 17 holidays:
- New Year: Jan 1-2 (state)
- Orthodox Christmas: Jan 7 (Orthodox only)
- Statehood Day: Feb 15-17 (state)
- Orthodox Easter: Apr 10-13 (Orthodox only)
- Catholic Easter: Apr 3-6 (Catholic only)
- Labour Day: May 1-2 (state)
- Armistice Day: Nov 11 (state)

#### Method 2: Manual Entry

If you need to add a holiday that isn't in the official list:

1. Click **Holidays / Settings**
2. Select the year
3. In the table, you can manually add rows:
   - **Date:** Select the date
   - **Name (Serbian):** Holiday name in Serbian
   - **Name (English):** Holiday name in English
   - **Type:** State, Orthodox, Catholic, or Other Religious
4. Click **Save**

### Religion-Based Holiday Filtering

**How It Works:**
- **State holidays:** Apply to ALL employees (Orthodox and Catholic)
- **Orthodox holidays:** Only apply to employees marked as Orthodox
- **Catholic holidays:** Only apply to employees marked as Catholic

**Example:**
Orthodox Christmas (Jan 7) is a non-working day:
- For **Orthodox** employee: Jan 7 is excluded from vacation day count
- For **Catholic** employee: Jan 7 is a regular working day (counts toward vacation)

**Why This Matters:**
This ensures fair treatment according to Serbian labor law, which respects religious holidays for each faith.

### Clearing Holidays

If you need to clear all holidays for a specific year:

1. Click **Holidays / Settings**
2. Select the year
3. Click **Clear All Holidays for Year**
4. Confirm the action
5. All holidays for that year will be deleted

**Warning:** This will recalculate all vacation records! Use with caution.

### Annual Maintenance

**At the start of each new year:**
1. Click **Holidays / Settings**
2. Select the new year (e.g., 2027)
3. Click **Fetch from Ministry Website**
4. Review and click **Save**

This takes about 30 seconds and ensures accurate calculations for the new year.

---

## Business Rules and Calculations

### Automatic Calculations

The application handles many calculations automatically:

#### 1. Working Days Calculation
When a vacation is scheduled:
- Count all calendar days between start and end dates (inclusive)
- Exclude weekends (Saturday/Sunday)
- Exclude public holidays (based on employee's religion)
- Result = actual working days to deduct

#### 2. Day Deduction Priority
Days are deducted in this order:
1. Transferred days (from previous year)
2. Days at start (this year's allocation)
3. Earned days (additional days)

This is visible in the employee detail screen's "Used Days Off" table.

#### 3. Transferred Days Expiration
After June 30:
- Transferred days are no longer included in "Days Left" calculation
- They still appear in the balance table for reference
- Employees should be encouraged to use transferred days before June

#### 4. Open-Ended Contract Allocation
On January 1 of each year:
- Open-ended contracts automatically receive 20 days
- This is done during the year rollover process
- No manual intervention needed

### Contract Start Date Proration

If an employee starts mid-year with an open-ended contract:

**Example:** Employee starts on July 1, 2026
- Full year entitlement: 20 days
- Prorated for 6 months (July-December): 10 days
- Application automatically calculates this based on start date

**Formula:** `(20 days × months remaining) ÷ 12`

### Past Date Handling

If you try to schedule a vacation with a start date in the past:
1. You'll see a warning: "The start date is in the past. Do you want to continue?"
2. If you click **Yes**:
   - The vacation is saved
   - It's immediately marked as "Completed"
   - Days are deducted from the employee's balance

This is useful for entering historical vacation records.

---

## Reports and Printing

### Employee Detail Report

From the employee detail screen, click the **Print** button:

**What's Included:**
- Employee information (name, JMBG, contract details)
- Current year balance breakdown
- Complete list of used days off
- Complete list of earned days
- Summary totals

**Output Options:**
- Print directly to printer
- Save as PDF (if you have a PDF printer installed)

*Note: The print dialog is managed by your operating system.*

### Viewing All Schedules

Click **All Schedules** from the employee list:

**Use Cases:**
- See who is on vacation at specific dates
- Plan upcoming vacation schedules
- Verify vacation records across all employees
- Check for scheduling conflicts

**Filter/Sort Options:**
- Currently displays all records sorted by booking date
- Use Ctrl+F (in most browsers) to search within the table

*Note: Advanced filtering may be added in a future version.*

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database File Not Found

**Problem:** Application can't find `vacation.db` file

**Solutions:**
- Check if the file exists in the expected location (OneDrive folder)
- If using OneDrive, ensure it's fully synced (check OneDrive sync status)
- Use "Locate database" dialog to manually find the file
- If file is lost, you may need to restore from backup

#### 2. Incorrect Day Counts

**Problem:** Vacation days don't match your expectations

**Possible Causes:**
- Holidays not loaded for the year → Load holidays first
- Wrong religion set for employee → Check employee's religion setting
- Calculation includes weekends → This shouldn't happen; check dates
- Transferred days expired after June → This is expected behavior

**Solution:**
- Verify holidays are loaded: Click "Holidays / Settings" and check for your year
- Verify employee religion matches their actual faith
- Remember: Only working days are counted (not calendar days)

#### 3. Application Won't Start

**Problem:** Double-clicking EXE does nothing or shows error

**Solutions:**
- Check if antivirus is blocking the application
- Right-click → "Run as Administrator"
- If using Python: Check that all dependencies are installed (`pip install -r requirements.txt`)
- Check Windows Event Viewer for error details

#### 4. Changes Not Appearing on Other Computer

**Problem:** Second user doesn't see updates made by first user

**Solutions:**
- Ensure both users are NOT running the application simultaneously
- Check OneDrive sync status on both computers
- Close and reopen the application to reload the database
- Allow 1-2 minutes for OneDrive to sync changes

#### 5. Wrong Year Showing

**Problem:** Year balance shows the wrong year or no data

**Solutions:**
- Ensure year balance was created for the current year
- Check if employee needs year rollover from previous year
- Verify contract type is set correctly (open-ended should auto-allocate 20 days)

### Best Practices

1. **OneDrive Sharing:**
   - Only one user should run the application at a time
   - Wait for sync to complete before the other user opens the app
   - Check OneDrive sync status icon in system tray

2. **Regular Backups:**
   - Periodically copy `vacation.db` to a backup location
   - OneDrive versioning can help recover from accidental changes

3. **Year-End Process:**
   - In late December, prepare for year rollover
   - Remind employees to use transferred days before June
   - Load holidays for the new year in early January

4. **Data Entry:**
   - Enter vacations as soon as they're approved
   - Keep earned days records up to date with reasons
   - Use consistent naming in notes fields

---

## Keyboard Shortcuts

- **Double-click row:** Open employee details
- **Escape:** Close dialogs and return to previous screen
- **Tab:** Navigate between form fields
- **Enter:** Submit forms (when OK/Save button has focus)

---

## Support and Additional Help

### Technical Documentation

For developers and advanced users, see:
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `WORKING_DAYS_IMPLEMENTATION.md` - Working days calculation logic
- `RELIGION_IMPLEMENTATION.md` - Religion-based filtering
- `DEDUCTION_ORDER_IMPLEMENTATION.md` - Day deduction priority

### Database Schema

The application uses SQLite with the following main tables:
- `employees` - Employee information
- `employee_year_balance` - Yearly vacation day allocations
- `vacation_records` - All scheduled and completed vacations
- `earned_days` - Additional days earned
- `non_working_days` - Public holidays

You can use any SQLite browser to inspect the database if needed.

---

## Version Information

**Current Version:** 1.0

**Changelog:**
- Working days calculation (excludes weekends and holidays)
- Religion-based holiday filtering (Orthodox/Catholic)
- Deduction tracking (shows which bucket days came from)
- Bilingual support (English/Serbian)
- Automatic vacation completion
- Year rollover functionality
- Holiday management interface

---

## License and Legal

This application is provided as-is for tracking vacation days in accordance with Serbian labor law. Users are responsible for ensuring compliance with applicable laws and regulations.

**Data Privacy:**
- All data is stored locally in your `vacation.db` file
- No data is sent to external servers
- You control where the database is stored
- Regular backups are recommended

---

## Quick Reference Card

### First-Time Setup
1. Run application → Choose database location (OneDrive recommended)
2. Click "Holidays / Settings" → Select year → "Fetch from Ministry Website" → Save
3. Add employees via "Add Employee" button

### Daily Use
1. **Schedule vacation:** Double-click employee → "Schedule Vacation" → Enter dates → Save
2. **Check days left:** View "Days Left" column in employee list
3. **Add earned days:** Double-click employee → "Add Earned Days" → Enter info → Save

### Year-End
1. Load holidays for new year (January)
2. Set transferred days for employees (early January)
3. Verify all previous year vacations are marked completed

### Common Tasks
- **Change contract:** Employee detail → "Contract Date / Type"
- **View all vacations:** "All Schedules" button
- **Print report:** Employee detail → "Print" button
- **Switch language:** Top-right corner dropdown

---

*End of User Manual*
