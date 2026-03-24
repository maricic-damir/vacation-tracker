"""Prorated annual vacation entitlement (e.g. when adding an employee mid-year)."""
import math
from calendar import isleap
from datetime import date
from typing import Optional


def prorated_vacation_entitlement_for_year(
    current_date: date,
    contract_end_date: Optional[str],
) -> int:
    """
    Full-year allowance is 24 days. Entitlement is prorated by share of the year
    from current_date until the effective end of employment within the calendar year.

    contract_end_date: ISO date string (yyyy-mm-dd) or None for open-ended.
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
    raw = (days_remaining / days_in_year) * 24
    return max(0, math.ceil(raw))
