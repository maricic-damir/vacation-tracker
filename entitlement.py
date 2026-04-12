"""Prorated annual vacation entitlement (e.g. when adding an employee mid-year)."""
import math
from calendar import isleap
from datetime import date
from typing import Optional, Dict, List


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


def calculate_prorated_days_for_contract_update(
    old_contract_end_date: Optional[str],
    new_contract_end_date: Optional[str],
    working_days_per_week: int = 6,
    calculation_start_date: Optional[date] = None,
    old_contract_type: Optional[str] = None,
    new_contract_type: Optional[str] = None,
) -> List[Dict[str, any]]:
    """
    Calculate prorated vacation days when updating contract end date.
    
    This function handles various contract transition scenarios:
    - Fixed-term → Fixed-term (extending): Calculate additional days
    - Fixed-term → Open-ended (permanent): No additional calculation needed
    - Open-ended → Fixed-term (temporary): No prorated calculation (use existing balance)
    - New contract (any type): Calculate from start date
    
    If the new contract spans multiple years, calculations are done year by year.
    
    Args:
        old_contract_end_date: Previous contract end date (ISO string) or None
        new_contract_end_date: New contract end date (ISO string) or None  
        working_days_per_week: 5 or 6 days per week
        calculation_start_date: Start date for calculation (defaults to today or old contract end + 1 day)
        old_contract_type: Previous contract type ('fixed_term', 'open_ended', or None)
        new_contract_type: New contract type ('fixed_term', 'open_ended', or None)
        
    Returns:
        List of dictionaries with year-by-year prorated calculations:
        [{"year": 2026, "days": 12, "period_start": "2026-06-01", "period_end": "2026-12-31"}, ...]
    """
    # Handle different contract transition scenarios
    if old_contract_type == "open_ended" and new_contract_type == "fixed_term":
        # Transitioning from open-ended to fixed-term
        # No additional prorated days - employee already has full entitlement
        # The fixed-term end date just sets a boundary, doesn't add days
        return []
    
    if not new_contract_end_date:
        # New contract is open-ended - calculate prorated days from old end date to year end
        if old_contract_end_date:
            # Calculate from old contract end to end of current/future years
            old_end = date.fromisoformat(old_contract_end_date)
            from datetime import timedelta
            start_date = old_end + timedelta(days=1)
            
            # For open-ended contracts, calculate to end of year(s)
            results = []
            current_year = start_date.year
            
            # Calculate for current year and potentially future years if needed
            year_end = date(current_year, 12, 31)
            
            if start_date <= year_end:
                prorated_days = prorated_vacation_entitlement_for_year(
                    start_date,
                    year_end.isoformat(),
                    working_days_per_week
                )
                
                if prorated_days > 0:
                    results.append({
                        "year": current_year,
                        "days": prorated_days,
                        "period_start": start_date.isoformat(),
                        "period_end": year_end.isoformat()
                    })
            
            return results
        else:
            # No old contract date, open-ended from start - no additional calculation needed
            return []
        
    new_end = date.fromisoformat(new_contract_end_date)
    
    # Determine calculation start date
    if calculation_start_date:
        start_date = calculation_start_date
    elif old_contract_end_date:
        old_end = date.fromisoformat(old_contract_end_date)
        # Start calculation from the day after old contract ended
        from datetime import timedelta
        start_date = old_end + timedelta(days=1)
    else:
        # No old contract date, start from today
        start_date = date.today()
    
    # If new end date is before or equal to start date, no days to calculate
    if new_end <= start_date:
        return []
    
    results = []
    current_date = start_date
    
    # Calculate year by year until we reach the new contract end date
    while current_date <= new_end:
        year = current_date.year
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        # Period start is the later of current_date or year_start
        period_start = max(current_date, year_start)
        
        # Period end is the earlier of new_end or year_end
        period_end = min(new_end, year_end)
        
        # Calculate prorated days for this period
        if period_end >= period_start:
            prorated_days = prorated_vacation_entitlement_for_year(
                period_start, 
                period_end.isoformat(),
                working_days_per_week
            )
            
            if prorated_days > 0:
                results.append({
                    "year": year,
                    "days": prorated_days,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat()
                })
        
        # Move to next year
        current_date = date(year + 1, 1, 1)
    
    return results


def recalculate_days_at_start_for_working_days_change(
    contract_start_date: Optional[str],
    contract_end_date: Optional[str],
    contract_type: str,
    old_working_days_per_week: int,
    new_working_days_per_week: int,
    year: int
) -> Optional[int]:
    """
    Recalculate days at start when working days per week changes.
    
    This handles the scenario where an employee's working days per week changes
    (e.g., 5-day to 6-day work week) and we need to recalculate their vacation
    entitlement for the current year.
    
    Args:
        contract_start_date: Contract start date (ISO string) or None
        contract_end_date: Contract end date (ISO string) or None
        contract_type: 'fixed_term' or 'open_ended'
        old_working_days_per_week: Previous working days (5 or 6)
        new_working_days_per_week: New working days (5 or 6)
        year: Year to recalculate for
        
    Returns:
        New days at start value, or None if no recalculation needed
    """
    # If working days haven't changed, no recalculation needed
    if old_working_days_per_week == new_working_days_per_week:
        return None
    
    # Determine the start date for calculation
    year_start = date(year, 1, 1)
    
    if contract_start_date:
        start_date_obj = date.fromisoformat(contract_start_date)
        # Use the later of contract start or year start
        calculation_start = max(start_date_obj, year_start)
    else:
        # No contract start date, assume year start
        calculation_start = year_start
    
    # For open-ended contracts, calculate to end of year
    # For fixed-term contracts, calculate to contract end or year end (whichever is earlier)
    if contract_type == "open_ended":
        effective_end_date = None  # Will default to year end in the calculation
    else:
        effective_end_date = contract_end_date
    
    # Calculate new prorated entitlement with new working days
    new_days_at_start = prorated_vacation_entitlement_for_year(
        calculation_start,
        effective_end_date,
        new_working_days_per_week
    )
    
    return new_days_at_start
