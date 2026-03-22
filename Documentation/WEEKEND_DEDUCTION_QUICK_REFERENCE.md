# Weekend Day Deduction - Quick Reference

## Summary

Starting with this update, **weekend days (Saturday and Sunday) are deducted from your vacation bucket** when you request them as day-offs, unless they are already defined as public holidays.

## Key Points

### What Changed?

**Before:**
- Only working days (Monday-Friday) were deducted from vacation bucket
- Weekend days were "free" and didn't count

**After:**
- Working days (Monday-Friday) AND weekend days (Saturday-Sunday) are deducted
- **Exception:** Weekend days that are public holidays are NOT deducted

### Examples

#### Example 1: Weekend Request
You request Saturday-Sunday off:
- **Deducted: 2 days**

#### Example 2: Full Week Request
You request Monday-Sunday off (7 days):
- **Deducted: 7 days** (5 working + 2 weekend)

#### Example 3: Weekend with Holiday
You request Saturday-Sunday off, but Sunday is a national holiday:
- **Deducted: 1 day** (only Saturday; Sunday is already a holiday)

#### Example 4: Insufficient Balance
You have 5 days available, you try to request Monday-Sunday (7 days):
- **Result: Request REJECTED** with error message

### Validation

The system now **validates before allowing** you to schedule vacation:

✅ **Allowed:**
- If you have enough days in your bucket
- System checks: transferred days + current year days + earned days

❌ **Rejected:**
- If you don't have enough days
- Error shows how many days you're short

### Deduction Order (Unchanged)

Days are still deducted in this order:
1. **Transferred days** (from previous year)
2. **At start days** (current year allowance)
3. **Earned days** (blood donation, overtime, etc.)

### Error Messages

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

## FAQ

### Q: Why are weekends now counted?
A: To accurately reflect actual time off and prevent unlimited weekend requests.

### Q: Are weekend holidays counted?
A: No. If a Saturday or Sunday is already defined as a public holiday, it will NOT be deducted.

### Q: What happens to my existing vacation records?
A: Existing records are automatically recalculated with the new logic on next app launch.

### Q: Can I still request weekend-only days off?
A: Yes, but they will be deducted from your vacation bucket.

### Q: What if I try to request more days than I have?
A: The system will show an error and prevent you from scheduling the vacation.

## Testing

Three test files verify the implementation:
- `test_weekend_deduction.py` - Basic weekend counting
- `test_validation_weekend.py` - Validation logic
- `test_deduction_order_weekends.py` - Deduction order with weekends

Run tests:
```bash
python3 test_weekend_deduction.py
python3 test_validation_weekend.py
python3 test_deduction_order_weekends.py
```

## Technical Details

See `WEEKEND_DEDUCTION_IMPLEMENTATION.md` for complete technical documentation.
