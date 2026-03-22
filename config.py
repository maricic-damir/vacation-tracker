"""Persist and resolve database path (first run vs. find existing)."""
import os
import configparser
from pathlib import Path
from typing import Optional


def _config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", os.path.expanduser("~")))
    else:
        base = Path.home()
    return base / "VacationTracker"


def _config_path() -> Path:
    return _config_dir() / "config.ini"


def get_db_path() -> Optional[str]:
    """Return saved database path if set and file exists; else None."""
    path = _config_path()
    if not path.exists():
        return None
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    db = cfg.get("app", "db_path", fallback=None)
    if not db or not Path(db).exists():
        return None
    return db


def get_saved_db_path_raw() -> Optional[str]:
    """Return saved path from config even if file is missing (e.g. moved/OneDrive)."""
    path = _config_path()
    if not path.exists():
        return None
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg.get("app", "db_path", fallback=None) or None


def set_db_path(db_path: str) -> None:
    """Save database path to config."""
    _config_dir().mkdir(parents=True, exist_ok=True)
    path = _config_path()
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding="utf-8")
    if "app" not in cfg:
        cfg.add_section("app")
    cfg.set("app", "db_path", db_path)
    with open(path, "w", encoding="utf-8") as f:
        cfg.write(f)


def clear_db_path() -> None:
    """Remove saved path (e.g. after user chose 'Locate' and we want to re-prompt)."""
    path = _config_path()
    if not path.exists():
        return
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    if "app" in cfg and cfg.has_option("app", "db_path"):
        cfg.remove_option("app", "db_path")
        with open(path, "w", encoding="utf-8") as f:
            cfg.write(f)


def get_language() -> str:
    """Return saved language preference or default to 'en'."""
    path = _config_path()
    if not path.exists():
        return "en"
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg.get("app", "language", fallback="en")


def set_language(lang_code: str) -> None:
    """Save language preference to config."""
    _config_dir().mkdir(parents=True, exist_ok=True)
    path = _config_path()
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding="utf-8")
    if "app" not in cfg:
        cfg.add_section("app")
    cfg.set("app", "language", lang_code)
    with open(path, "w", encoding="utf-8") as f:
        cfg.write(f)
