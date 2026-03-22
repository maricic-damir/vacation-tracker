# Localization System

This document describes the localization system implemented for the Vacation Tracker application.

## Overview

The application now supports multiple languages with Serbian (Српски) and English translations. Users can switch between languages using a dropdown in the top right corner of the application.

## Architecture

### Files Modified/Created

1. **translations.py** (NEW) - Central translation system
   - Contains all translations in a structured dictionary
   - Provides `tr(key)` function for translating keys
   - Manages current language state
   - Supports formatting parameters (e.g., `tr("loaded_count", count=5, year=2026)`)

2. **config.py** (UPDATED)
   - Added `get_language()` and `set_language()` functions
   - Persists language preference across sessions

3. **ui/main_window.py** (UPDATED)
   - Added language selector combo box in top right corner
   - Loads saved language on startup
   - Refreshes all screens when language changes

4. **All UI Screens and Dialogs** (UPDATED)
   - `ui/screen_employees.py` - Employee list screen
   - `ui/screen_employee_detail.py` - Employee detail screen
   - `ui/screen_all_schedules.py` - All schedules screen
   - `ui/dialogs.py` - All dialog boxes
   
## Usage

### For Users

1. Launch the application
2. Look for the language dropdown in the top right corner
3. Select "English" or "Српски"
4. The interface will immediately update to the selected language
5. Your language preference is saved and will be remembered next time you open the app

### For Developers

#### Adding a New Translation

1. Open `translations.py`
2. Add your key to both `"en"` and `"sr"` dictionaries:

```python
TRANSLATIONS = {
    "en": {
        # ... existing translations ...
        "your_new_key": "English text",
    },
    "sr": {
        # ... existing translations ...
        "your_new_key": "Српски текст",
    }
}
```

3. Use in your code:

```python
from translations import tr

label.setText(tr("your_new_key"))
```

#### With Formatting Parameters

```python
# In translations.py
"welcome_message": "Welcome, {name}!"  # English
"welcome_message": "Добродошли, {name}!"  # Serbian

# In your code
label.setText(tr("welcome_message", name="John"))
```

#### Conditional Logic for Complex Cases

For cases where simple string replacement isn't enough:

```python
if tr("language") == "Language":  # English
    # English-specific logic
else:  # Serbian
    # Serbian-specific logic
```

## Translation Keys

All translation keys are documented in `translations.py`. Key categories include:

- **Main window**: app_title, database_required, language, etc.
- **Employee list**: employees, add_employee, all_schedules, etc.
- **Employee detail**: details, year, days_at_start, transferred, etc.
- **Dialogs**: add_new_employee, schedule_vacation, edit_contract, etc.
- **Common**: save, cancel, error, yes, no, etc.

## Language Support

Currently supported languages:
- **English** (en) - Default language
- **Serbian** (sr) - Српски (Cyrillic)

## Print Functionality

The print feature also respects the current language setting. When you print employee details:
- All labels and headers are translated
- The layout remains consistent across languages
- Font sizes are optimized for printing (reduced by 25%)

## Testing

The localization system has been integrated into:
- ✅ Main window with language selector
- ✅ Employee list screen
- ✅ Employee detail screen  
- ✅ All schedules screen
- ✅ All dialog boxes
- ✅ Print functionality
- ✅ Error messages and warnings
- ✅ Button labels and table headers

## Future Enhancements

To add a new language:

1. Add a new language code to `translations.py`:

```python
TRANSLATIONS = {
    "en": { ... },
    "sr": { ... },
    "de": {  # German example
        "app_title": "Urlaubstracker",
        # ... all other keys ...
    }
}
```

2. Update the language selector in `ui/main_window.py`:

```python
self._lang_combo.addItem("Deutsch", "de")
```

3. Test thoroughly with the new language selected

## Notes

- Language preference is stored in the config file alongside database path
- Switching languages triggers a full UI refresh to update all visible text
- The current implementation uses inline conditional logic for some complex cases (e.g., message boxes with multiple sentences)
- Consider extracting more complex conditionals to the translation system if the number of languages grows
