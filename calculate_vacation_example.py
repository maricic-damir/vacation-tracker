#!/usr/bin/env python3
"""
Demonstracija kako vacation tracker računa potrebne dane za godišnji odmor.
Odgovor na pitanje: "Imam na raspolaganju 15 preostalih dana. Radim 6 dana nedeljno 
i zelim da uzmem godisnji odmor pocevsi od 28.04.2026 do 17.05.2026. Koliko mi je dana potrebno?"
"""

import sys
import sqlite3
from datetime import date

# Add parent directory to path
sys.path.insert(0, '/Users/d.maricic/vacation_tracker')

from database import init_schema, get_connection, save_non_working_days
from db_helpers import (
    insert_employee, 
    count_working_days_in_range, 
    count_total_deductible_days,
    calculate_multi_year_vacation_requirements,
    validate_vacation_scheduling
)


def create_test_employee(conn):
    """Kreiraj test zaposlenog koji radi 6 dana nedeljno."""
    employee_id = insert_employee(
        conn,
        jmbg="1234567890123",
        first_name="Marko",
        last_name="Petrovic",
        contract_type="open_ended",
        contract_end_date=None,
        religion="orthodox",
        start_contract_date="2026-01-01",
        working_days_per_week=6  # Radi 6 dana nedeljno (ponedeljak-subota)
    )
    return employee_id


def load_basic_holidays(conn):
    """Učitaj osnovne praznike za 2026."""
    holidays = [
        {'date': '2026-01-01', 'name_sr': 'Nova godina', 'name_en': 'New Year', 'holiday_type': 'state'},
        {'date': '2026-01-02', 'name_sr': 'Nova godina', 'name_en': 'New Year', 'holiday_type': 'state'},
        {'date': '2026-01-07', 'name_sr': 'Božić', 'name_en': 'Orthodox Christmas', 'holiday_type': 'orthodox'},
        {'date': '2026-05-01', 'name_sr': 'Praznik rada', 'name_en': 'Labour Day', 'holiday_type': 'state'},
        {'date': '2026-05-02', 'name_sr': 'Praznik rada', 'name_en': 'Labour Day', 'holiday_type': 'state'},
    ]
    count = save_non_working_days(conn, holidays)
    return count


