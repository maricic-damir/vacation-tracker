# Quick Start: Non-Working Days Feature

## What's New?

Your Vacation Tracker now calculates vacation days based on **working days only** - weekends (Saturday/Sunday) and Serbian public holidays are automatically excluded!

---

## How to Get Started (3 Steps)

### Step 1: Run the Application
```bash
cd /Users/d.maricic/vacation_tracker
python3 main.py
```

### Step 2: Load Public Holidays
1. Look for the new button: **"Manage Non-Working Days"**
2. Click it
3. Select year: **2026** (or current year)
4. Click **"Fetch from Ministry Website"**
5. You'll see 13 Serbian holidays loaded
6. Click **"Save"**
7. Wait a moment for recalculation (existing records will be updated)

### Step 3: Done!
From now on, all vacation calculations automatically:
- ✅ Exclude weekends (Sat/Sun)
- ✅ Exclude public holidays you loaded
- ✅ Count only working days

---

## Example

**Before:** Employee books Jan 1-5, 2026 = 5 calendar days deducted

**After:** 
- Jan 1 (Thu) = Holiday ❌
- Jan 2 (Fri) = Holiday ❌
- Jan 3 (Sat) = Weekend ❌
- Jan 4 (Sun) = Weekend ❌
- Jan 5 (Mon) = Working day ✅

**Result:** Only 1 working day deducted!

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

## Annual Maintenance

At the start of each new year:
1. Click "Manage Non-Working Days"
2. Select the new year
3. Click "Fetch from Ministry Website"
4. Save

That's it! Takes 30 seconds.

---

Enjoy your improved vacation tracker! 🎉
