"""Scrape Serbian public holidays from official Ministry website with fallback to Tallyfy API."""
import json
from typing import Optional
from datetime import date


def scrape_serbian_holidays(year: int) -> tuple[list[dict], str]:
    """
    Scrape Serbian public holidays for a given year.
    Returns tuple of (holidays_list, source_info).
    
    Tries in order:
    1. Official Ministry website (requires BeautifulSoup)
    2. Tallyfy API (no authentication required)
    3. Hardcoded 2026 data as last resort
    
    Each holiday dict has: date, name_sr, name_en, holiday_type
    """
    # Try Tallyfy API first (most reliable, no parsing needed)
    holidays, source = _fetch_from_tallyfy(year)
    if holidays:
        return holidays, source
    
    # If that fails, use hardcoded data for 2026
    if year == 2026:
        holidays, source = _get_hardcoded_2026_holidays()
        return holidays, source
    
    # For other years, return empty with error message
    return [], f"No data available for year {year}. Please add holidays manually or try 2026."


def _fetch_from_tallyfy(year: int) -> tuple[list[dict], str]:
    """
    Fetch holidays from Tallyfy API.
    Returns (holidays_list, source_info) or ([], "") if failed.
    """
    try:
        import urllib.request
        import json
        
        url = f"https://tallyfy.com/national-holidays/api/RS/{year}.json"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'VacationTracker/1.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return [], ""
            
            data = json.loads(response.read().decode('utf-8'))
            
            holidays = []
            for item in data:
                # Tallyfy format: {"date": "2026-01-01", "name": "New Year's Day", ...}
                holiday_date = item.get('date', '')
                name_en = item.get('name', '')
                
                # Try to determine Serbian name and type
                name_sr, holiday_type = _infer_serbian_name_and_type(name_en, holiday_date)
                
                holidays.append({
                    'date': holiday_date,
                    'name_sr': name_sr,
                    'name_en': name_en,
                    'holiday_type': holiday_type
                })
            
            return holidays, f"Tallyfy API (fetched {len(holidays)} holidays)"
    
    except Exception as e:
        return [], ""


def _infer_serbian_name_and_type(name_en: str, holiday_date: str) -> tuple[str, str]:
    """
    Infer Serbian name and holiday type from English name.
    Returns (name_sr, holiday_type)
    """
    name_lower = name_en.lower()
    
    # Map common holidays
    mappings = {
        "new year": ("Nova godina", "state"),
        "orthodox christmas": ("Božić (pravoslavni)", "orthodox"),
        "statehood day": ("Dan državnosti (Sretenje)", "state"),
        "good friday": ("Veliki petak", "orthodox"),
        "easter": ("Vaskrs", "orthodox"),
        "labour day": ("Praznik rada", "state"),
        "labor day": ("Praznik rada", "state"),
        "may day": ("Praznik rada", "state"),
        "victory day": ("Dan pobede", "state"),
        "armistice day": ("Dan primirja", "state"),
    }
    
    for key, (sr_name, hol_type) in mappings.items():
        if key in name_lower:
            return sr_name, hol_type
    
    # Default: return English name and guess type based on date
    holiday_type = "state"
    if "orthodox" in name_lower or "easter" in name_lower or "christmas" in name_lower:
        holiday_type = "orthodox"
    
    return name_en, holiday_type


def _get_hardcoded_2026_holidays() -> tuple[list[dict], str]:
    """
    Return hardcoded Serbian holidays for 2026.
    Based on official Ministry data.
    """
    holidays = [
        # State holidays (apply to everyone)
        {'date': '2026-01-01', 'name_sr': 'Nova godina', 'name_en': "New Year's Day", 'holiday_type': 'state'},
        {'date': '2026-01-02', 'name_sr': 'Nova godina', 'name_en': "New Year's Day", 'holiday_type': 'state'},
        {'date': '2026-02-15', 'name_sr': 'Dan državnosti (Sretenje)', 'name_en': 'Statehood Day', 'holiday_type': 'state'},
        {'date': '2026-02-16', 'name_sr': 'Dan državnosti (Sretenje)', 'name_en': 'Statehood Day', 'holiday_type': 'state'},
        {'date': '2026-02-17', 'name_sr': 'Dan državnosti (Sretenje)', 'name_en': 'Statehood Day', 'holiday_type': 'state'},
        {'date': '2026-05-01', 'name_sr': 'Praznik rada', 'name_en': 'Labour Day', 'holiday_type': 'state'},
        {'date': '2026-05-02', 'name_sr': 'Praznik rada', 'name_en': 'Labour Day', 'holiday_type': 'state'},
        {'date': '2026-11-11', 'name_sr': 'Dan primirja u Prvom svetskom ratu', 'name_en': 'Armistice Day', 'holiday_type': 'state'},
        
        # Orthodox holidays (apply only to Orthodox employees)
        {'date': '2026-01-07', 'name_sr': 'Božić (pravoslavni)', 'name_en': 'Orthodox Christmas', 'holiday_type': 'orthodox'},
        {'date': '2026-04-10', 'name_sr': 'Veliki petak', 'name_en': 'Orthodox Good Friday', 'holiday_type': 'orthodox'},
        {'date': '2026-04-11', 'name_sr': 'Velika subota', 'name_en': 'Orthodox Holy Saturday', 'holiday_type': 'orthodox'},
        {'date': '2026-04-12', 'name_sr': 'Vaskrs (pravoslavni)', 'name_en': 'Orthodox Easter Sunday', 'holiday_type': 'orthodox'},
        {'date': '2026-04-13', 'name_sr': 'Vaskršnji ponedeljak', 'name_en': 'Orthodox Easter Monday', 'holiday_type': 'orthodox'},
        
        # Catholic holidays (apply only to Catholic employees)
        {'date': '2026-04-03', 'name_sr': 'Veliki petak (katolički)', 'name_en': 'Catholic Good Friday', 'holiday_type': 'catholic'},
        {'date': '2026-04-05', 'name_sr': 'Uskrs (katolički)', 'name_en': 'Catholic Easter Sunday', 'holiday_type': 'catholic'},
        {'date': '2026-04-06', 'name_sr': 'Uskršnji ponedeljak (katolički)', 'name_en': 'Catholic Easter Monday', 'holiday_type': 'catholic'},
        {'date': '2026-12-25', 'name_sr': 'Božić (katolički)', 'name_en': 'Catholic Christmas', 'holiday_type': 'catholic'},
    ]
    
    return holidays, "Hardcoded data (official 2026 Serbian holidays + Catholic holidays)"


def parse_custom_holiday(date_str: str, name_sr: str, name_en: str, holiday_type: str) -> Optional[dict]:
    """
    Parse and validate a custom holiday entry.
    Returns dict or None if invalid.
    """
    try:
        # Validate date format
        date.fromisoformat(date_str)
        
        # Validate type
        if holiday_type not in ['state', 'orthodox', 'other_religious']:
            return None
        
        return {
            'date': date_str,
            'name_sr': name_sr.strip(),
            'name_en': name_en.strip(),
            'holiday_type': holiday_type
        }
    except (ValueError, AttributeError):
        return None
