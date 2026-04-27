# Vacation Tracker - Startup Behavior Guide

This guide explains what happens when starting the Vacation Tracker on different computers and how to safely work with shared databases.

## Startup Scenarios

### 1. Fresh Installation (New Computer, First Time)

**What happens:**
- No configuration file exists yet
- User sees: "Welcome to Vacation Tracker! What would you like to do?"
- Two options:
  - **"Create New Database"** - Creates a new, empty vacation database
  - **"Use Existing Database"** - Browse to select an existing database file

**Recommended choice:**
- Choose **"Use Existing Database"** if you have a shared database (OneDrive, network drive, etc.)
- Choose **"Create New Database"** only if this is truly a new setup

### 2. Previous Installation (Config Exists, Database Missing)

**What happens:**
- Configuration file exists with saved database path
- But the database file is not found at that location
- User sees: "Database Not Found" with explanation
- Two options:
  - **"Find Existing Database"** - Browse to locate the moved database (recommended)
  - **"Create New Database Here"** - Creates fresh database at saved location

**Common causes:**
- Database moved to different location
- OneDrive/cloud storage not yet synced
- Network drive temporarily unavailable
- File was deleted or renamed

**Recommended choice:**
- Always choose **"Find Existing Database"** first
- Only create new database if you're certain the original is lost

### 3. Valid Database Found

**What happens:**
- Saved database path exists and file is accessible
- Connects directly to existing database
- Runs completion job (marks past vacations as completed)
- Application starts normally

## Best Practices for Shared Databases

### Setting Up Shared Access

1. **Choose a shared location:**
   - OneDrive, Google Drive, Dropbox folder
   - Network drive accessible to all users
   - Shared folder on local server

2. **First user setup:**
   - Run application, choose "Create New Database"
   - Select the shared folder location
   - Add initial data (employees, holidays, etc.)

3. **Additional users setup:**
   - Run application, choose "Use Existing Database"
   - Browse to and select the shared database file
   - Application remembers this location

### Handling Sync Issues

**When shared folder is not synced:**
- Application shows "Database Not Found"
- Wait for sync to complete, then choose "Find Existing Database"
- Browse to the synced database location
- **Never** choose "Create New Database" as this creates duplicates

**When database is temporarily unavailable:**
- Network drives may disconnect
- Cloud storage may be offline
- Always wait and locate the existing database
- Check sync status in OneDrive/cloud storage app

### Multi-User Coordination

**Important:** SQLite databases don't support concurrent access
- Only one person should use the application at a time
- Coordinate with other users before making changes
- Close application when done to release database lock
- Let cloud storage sync before others access

## Troubleshooting

### "Database file missing" on startup
1. Check if OneDrive/cloud storage is syncing
2. Verify network drive connection
3. Choose "Find Existing Database" and browse to correct location
4. If database is truly lost, restore from backup if available

### Duplicate databases created
- This happens when choosing "Create New Database" while shared database exists
- Merge data manually or restore from most recent complete database
- Educate users to always choose "Find Existing" options

### Database corruption or conflicts
- Keep regular backups of database file
- Never edit database file outside the application
- If corruption occurs, restore from most recent backup
- Avoid concurrent access by multiple users

## Configuration Details

**Config file locations:**
- Windows: `%APPDATA%\VacationTracker\config.ini`
- macOS/Linux: `~/.VacationTracker/config.ini`

**Config file contains:**
- Database file path
- Language preference
- Window preferences (future)

**Database file:**
- SQLite format (`.db` extension)
- Contains all employee data, vacations, holidays
- Can be backed up by copying the file
- Should be stored in shared location for multi-user access

## Summary

The application is designed to prevent accidental data loss when working with shared databases. The startup dialogs prioritize finding existing databases over creating new ones, and provide clear explanations to help users make the right choice.

Key principle: **When in doubt, always look for the existing database first.**