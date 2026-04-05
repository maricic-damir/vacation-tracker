"""Prorated annual vacation entitlement (e.g. when adding an employee mid-year)."""
import math
from calendar import isleap
from datetime import date
from typing import Optional


def prorated_vacation_entitlement_for_year(
    current_date: date,
    contract_end_date: Optional[str],
    working_days_per_week: int = 6,
) -> int:
    """
    Calculate prorated vacation entitlement based on working days per week.
    
    For 6-day work week: Full-year allowance is 24 days.
    For 5-day work week: Full-year allowance is 20 days.
    
    Entitlement is prorated by share of the year from current_date until 
    the effective end of employment within the calendar year.

    Args:
        current_date: Start date for the calculation
        contract_end_date: ISO date string (yyyy-mm-dd) or None for open-ended
        working_days_per_week: 5 or 6 days per week (default 6 for backwards compatibility)
    """
    year = current_date.year
    year_end_date = date(year, 12, 31)

    if contract_end_date:
        contract_end = date.fromisoformat(contract_end_date)
        effective_end = contract_end if contract_end < year_end_date else year_end_date
    else:
        effective_end = year_end_date

    if effective_end <= current_date:
        return 0

    days_remaining = (effective_end - current_date).days
    days_in_year = 366 if isleap(year) else 365
    
    # Determine full-year allowance based on working days per week
    full_year_allowance = 20 if working_days_per_week == 5 else 24
    
    raw = (days_remaining / days_in_year) * full_year_allowance
    return max(0, math.ceil(raw))
