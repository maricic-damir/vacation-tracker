"""Localization support for the Vacation Tracker application."""

TRANSLATIONS = {
    "en": {
        # Main window
        "app_title": "Vacation tracker",
        "database_required": "Database required",
        "no_database_selected": "No database was selected. The application will close.",
        
        # Language toggle
        "language": "Language",
        "english": "English",
        "serbian": "Serbian",
        
        # Employee list screen
        "employees": "Employees",
        "add_employee": "Add employee",
        "all_schedules": "All schedules",
        "holidays_settings": "Holidays / settings",
        "name": "Name",
        "jmbg": "JMBG",
        "contract": "Contract",
        "contract_start_date": "Contract start",
        "days_left": "Days left",
        "status": "Status",
        "fixed_term": "Fixed term",
        "open_ended": "Open-ended",
        "active": "Active",
        "archived": "Archived",
        
        # Employee detail screen
        "back_to_list": "← Back to list",
        "details": "Details",
        "first_name": "First name",
        "last_name": "Last name",
        "year": "Year",
        "days_at_start": "Days at start",
        "transferred": "Transferred",
        "earned": "Earned",
        "used": "Used",
        "left": "Left",
        "used_days_off": "Used days off",
        "earned_days": "Earned days",
        "booking_date": "Booking date",
        "start": "Start",
        "end": "End",
        "days": "Days",
        "date_earned": "Date earned",
        "reason_notes": "Reason / notes",
        "created": "Created",
        "contract_date_type": "Contract date / type",
        "set_transferred_days": "Set transferred days",
        "schedule_vacation": "Schedule vacation / day off",
        "add_earned_days": "Add earned days",
        "print": "Print",
        "transferred_note": "(Transferred days must be used by end of year; not counted after December 31.)",
        
        # All schedules screen
        "all_vacation_schedules": "All vacation schedules",
        "employee": "Employee",
        "completed": "Completed",
        "scheduled": "Scheduled",
        
        # Dialogs
        "add_new_employee": "Add new employee",
        "edit_contract": "Edit contract",
        "religion": "Religion",
        "orthodox": "Orthodox",
        "catholic": "Catholic",
        "working_days_per_week": "Working days per week",
        "contract_type": "Contract type",
        "contract_end_date": "Contract end date",
        "start_contract_date": "Start contract date",
        "optional": "(optional)",
        "save": "Save",
        "cancel": "Cancel",
        "error": "Error",
        "invalid_dates": "Invalid dates",
        "start_before_end": "Start date must be before or equal to end date.",
        "past_start_date": "Past start date",
        "past_start_warning": "The start date is in the past. Do you want to continue?",
        "yes": "Yes",
        "no": "No",
        "set_transferred": "Set transferred days for year",
        "number_of_days": "Number of days",
        "schedule_vacation_for": "Schedule vacation / day off for",
        "add_earned_days_title": "Add earned days",
        "manage_holidays": "Manage holidays",
        "load_holidays": "Load holidays for year",
        "clear_holidays": "Clear all holidays for year",
        "load": "Load",
        "clear": "Clear",
        "close": "Close",
        "date": "Date",
        "name_serbian": "Name (Serbian)",
        "name_english": "Name (English)",
        "holiday_type": "Holiday type",
        "state": "State",
        "other_religious": "Other religious",
        "holidays_loaded": "Holidays loaded",
        "loaded_count": "Loaded {count} holidays for year {year}.",
        "holidays_cleared": "Holidays cleared",
        "cleared_count": "Cleared {count} holidays for year {year}.",
        "loading_error": "Error loading holidays",
        "choose_database_location": "Choose database location",
        "choose_folder": "Choose a folder where the vacation.db file will be created:",
        "browse": "Browse",
        "locate_database": "Locate database",
        "locate_prompt": "Locate the existing vacation.db file:",
        "file_label": "File:",
        "until": "until",
        
        # Special leave
        "special_leaves": "Schedule special leave",
        "manage_special_leaves": "Manage special leaves",
        "add_special_leave": "Add special leave",
        "special_leave_type": "Special leave type",
        "usage_date": "Usage date",
        "days_used": "Days used",
        "remaining_days": "Remaining days",
        "special_leave_balance": "Special leave balance",
        "entitled": "Entitled",
        "used_lowercase": "used",
        "remaining": "remaining",
        "child_birth": "Child birth",
        "wedding": "Wedding",
        "moving": "Moving",
        "death_wider_family": "Death of a member of a wider family",
        "death_immediate_family": "Deaths of a member of the immediate family and members of the household",
        "insufficient_special_leave": "Insufficient special leave days",
        "special_leave_added": "Special leave added successfully",
        "adjust_special_leave_entitlements": "Adjust special leave entitlements",
        "days_entitled": "Days entitled",
        "entitlements_updated": "Special leave entitlements updated successfully",
        "success": "Success",
        "confirm": "Confirm",
        
        # Days left format
        "days_left_format": "{left} left",
    },
    "sr": {
        # Main window
        "app_title": "Праћење годишњих одмора",
        "database_required": "База података је неопходна",
        "no_database_selected": "База података није изабрана. Апликација ће се затворити.",
        
        # Language toggle
        "language": "Језик",
        "english": "Енглески",
        "serbian": "Српски",
        
        # Employee list screen
        "employees": "Запослени",
        "add_employee": "Додај запосленог",
        "all_schedules": "Сви распореди",
        "holidays_settings": "Празници / подешавања",
        "name": "Име",
        "jmbg": "ЈМБГ",
        "contract": "Уговор",
        "contract_start_date": "Почетак уговора",
        "days_left": "Преостало дана",
        "status": "Статус",
        "fixed_term": "Одређено",
        "open_ended": "Неодређено",
        "active": "Активан",
        "archived": "Архивиран",
        
        # Employee detail screen
        "back_to_list": "← Назад на листу",
        "details": "Детаљи",
        "first_name": "Име",
        "last_name": "Презиме",
        "year": "Година",
        "days_at_start": "Дана на почетку",
        "transferred": "Пренето",
        "earned": "Зарађено",
        "used": "Искоришћено",
        "left": "Преостало",
        "used_days_off": "Искоришћени дани одсуства",
        "earned_days": "Зарађени дани",
        "booking_date": "Датум резервације",
        "start": "Почетак",
        "end": "Крај",
        "days": "Дани",
        "date_earned": "Датум зарађивања",
        "reason_notes": "Разлог / напомене",
        "created": "Креирано",
        "contract_date_type": "Датум / тип уговора",
        "set_transferred_days": "Постави пренете дане",
        "schedule_vacation": "Закажи годишњи / одсуство",
        "add_earned_days": "Додај зарађене дане",
        "print": "Штампај",
        "transferred_note": "(Пренети дани морају бити искоришћени до краја године; не рачунају се после 31. децембра.)",
        
        # All schedules screen
        "all_vacation_schedules": "Сви распореди годишњих одмора",
        "employee": "Запослени",
        "completed": "Завршено",
        "scheduled": "Заказано",
        
        # Dialogs
        "add_new_employee": "Додај новог запосленог",
        "edit_contract": "Измени уговор",
        "religion": "Вероисповест",
        "orthodox": "Православна",
        "catholic": "Католичка",
        "working_days_per_week": "Радних дана недељно",
        "contract_type": "Тип уговора",
        "contract_end_date": "Датум истека уговора",
        "start_contract_date": "Датум почетка уговора",
        "optional": "(опционо)",
        "save": "Сачувај",
        "cancel": "Откажи",
        "error": "Грешка",
        "invalid_dates": "Неважећи датуми",
        "start_before_end": "Датум почетка мора бити пре или једнак датуму краја.",
        "past_start_date": "Прошли датум почетка",
        "past_start_warning": "Датум почетка је у прошлости. Да ли желите да наставите?",
        "yes": "Да",
        "no": "Не",
        "set_transferred": "Постави пренете дане за годину",
        "number_of_days": "Број дана",
        "schedule_vacation_for": "Закажи годишњи / одсуство за",
        "add_earned_days_title": "Додај зарађене дане",
        "manage_holidays": "Управљај празницима",
        "load_holidays": "Учитај празнике за годину",
        "clear_holidays": "Обриши све празнике за годину",
        "load": "Учитај",
        "clear": "Обриши",
        "close": "Затвори",
        "date": "Датум",
        "name_serbian": "Назив (српски)",
        "name_english": "Назив (енглески)",
        "holiday_type": "Тип празника",
        "state": "Државни",
        "other_religious": "Други верски",
        "holidays_loaded": "Празници учитани",
        "loaded_count": "Учитано {count} празника за годину {year}.",
        "holidays_cleared": "Празници обрисани",
        "cleared_count": "Обрисано {count} празника за годину {year}.",
        "loading_error": "Грешка при учитавању празника",
        "choose_database_location": "Изаберите локацију базе података",
        "choose_folder": "Изаберите фолдер где ће vacation.db фајл бити креиран:",
        "browse": "Потражи",
        "locate_database": "Лоцирај базу података",
        "locate_prompt": "Лоцирајте постојећи vacation.db фајл:",
        "file_label": "Фајл:",
        "until": "до",
        
        # Special leave
        "special_leaves": "Закажи плаћено одсуство",
        "manage_special_leaves": "Управљај плаћеним одсуствима",
        "add_special_leave": "Додај плаћено одсуство",
        "special_leave_type": "Врста плаћеног одсуства",
        "usage_date": "Датум коришћења",
        "days_used": "Искоришћено дана",
        "remaining_days": "Преостало дана",
        "special_leave_balance": "Стање плаћених одсустава",
        "entitled": "Право",
        "used_lowercase": "искоришћено",
        "remaining": "преостало",
        "child_birth": "Рођење детета",
        "wedding": "Венчање",
        "moving": "Селидба",
        "death_wider_family": "Смрт члана шире породице",
        "death_immediate_family": "Смрт члана уже породице и домаћинства",
        "insufficient_special_leave": "Недовољно дана плаћеног одсуства",
        "special_leave_added": "Плаћено одсуство успешно додато",
        "adjust_special_leave_entitlements": "Подеси плаћена одсуства",
        "days_entitled": "Право на дане",
        "entitlements_updated": "Права плаћених одсустава успешно ажурирана",
        "success": "Успех",
        "confirm": "Потврди",
        
        # Days left format
        "days_left_format": "{left} преостало",
    }
}

_current_language = "en"

def get_language():
    """Get the current language code."""
    return _current_language

def set_language(lang_code: str):
    """Set the current language code."""
    global _current_language
    if lang_code in TRANSLATIONS:
        _current_language = lang_code

def tr(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    
    Args:
        key: Translation key
        **kwargs: Optional formatting parameters
    
    Returns:
        Translated string with formatting applied
    """
    text = TRANSLATIONS.get(_current_language, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
