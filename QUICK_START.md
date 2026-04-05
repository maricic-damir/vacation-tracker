# Quick Start: Working Days & Holidays Features

## What's New?

Your Vacation Tracker now supports:
1. **Working Days Per Week**: Choose between 5-day (Mon-Fri) or 6-day work weeks
2. **Smart Holiday Calculation**: Weekends and Serbian public holidays are automatically excluded
3. **Flexible Vacation Entitlements**: 20 days for 5-day workers, 24 days for 6-day workers

---

## How to Get Started (4 Steps)

### Step 1: Run the Application
```bash
cd /Users/d.maricic/vacation_tracker
python3 main.py
```

### Step 2: Set Working Days for Employees
When adding new employees, you'll now see a **"Working days per week"** option:
- **6 days per week**: Traditional schedule (24 vacation days/year)
- **5 days per week (Mon-Fri)**: Modern schedule (20 vacation days/year)

For existing employees:
1. Click on an employee
2. Click **"Contract date / type"**
3. Set their working days per week
4. Save

### Step 3: Load Public Holidays
1. Look for the new button: **"Manage Non-Working Days"**
2. Click it
3. Select year: **2026** (or current year)
4. Click **"Fetch from Ministry Website"**
5. You'll see 13 Serbian holidays loaded
6. Click **"Save"**
7. Wait a moment for recalculation (existing records will be updated)

### Step 4: Done!
From now on, all vacation calculations automatically:
- ✅ Respect employee work schedules (5 or 6 days/week)
- ✅ Exclude appropriate weekends (Sat/Sun for 5-day, Sun only for 6-day)
- ✅ Exclude public holidays you loaded
- ✅ Count only working days
- ✅ Provide correct vacation entitlements (20 or 24 days)

---

## Examples

### 5-Day Work Week Employee
Employee books Jan 1-5, 2026:
- Jan 1 (Thu) = Holiday ❌
- Jan 2 (Fri) = Holiday ❌  
- Jan 3 (Sat) = Weekend ❌
- Jan 4 (Sun) = Weekend ❌
- Jan 5 (Mon) = Working day ✅

**Result:** Only 1 working day deducted from 20-day entitlement!

### 6-Day Work Week Employee  
Employee books Jan 1-5, 2026:
- Jan 1 (Thu) = Holiday ❌
- Jan 2 (Fri) = Holiday ❌
- Jan 3 (Sat) = Working day ✅
- Jan 4 (Sun) = Weekend ❌
- Jan 5 (Mon) = Working day ✅

**Result:** 2 working days deducted from 24-day entitlement!

---

## Testing

To verify everything works:
```bash
python3 test_working_days.py
```

Should show: **✓ ALL TESTS PASSED!**

---

## Need Help?

- **Can't fetch holidays?** Internet connection required, or add manually
- **Wrong day count?** Make sure holidays are loaded for the correct year
- **Questions?** See `IMPLEMENTATION_SUMMARY.md` for full details

---

## What Holidays Are Included?

For 2026 (13 days):
- New Year (Jan 1-2)
- Orthodox Christmas (Jan 7)
- Statehood Day (Feb 15-17)
- Orthodox Easter (Apr 10-13)
- Labour Day (May 1-2)
- Armistice Day (Nov 11)

You can add, edit, or remove any holiday using the "Manage Non-Working Days" dialog.

---

## Key Features Explained

### Working Days Per Week
- **5 days (Mon-Fri)**: Modern office schedule
  - 20 vacation days per year
  - Saturdays and Sundays are weekends (not deducted)
  - Perfect for office workers, remote workers
  
- **6 days**: Traditional schedule  
  - 24 vacation days per year
  - Only Sundays are weekends (not deducted)
  - Saturdays are working days (deducted if on vacation)

### Employee Details
Each employee's details page now shows:
- Working days per week (5 or 6)
- Vacation entitlement based on their schedule
- Proper weekend deduction calculations

## Annual Maintenance

At the start of each new year:
1. Click "Manage Non-Working Days"
2. Select the new year  
3. Click "Fetch from Ministry Website"
4. Save
5. Review employee working schedules if needed

That's it! Takes 1 minute.

---

Enjoy your improved vacation tracker! 🎉