def analyze_vacation_period():
    """Analiziraj period 28.04.2026 - 17.05.2026 za zaposlenog koji radi 6 dana nedeljno."""
    
    print("=" * 70)
    print("ANALIZA GODIŠNJEG ODMORA - VACATION TRACKER")
    print("=" * 70)
    
    # Create in-memory database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    
    # Create test employee
    employee_id = create_test_employee(conn)
    print(f"✓ Kreiran test zaposleni (ID: {employee_id}) - radi 6 dana nedeljno")
    
    # Load holidays
    holiday_count = load_basic_holidays(conn)
    print(f"✓ Učitano {holiday_count} praznika")
    
    # Period analysis
    start_date = "2026-04-28"  # Ponedeljak
    end_date = "2026-05-17"    # Nedelja
    
    print(f"\n📅 PERIOD ODMORA: {start_date} do {end_date}")
    
    # Check what days these are
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    
    print(f"   Start: {start.strftime('%A, %d.%m.%Y')} (dan u nedelji: {start.weekday()+1})")
    print(f"   Kraj:  {end.strftime('%A, %d.%m.%Y')} (dan u nedelji: {end.weekday()+1})")
    print(f"   Ukupno kalendarskih dana: {(end - start).days + 1}")
    
    print(f"\n⚙️  ALGORITAM ZA 6-DNEVNU RADNU NEDELJU:")
    print("   - Radi se: ponedeljak - subota")
    print("   - Odmara se: nedelja")
    print("   - Ne računa se: državni praznici")
    
    # Calculate using vacation tracker functions
    total_deductible_days = count_total_deductible_days(conn, start_date, end_date, employee_id)
    working_days_count = count_working_days_in_range(conn, start_date, end_date, employee_id)
    
    print(f"\n📊 REZULTAT RAČUNANJA:")
    print(f"   Ukupno dana za oduzimanje: {total_deductible_days}")
    print(f"   Čisto radnih dana: {working_days_count}")
    
    # Detailed breakdown
    print(f"\n🔍 DETALJNA ANALIZA:")
    
    current = start
    weekdays = ["Ponedeljak", "Utorak", "Sreda", "Četvrtak", "Petak", "Subota", "Nedelja"]
    working_days = 0
    sundays = 0
    holidays = 0
    
    print("   Dan po dan:")
    while current <= end:
        day_name = weekdays[current.weekday()]
        is_sunday = current.weekday() == 6
        
        # Check if holiday
        from database import is_non_working_day_for_employee
        is_holiday = is_non_working_day_for_employee(conn, current.isoformat(), employee_id)
        
        status = ""
        if is_holiday:
            status = "🎉 PRAZNIK"
            holidays += 1
        elif is_sunday:
            status = "😴 NEDELJA (ne radi se)"
            sundays += 1
        else:
            status = "💼 RADI SE"
            working_days += 1
            
        print(f"     {current.strftime('%d.%m')} {day_name:10} - {status}")
        current = date.fromordinal(current.toordinal() + 1)
    
    print(f"\n📈 SUMARNO:")
    print(f"   Radnih dana (pon-sub): {working_days}")
    print(f"   Nedelja (ne računa se): {sundays}")
    print(f"   Praznika (ne računa se): {holidays}")
    print(f"   UKUPNO ZA ODUZIMANJE: {total_deductible_days}")
    
    # Answer the original question
    available_days = 15
    needed_days = total_deductible_days
    shortage = needed_days - available_days
    
    print(f"\n🎯 ODGOVOR NA PITANJE:")
    print(f"   Imate na raspolaganju: {available_days} dana")
    print(f"   Potrebno vam je: {needed_days} dana")
    
    if shortage > 0:
        print(f"   ❌ NEDOSTAJU VAM: {shortage} dana")
        print(f"\n💡 OBJAŠNJENJE:")
        print(f"   Period od 20 kalendarskih dana sadrži {working_days} radnih dana")
        print(f"   (ne računaju se {sundays} nedelje i {holidays} praznika)")
    else:
        print(f"   ✅ DOVOLJNO DANA! Ostaje vam: {abs(shortage)} dana")
    
    # Validation using the system's validation function
    print(f"\n🔍 VALIDACIJA PUTEM SISTEMA:")
    validation = validate_vacation_scheduling(conn, employee_id, start_date, end_date)
    
    # Multi-year requirements (although this is same year)
    year_reqs = calculate_multi_year_vacation_requirements(conn, employee_id, start_date, end_date)
    for year, req in year_reqs.items():
        print(f"   {year}: {req['days_needed']} dana potrebno")
    
    conn.close()
    
    print(f"\n💻 PROGRAMSKA LOGIKA:")
    print(f"   Funkcija: count_total_deductible_days()")
    print(f"   Za 6-dnevnu nedelju koristi: calculate_deduction_days_new_algorithm()")
    print(f"   Formula: ukupni_dani - nedelje - praznici = dani_za_oduzimanje")
    

def show_code_structure():
    """Pokaži strukturu koda koji računa dane."""
    print(f"\n🔧 STRUKTURA KODA:")
    print(f"\n1. Glavni entry point:")
    print(f"   count_total_deductible_days(conn, start_date, end_date, employee_id)")
    
    print(f"\n2. Za 6-dnevnu radnu nedelju poziva:")
    print(f"   calculate_deduction_days_new_algorithm(conn, start_date, end_date, employee_id)")
    
    print(f"\n3. Algoritam:")
    print(f"   - total_days = broj kalendarskih dana")
    print(f"   - full_weeks = total_days // 7")
    print(f"   - rest_days = full_weeks (broj nedelja)")
    print(f"   - holiday_count = broj praznika (iskljucuje duplo brojanje sa nedeljama)")
    print(f"   - deduction_days = total_days - rest_days - holiday_count")
    
    print(f"\n4. Fajlovi:")
    print(f"   - db_helpers.py: count_total_deductible_days(), calculate_deduction_days_new_algorithm()")
    print(f"   - database.py: is_non_working_day_for_employee() - provera praznika")
    print(f"   - holiday_scraper.py: scrape_serbian_holidays() - učitavanje praznika")


if __name__ == '__main__':
    analyze_vacation_period()
    show_code_structure()