"""Dialogs: DB path (choose/create, locate), add employee, schedule vacation, add earned days, contract extension."""
from datetime import date
import sqlite3

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QProgressDialog,
    QHeaderView,
    QCheckBox,
)
from PyQt6.QtCore import QDate, Qt
from typing import Optional

from entitlement import prorated_vacation_entitlement_for_year
from translations import tr
from database import get_special_leave_types, get_special_leave_balance_for_employee, update_special_leave_entitlement


def choose_or_create_db_path(parent: Optional[QWidget]) -> Optional[str]:
    """Let user choose where to create or select the database file (first run)."""
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Choose where to store the database",
        "",
        "SQLite database (*.db);;All files (*)",
        "SQLite database (*.db)",
    )
    if not path:
        return None
    if not path.lower().endswith(".db"):
        path = path + ".db" if not path.endswith(".") else path + "db"
    return path


def locate_db_path(parent: Optional[QWidget]) -> Optional[str]:
    """Let user locate existing vacation.db (e.g. after move/OneDrive)."""
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Locate database file",
        "",
        "SQLite database (*.db);;All files (*)",
        "SQLite database (*.db)",
    )
    return path or None


def resolve_missing_saved_db_path(parent: Optional[QWidget], saved_path: str) -> Optional[str]:
    """Saved path in config but file missing: create empty DB there or locate another file."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(tr("database_file_missing_title"))
    box.setText(tr("database_file_missing_message").format(path=saved_path))
    create_btn = box.addButton(
        tr("create_empty_database_here"),
        QMessageBox.ButtonRole.AcceptRole,
    )
    locate_btn = box.addButton(
        tr("locate_existing_database"),
        QMessageBox.ButtonRole.ActionRole,
    )
    box.addButton(QMessageBox.StandardButton.Cancel)
    box.exec()
    clicked = box.clickedButton()
    if clicked == create_btn:
        return saved_path
    if clicked == locate_btn:
        return locate_db_path(parent)
    return None


def warn_past_start_date(parent: QWidget, start_date: date) -> bool:
    """Warn that start date is in the past; return True if user confirms."""
    if tr("language") == "Language":  # English
        return (
            QMessageBox.question(
                parent,
                "Start date in the past",
                f"The start date ({start_date}) is in the past. Do you want to save anyway? The leave will be marked as used.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )
    else:  # Serbian
        return (
            QMessageBox.question(
                parent,
                "Датум почетка у прошлости",
                f"Датум почетка ({start_date}) је у прошлости. Да ли желите да сачувате? Одсуство ће бити означено као искоришћено.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )


# ---------- Add employee ----------


class AddEmployeeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("add_new_employee"))
        lay = QFormLayout(self)
        self.jmbg = QLineEdit()
        self.jmbg.setPlaceholderText("13 digits")
        lay.addRow(tr("jmbg") + ":", self.jmbg)
        self.first_name = QLineEdit()
        lay.addRow(tr("first_name") + ":", self.first_name)
        self.last_name = QLineEdit()
        lay.addRow(tr("last_name") + ":", self.last_name)
        self.religion = QComboBox()
        self.religion.addItems([tr("orthodox"), tr("catholic")])
        lay.addRow(tr("religion") + ":", self.religion)
        self.working_days_per_week = QComboBox()
        if tr("language") == "Language":  # English
            self.working_days_per_week.addItems(["6 days per week", "5 days per week (Mon-Fri)"])
        else:  # Serbian
            self.working_days_per_week.addItems(["6 дана недељно", "5 дана недељно (пон-пет)"])
        self.working_days_per_week.currentIndexChanged.connect(lambda _: self._update_prorated_label())
        lay.addRow(tr("working_days_per_week") + ":", self.working_days_per_week)
        self.start_contract_date = QDateEdit()
        self.start_contract_date.setCalendarPopup(True)
        self.start_contract_date.setDate(QDate.currentDate())
        self.start_contract_date.dateChanged.connect(lambda _d: self._update_prorated_label())
        lay.addRow(tr("start_contract_date") + ":", self.start_contract_date)
        self.contract_type = QComboBox()
        if tr("language") == "Language":  # English
            self.contract_type.addItems(["Fixed term (with end date)", "Open-ended (no end date)"])
        else:  # Serbian
            self.contract_type.addItems(["Одређено (са датумом истека)", "Неодређено (без датума истека)"])
        self.contract_type.currentIndexChanged.connect(self._on_contract_type_changed)
        lay.addRow(tr("contract_type") + ":", self.contract_type)
        self.contract_end_date = QDateEdit()
        self.contract_end_date.setCalendarPopup(True)
        self.contract_end_date.setDate(QDate.currentDate().addYears(1))
        self.contract_end_date.dateChanged.connect(lambda _d: self._update_prorated_label())
        lay.addRow(tr("contract_end_date") + ":", self.contract_end_date)
        self._prorated_label = QLabel()
        self._prorated_label.setWordWrap(True)
        if tr("language") == "Language":  # English
            lay.addRow("Vacation days (this year, prorated):", self._prorated_label)
        else:  # Serbian
            lay.addRow("Дани годишњег (ова година, пропорционално):", self._prorated_label)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._on_accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)
        self._on_contract_type_changed(0)

    def _on_contract_type_changed(self, idx: int):
        is_fixed = idx == 0
        self.contract_end_date.setEnabled(is_fixed)
        self._update_prorated_label()

    def _update_prorated_label(self):
        idx = self.contract_type.currentIndex()
        end_str = (
            self.contract_end_date.date().toString("yyyy-MM-dd") if idx == 0 else None
        )
        start_date = self.start_contract_date.date().toPyDate()
        working_days_idx = self.working_days_per_week.currentIndex()
        working_days_per_week = 6 if working_days_idx == 0 else 5
        n = prorated_vacation_entitlement_for_year(start_date, end_str, working_days_per_week)
        if tr("language") == "Language":  # English
            self._prorated_label.setText(
                str(n)
                + " (based on start contract date, contract type, working days per week, and end of employment within this year)"
            )
        else:  # Serbian
            self._prorated_label.setText(
                str(n)
                + " (на основу датума почетка уговора, типа уговора, радних дана недељно и краја запослења у овој години)"
            )

    def _validate_jmbg(self) -> Optional[str]:
        """Return None if valid, else error message."""
        j = self.jmbg.text().strip()
        if len(j) != 13 or not j.isdigit():
            if tr("language") == "Language":  # English
                return "JMBG must be exactly 13 digits."
            else:  # Serbian
                return "ЈМБГ мора бити тачно 13 цифара."
        return None

    def _on_accept(self):
        err = self._validate_jmbg()
        if err:
            QMessageBox.warning(self, tr("error"), err)
            return
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            if tr("language") == "Language":  # English
                QMessageBox.warning(self, tr("error"), "First name and last name are required.")
            else:  # Serbian
                QMessageBox.warning(self, tr("error"), "Име и презиме су обавезни.")
            return
        self.accept()

    def get_data(self) -> dict:
        idx = self.contract_type.currentIndex()
        contract_type = "fixed_term" if idx == 0 else "open_ended"
        end_date = self.contract_end_date.date().toString("yyyy-MM-dd") if idx == 0 else None
        start_date = self.start_contract_date.date().toPyDate()
        working_days_idx = self.working_days_per_week.currentIndex()
        working_days_per_week = 6 if working_days_idx == 0 else 5
        days_at_start = prorated_vacation_entitlement_for_year(start_date, end_date, working_days_per_week)
        religion_idx = self.religion.currentIndex()
        religion = "orthodox" if religion_idx == 0 else "catholic"
        return {
            "jmbg": self.jmbg.text().strip(),
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "religion": religion,
            "working_days_per_week": working_days_per_week,
            "contract_type": contract_type,
            "contract_end_date": end_date,
            "start_contract_date": self.start_contract_date.date().toString("yyyy-MM-dd"),
            "days_at_start": days_at_start,
        }


# ---------- Schedule vacation / day off ----------


class ScheduleVacationDialog(QDialog):
    def __init__(self, parent=None, employee_name: str = ""):
        super().__init__(parent)
        title = tr("schedule_vacation_for") + (f" {employee_name}" if employee_name else "")
        self.setWindowTitle(title)
        lay = QFormLayout(self)
        self.booking_date = QDateEdit()
        self.booking_date.setDate(QDate.currentDate())
        self.booking_date.setCalendarPopup(True)
        lay.addRow(tr("booking_date") + ":", self.booking_date)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        lay.addRow(tr("start") + ":", self.start_date)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        lay.addRow(tr("end") + ":", self.end_date)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def get_data(self) -> dict:
        return {
            "booking_date": self.booking_date.date().toString("yyyy-MM-dd"),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd"),
        }


# ---------- Add earned days ----------


class AddEarnedDaysDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("add_earned_days_title"))
        lay = QFormLayout(self)
        self.earned_date = QDateEdit()
        self.earned_date.setDate(QDate.currentDate())
        self.earned_date.setCalendarPopup(True)
        lay.addRow(tr("date_earned") + ":", self.earned_date)
        self.number_of_days = QSpinBox()
        self.number_of_days.setMinimum(1)
        self.number_of_days.setMaximum(365)
        self.number_of_days.setValue(1)
        lay.addRow(tr("number_of_days") + ":", self.number_of_days)
        self.reason_notes = QPlainTextEdit()
        if tr("language") == "Language":  # English
            self.reason_notes.setPlaceholderText("e.g. blood donation, overtime, stepping in, public holiday…")
        else:  # Serbian
            self.reason_notes.setPlaceholderText("нпр. давање крви, прековремени рад, замена, државни празник…")
        self.reason_notes.setMaximumHeight(80)
        lay.addRow(tr("reason_notes") + ":", self.reason_notes)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def get_data(self) -> dict:
        return {
            "earned_date": self.earned_date.date().toString("yyyy-MM-dd"),
            "number_of_days": self.number_of_days.value(),
            "reason_notes": self.reason_notes.toPlainText().strip(),
        }


# ---------- Contract extension / change type ----------


class ContractDialog(QDialog):
    def __init__(
        self,
        parent=None,
        current_type: str = "fixed_term",
        current_end_date: Optional[str] = None,
        current_start_date: Optional[str] = None,
        current_days_at_start: int = 0,
        current_religion: str = "orthodox",
        current_working_days_per_week: int = 6,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("edit_contract"))
        lay = QFormLayout(self)
        self.religion = QComboBox()
        self.religion.addItems([tr("orthodox"), tr("catholic")])
        rel_idx = 0 if current_religion == "orthodox" else 1
        self.religion.setCurrentIndex(rel_idx)
        lay.addRow(tr("religion") + ":", self.religion)
        self.working_days_per_week = QComboBox()
        if tr("language") == "Language":  # English
            self.working_days_per_week.addItems(["6 days per week", "5 days per week (Mon-Fri)"])
        else:  # Serbian
            self.working_days_per_week.addItems(["6 дана недељно", "5 дана недељно (пон-пет)"])
        working_days_idx = 0 if current_working_days_per_week == 6 else 1
        self.working_days_per_week.setCurrentIndex(working_days_idx)
        self.working_days_per_week.currentIndexChanged.connect(self._on_working_days_changed)
        lay.addRow(tr("working_days_per_week") + ":", self.working_days_per_week)
        self.contract_type = QComboBox()
        if tr("language") == "Language":  # English
            self.contract_type.addItems(["Fixed term (with end date)", "Open-ended (no end date)"])
        else:  # Serbian
            self.contract_type.addItems(["Одређено (са датумом истека)", "Неодређено (без датума истека)"])
        idx = 0 if current_type == "fixed_term" else 1
        self.contract_type.setCurrentIndex(idx)
        self.contract_type.currentIndexChanged.connect(self._on_type_changed)
        lay.addRow(tr("contract_type") + ":", self.contract_type)
        
        # Contract start date
        self.contract_start_date = QDateEdit()
        self.contract_start_date.setCalendarPopup(True)
        if current_start_date:
            qd = QDate.fromString(current_start_date, "yyyy-MM-dd")
            if qd.isValid():
                self.contract_start_date.setDate(qd)
            else:
                self.contract_start_date.setDate(QDate.currentDate())
        else:
            self.contract_start_date.setDate(QDate.currentDate())
        self.contract_start_date.dateChanged.connect(self._on_date_changed)
        lay.addRow(tr("start_contract_date") + ":", self.contract_start_date)
        self.contract_end_date = QDateEdit()
        self.contract_end_date.setCalendarPopup(True)
        if current_end_date:
            qd = QDate.fromString(current_end_date, "yyyy-MM-dd")
            if qd.isValid():
                self.contract_end_date.setDate(qd)
            else:
                self.contract_end_date.setDate(QDate.currentDate().addYears(1))
        else:
            self.contract_end_date.setDate(QDate.currentDate().addYears(1))
        self.contract_end_date.dateChanged.connect(self._on_date_changed)
        lay.addRow(tr("contract_end_date") + ":", self.contract_end_date)
        self.days_at_start = QSpinBox()
        self.days_at_start.setMinimum(0)
        self.days_at_start.setMaximum(365)
        self.days_at_start.setValue(current_days_at_start)
        if tr("language") == "Language":  # English
            lay.addRow("Days at start (this year):", self.days_at_start)
        else:  # Serbian
            lay.addRow("Дани на почетку (ова година):", self.days_at_start)
        
        # Prorated calculation display
        self.prorated_info = QLabel()
        self.prorated_info.setWordWrap(True)
        self.prorated_info.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        lay.addRow("", self.prorated_info)
        
        self._current_old_end_date = current_end_date
        self._current_old_type = current_type
        self._current_old_working_days = current_working_days_per_week
        self._on_type_changed(idx)
        self._check_and_handle_field_conflicts()  # Set initial field states
        self._update_prorated_info()
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _on_type_changed(self, idx: int):
        is_fixed = idx == 0
        self.contract_start_date.setEnabled(is_fixed)
        self.contract_end_date.setEnabled(is_fixed)
        self.days_at_start.setEnabled(is_fixed)
        self._check_and_handle_field_conflicts()
        self._update_prorated_info()
    
    def _on_date_changed(self):
        self._check_and_handle_field_conflicts()
        self._update_prorated_info()
    
    def _on_working_days_changed(self):
        self._check_and_handle_field_conflicts()
        self._update_prorated_info()
    
    def _check_and_handle_field_conflicts(self):
        """Check for conflicting changes and disable/enable fields accordingly."""
        # Check if working days changed
        current_working_days = 6 if self.working_days_per_week.currentIndex() == 0 else 5
        working_days_changed = current_working_days != self._current_old_working_days
        
        if working_days_changed:
            # Working days changed - disable other contract modifications
            self.contract_type.setEnabled(False)
            self.contract_start_date.setEnabled(False) 
            self.contract_end_date.setEnabled(False)
            self.days_at_start.setEnabled(False)
            self.religion.setEnabled(False)
        else:
            # Working days not changed - enable fields based on contract type
            self.contract_type.setEnabled(True)
            self.religion.setEnabled(True)
            
            # Enable contract-specific fields based on type
            is_fixed = self.contract_type.currentIndex() == 0
            self.contract_start_date.setEnabled(is_fixed)
            self.contract_end_date.setEnabled(is_fixed)
            self.days_at_start.setEnabled(is_fixed)
    
    def _update_prorated_info(self):
        """Update the prorated calculation information display."""
        # Always try to calculate prorated days for any contract transition
        # (not just fixed-term contracts)
            
        try:
            from entitlement import calculate_prorated_days_for_contract_update
            
            old_end_date = self._current_old_end_date
            new_contract_type = "fixed_term" if self.contract_type.currentIndex() == 0 else "open_ended"
            
            # For open-ended contracts, new_end_date should be None
            if new_contract_type == "open_ended":
                new_end_date = None
            else:
                new_end_date = self.contract_end_date.date().toString("yyyy-MM-dd")
            
            working_days_idx = self.working_days_per_week.currentIndex()
            working_days = 6 if working_days_idx == 0 else 5
            
            # Determine contract types
            old_contract_type = self._current_old_type
            
            # Calculate prorated days
            prorated_results = calculate_prorated_days_for_contract_update(
                old_end_date,
                new_end_date,
                working_days,
                None,  # calculation_start_date
                old_contract_type,
                new_contract_type
            )
            
            # Check if working days changed
            old_working_days = self._current_old_working_days
            new_working_days = working_days
            working_days_changed = old_working_days != new_working_days
            
            info_text = ""
            
            # If working days changed, prioritize that message and explain field disabling
            if working_days_changed:
                if old_working_days == 5 and new_working_days == 6:
                    info_text += tr("working_days_5_to_6") + "\n"
                    info_text += tr("days_recalculated_20_to_24") + "\n\n"
                elif old_working_days == 6 and new_working_days == 5:
                    info_text += tr("working_days_6_to_5") + "\n"
                    info_text += tr("days_recalculated_24_to_20") + "\n\n"
                
                info_text += tr("fields_disabled_conflicts") + "\n"
                info_text += tr("revert_working_days_to_change")
            else:
                # Normal prorated calculation display when working days haven't changed
                if prorated_results:
                    info_text += tr("prorated_days_calculation") + "\n"
                    for result in prorated_results:
                        info_text += tr("days_period_format", 
                                      year=result['year'], 
                                      days=result['days'], 
                                      start=result['period_start'], 
                                      end=result['period_end']) + "\n"
                else:
                    # Provide more specific messaging based on contract transition
                    if old_contract_type == "open_ended" and new_contract_type == "fixed_term":
                        info_text += tr("converting_to_fixed_term") + "\n"
                    elif new_contract_type == "open_ended" and old_end_date:
                        info_text += tr("converting_to_permanent_no_days") + "\n"
                    elif new_contract_type == "open_ended":
                        info_text += tr("permanent_contract_full_entitlement") + "\n"
                    else:
                        info_text += tr("no_additional_prorated_days") + "\n"
            
            self.prorated_info.setText(info_text.strip())
                
        except Exception as e:
            self.prorated_info.setText(tr("calculation_error", error=str(e)))

    def get_data(self) -> dict:
        idx = self.contract_type.currentIndex()
        rel_idx = self.religion.currentIndex()
        working_days_idx = self.working_days_per_week.currentIndex()
        
        # Ensure we always return the correct database values regardless of UI language
        data = {
            "religion": "orthodox" if rel_idx == 0 else "catholic",
            "working_days_per_week": 6 if working_days_idx == 0 else 5,
            "contract_type": "fixed_term" if idx == 0 else "open_ended",
            "contract_end_date": self.contract_end_date.date().toString("yyyy-MM-dd") if idx == 0 else None,
            "contract_start_date": self.contract_start_date.date().toString("yyyy-MM-dd") if idx == 0 else None,
            "days_at_start": self.days_at_start.value() if idx == 0 else 0,
        }
        
        # Include prorated calculation results for all contract transitions
        try:
            from entitlement import calculate_prorated_days_for_contract_update
            new_contract_type = "fixed_term" if idx == 0 else "open_ended"
            data["prorated_results"] = calculate_prorated_days_for_contract_update(
                self._current_old_end_date,
                data["contract_end_date"],
                data["working_days_per_week"],
                None,  # calculation_start_date
                self._current_old_type,
                new_contract_type
            )
        except Exception:
            data["prorated_results"] = []
        
        # Check if working days per week changed and add recalculation info
        data["old_working_days_per_week"] = self._current_old_working_days
        data["working_days_changed"] = (self._current_old_working_days != data["working_days_per_week"])
            
        return data


# ---------- Set transferred days (from previous year) ----------


class SetTransferredDaysDialog(QDialog):
    def __init__(self, parent=None, year: Optional[int] = None, current_days: int = 0):
        super().__init__(parent)
        from datetime import date
        self._year = year or date.today().year
        if tr("language") == "Language":  # English
            self.setWindowTitle(f"Set transferred days (from previous year) – {self._year}")
        else:  # Serbian
            self.setWindowTitle(f"Постави пренете дане (из претходне године) – {self._year}")
        lay = QFormLayout(self)
        self.days = QSpinBox()
        self.days.setMinimum(0)
        self.days.setMaximum(365)
        self.days.setValue(current_days)
        if tr("language") == "Language":  # English
            lay.addRow("Days transferred:", self.days)
        else:  # Serbian
            lay.addRow("Пренети дани:", self.days)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def get_days(self) -> int:
        return self.days.value()


# ---------- Manage non-working days ----------


class ManageNonWorkingDaysDialog(QDialog):
    """Dialog to fetch, review, edit, and save Serbian public holidays."""
    
    def __init__(self, parent=None, conn: Optional[sqlite3.Connection] = None):
        super().__init__(parent)
        self._conn = conn
        self._holidays = []
        
        self.setWindowTitle(tr("manage_holidays"))
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(tr("year") + ":"))
        
        self.year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year - 2, current_year + 5):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self._on_year_changed)
        top_layout.addWidget(self.year_combo)
        
        self.fetch_btn = QPushButton(tr("fetch_from_ministry"))
        self.fetch_btn.clicked.connect(self._fetch_holidays)
        top_layout.addWidget(self.fetch_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        self.source_label = QLabel("")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self._refresh_table_headers()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setColumnHidden(6, True)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(tr("add_custom_holiday"))
        self.add_btn.clicked.connect(self._add_custom_holiday)
        btn_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton(tr("delete_selected"))
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._save_holidays)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Save).setText(tr("save"))
        self._button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        layout.addWidget(self._button_box)
        
        self._load_existing_holidays()
    
    def _refresh_table_headers(self):
        self.table.setHorizontalHeaderLabels([
            tr("include"),
            tr("date"),
            tr("name_serbian"),
            tr("name_english"),
            tr("holiday_type"),
            tr("applies_to"),
            tr("id_column"),
        ])
    
    def _applies_to_for_type(self, holiday_type: str) -> str:
        if holiday_type == "state":
            return tr("holiday_applies_everyone")
        if holiday_type == "orthodox":
            return tr("holiday_applies_orthodox_only")
        if holiday_type == "catholic":
            return tr("holiday_applies_catholic_only")
        return tr("holiday_applies_other")
    
    def _make_holiday_type_combo(self, current_key: str) -> QComboBox:
        combo = QComboBox()
        for key in ("state", "orthodox", "catholic", "other_religious"):
            label = {
                "state": tr("state"),
                "orthodox": tr("orthodox"),
                "catholic": tr("catholic"),
                "other_religious": tr("other_religious"),
            }[key]
            combo.addItem(label, key)
        idx = combo.findData(current_key)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        return combo
    
    def _wire_holiday_type_combo(self, combo: QComboBox):
        def on_change(_idx: int):
            key = combo.currentData()
            if key is None:
                return
            for r in range(self.table.rowCount()):
                if self.table.cellWidget(r, 4) is combo:
                    applies = self.table.item(r, 5)
                    if applies:
                        applies.setText(self._applies_to_for_type(key))
                    break
        combo.currentIndexChanged.connect(on_change)
    
    def _on_year_changed(self, year_text: str):
        self._load_existing_holidays()
    
    def _load_existing_holidays(self):
        if not self._conn:
            return
        
        from database import get_non_working_days
        
        year = int(self.year_combo.currentText())
        self._holidays = get_non_working_days(self._conn, year)
        
        if self._holidays:
            self.source_label.setText(tr("loaded_existing_holidays", count=len(self._holidays)))
            self._populate_table()
        else:
            self.source_label.setText(
                tr("no_holidays_use_fetch", action=tr("fetch_from_ministry"))
            )
            self.table.setRowCount(0)
    
    def _fetch_holidays(self):
        year = int(self.year_combo.currentText())
        
        progress = QProgressDialog(tr("fetching_holidays"), None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        try:
            from holiday_scraper import scrape_serbian_holidays
            
            holidays, source = scrape_serbian_holidays(year)
            
            progress.close()
            
            if not holidays:
                QMessageBox.warning(
                    self,
                    tr("no_data"),
                    tr("could_not_fetch_holidays", year=year, source=source),
                )
                return
            
            self._holidays = holidays
            self.source_label.setText(tr("source_prefix", source=source))
            self._populate_table()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                tr("error"),
                tr("failed_to_fetch_holidays", error=str(e)),
            )
    
    def _populate_table(self):
        self.table.setRowCount(len(self._holidays))
        
        for row, holiday in enumerate(self._holidays):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            cell_widget = QWidget()
            cell_lay = QHBoxLayout(cell_widget)
            cell_lay.addWidget(checkbox)
            cell_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_lay.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, cell_widget)
            
            date_item = QTableWidgetItem(holiday["date"])
            self.table.setItem(row, 1, date_item)
            
            name_sr_item = QTableWidgetItem(holiday["name_sr"])
            self.table.setItem(row, 2, name_sr_item)
            
            name_en_item = QTableWidgetItem(holiday.get("name_en", ""))
            self.table.setItem(row, 3, name_en_item)
            
            htype = holiday["holiday_type"]
            type_combo = self._make_holiday_type_combo(htype)
            self._wire_holiday_type_combo(type_combo)
            self.table.setCellWidget(row, 4, type_combo)
            
            applies_item = QTableWidgetItem(self._applies_to_for_type(htype))
            applies_item.setFlags(applies_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, applies_item)
            
            id_item = QTableWidgetItem(str(holiday.get("id", "")))
            self.table.setItem(row, 6, id_item)
    
    def _add_custom_holiday(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        cell_widget = QWidget()
        cell_lay = QHBoxLayout(cell_widget)
        cell_lay.addWidget(checkbox)
        cell_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_lay.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, cell_widget)
        
        year = self.year_combo.currentText()
        date_item = QTableWidgetItem(f"{year}-01-01")
        self.table.setItem(row, 1, date_item)
        
        self.table.setItem(row, 2, QTableWidgetItem(""))
        self.table.setItem(row, 3, QTableWidgetItem(""))
        
        type_combo = self._make_holiday_type_combo("state")
        self._wire_holiday_type_combo(type_combo)
        self.table.setCellWidget(row, 4, type_combo)
        
        applies_item = QTableWidgetItem(self._applies_to_for_type("state"))
        applies_item.setFlags(applies_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, applies_item)
        
        self.table.setItem(row, 6, QTableWidgetItem(""))
    
    def _delete_selected(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        
        if not selected_rows:
            QMessageBox.information(
                self,
                tr("no_selection"),
                tr("select_rows_to_delete"),
            )
            return
        
        reply = QMessageBox.question(
            self,
            tr("confirm_delete"),
            tr("confirm_delete_holidays", count=len(selected_rows)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for r in sorted(selected_rows, reverse=True):
                self.table.removeRow(r)
    
    def _save_holidays(self):
        if not self._conn:
            QMessageBox.critical(self, tr("error"), tr("no_database_connection"))
            return
        
        holidays_to_save = []
        
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if not checkbox or not checkbox.isChecked():
                continue
            
            date_str = self.table.item(row, 1).text().strip()
            name_sr = self.table.item(row, 2).text().strip()
            name_en = self.table.item(row, 3).text().strip()
            type_combo = self.table.cellWidget(row, 4)
            holiday_type = type_combo.currentData()
            if holiday_type is None:
                holiday_type = "state"
            
            if not date_str or not name_sr:
                QMessageBox.warning(
                    self,
                    tr("validation_error"),
                    tr("row_date_serbian_required", row=row + 1),
                )
                return
            
            try:
                date.fromisoformat(date_str)
            except ValueError:
                QMessageBox.warning(
                    self,
                    tr("validation_error"),
                    tr("row_invalid_date_yyyy_mm_dd", row=row + 1),
                )
                return
            
            holidays_to_save.append({
                "date": date_str,
                "name_sr": name_sr,
                "name_en": name_en,
                "holiday_type": holiday_type,
            })
        
        if not holidays_to_save:
            QMessageBox.information(
                self,
                tr("no_holidays"),
                tr("no_holidays_selected_save"),
            )
            return
        
        year = self.year_combo.currentText()
        reply = QMessageBox.question(
            self,
            tr("confirm_save_non_working_title"),
            tr("confirm_save_non_working", count=len(holidays_to_save), year=year),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from database import save_non_working_days, recalculate_all_vacation_records_with_working_days
            
            count = save_non_working_days(self._conn, holidays_to_save)
            
            progress = QProgressDialog(tr("recalculating_vacation"), None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            recalculate_all_vacation_records_with_working_days(self._conn)
            
            progress.close()
            
            QMessageBox.information(
                self,
                tr("success"),
                tr("saved_non_working_recalculated", count=count, year=year),
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("error"),
                tr("failed_to_save_holidays_msg", error=str(e)),
            )


# ---------- Special Leave Dialog ----------


class SpecialLeaveDialog(QDialog):
    def __init__(self, parent, conn, employee_id: int, employee_name: str):
        super().__init__(parent)
        self._conn = conn
        self._employee_id = employee_id
        self._employee_name = employee_name
        
        self.setWindowTitle(f"{tr('manage_special_leaves')} - {employee_name}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Important policy notice
        policy_notice = QLabel()
        if tr("language") == "Language":  # English
            policy_notice.setText(
                "⚠️ IMPORTANT: Special leave entitlements reset annually on January 1st.\n"
                "Unused special leave days cannot be transferred to the next year and will be lost."
            )
        else:  # Serbian
            policy_notice.setText(
                "⚠️ ВАЖНО: Права на плаћено одсуство се ресетују сваке године 1. јануара.\n"
                "Неискоришћени дани плаћеног одсуства се не могу пренети у следећу годину и биће изгубљени."
            )
        policy_notice.setWordWrap(True)
        policy_notice.setStyleSheet("""
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 5px 0 15px 0;
            color: #856404;
            font-weight: bold;
        """)
        layout.addWidget(policy_notice)
        
        # Balance section
        balance_group = QLabel(tr("special_leave_balance"))
        balance_group.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px 0;")
        layout.addWidget(balance_group)
        
        self._balance_table = QTableWidget()
        self._balance_table.setColumnCount(4)
        self._balance_table.setHorizontalHeaderLabels([
            tr("special_leave_type"),
            tr("entitled"), 
            tr("used_lowercase"),
            tr("remaining")
        ])
        self._balance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._balance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._balance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._balance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._balance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._balance_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._balance_table)
        
        # Usage history section
        history_group = QLabel(tr("used_days_off"))  # Reusing existing translation
        history_group.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px 0;")
        layout.addWidget(history_group)
        
        self._usage_table = QTableWidget()
        self._usage_table.setColumnCount(5)
        self._usage_table.setHorizontalHeaderLabels([
            tr("special_leave_type"),
            tr("usage_date"),
            tr("days_used"),
            tr("reason_notes"),
            ""  # Delete button column
        ])
        self._usage_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._usage_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._usage_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._usage_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._usage_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._usage_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._usage_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._add_button = QPushButton(tr("add_special_leave"))
        self._add_button.clicked.connect(self._add_special_leave)
        button_layout.addWidget(self._add_button)
        
        button_layout.addStretch()
        
        self._close_button = QPushButton(tr("close"))
        self._close_button.clicked.connect(self.accept)
        button_layout.addWidget(self._close_button)
        
        layout.addLayout(button_layout)
        
        self._refresh_data()
    
    def _refresh_data(self):
        """Refresh balance and usage tables."""
        from datetime import date
        from database import get_special_leave_usage_for_employee
        
        current_year = date.today().year
        
        # Refresh balance table
        balances = get_special_leave_balance_for_employee(self._conn, self._employee_id, current_year)
        
        self._balance_table.setRowCount(len(balances))
        for i, (type_id, balance) in enumerate(balances.items()):
            # Use Serbian names if current language is Serbian
            type_name = balance['type_name_sr'] if tr("language") != "Language" else balance['type_name_en']
            
            self._balance_table.setItem(i, 0, QTableWidgetItem(type_name))
            self._balance_table.setItem(i, 1, QTableWidgetItem(str(balance['entitled'])))
            self._balance_table.setItem(i, 2, QTableWidgetItem(str(balance['used'])))
            self._balance_table.setItem(i, 3, QTableWidgetItem(str(balance['remaining'])))
            
            # Store type_id for later use
            self._balance_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, type_id)
        
        # Refresh usage table
        usage_records = get_special_leave_usage_for_employee(self._conn, self._employee_id, current_year)
        
        self._usage_table.setRowCount(len(usage_records))
        for i, record in enumerate(usage_records):
            # Use Serbian names if current language is Serbian
            type_name = record['type_name_sr'] if tr("language") != "Language" else record['type_name_en']
            
            self._usage_table.setItem(i, 0, QTableWidgetItem(type_name))
            self._usage_table.setItem(i, 1, QTableWidgetItem(record['usage_date']))
            self._usage_table.setItem(i, 2, QTableWidgetItem(str(record['days_used'])))
            self._usage_table.setItem(i, 3, QTableWidgetItem(record['reason_notes'] or ""))
            
            # Delete button
            delete_btn = QPushButton("🗑")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, record_id=record['id']: self._delete_usage(record_id))
            self._usage_table.setCellWidget(i, 4, delete_btn)
    
    def _add_special_leave(self):
        """Open dialog to add new special leave usage."""
        dialog = AddSpecialLeaveUsageDialog(self, self._conn, self._employee_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_data()
    
    def _delete_usage(self, usage_id: int):
        """Delete a special leave usage record."""
        reply = QMessageBox.question(
            self,
            tr("confirm"),  # Reusing existing translation
            "Delete this special leave usage record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from database import delete_special_leave_usage
                delete_special_leave_usage(self._conn, usage_id)
                self._refresh_data()
            except Exception as e:
                QMessageBox.critical(self, tr("error"), str(e))


class AddSpecialLeaveUsageDialog(QDialog):
    def __init__(self, parent, conn, employee_id: int):
        super().__init__(parent)
        self._conn = conn
        self._employee_id = employee_id
        
        self.setWindowTitle(tr("add_special_leave"))
        
        layout = QFormLayout(self)
        
        # Special leave type selector
        self._type_combo = QComboBox()
        self._populate_leave_types()
        layout.addRow(tr("special_leave_type") + ":", self._type_combo)
        
        # Usage date
        self._usage_date = QDateEdit()
        self._usage_date.setCalendarPopup(True)
        self._usage_date.setDate(QDate.currentDate())
        layout.addRow(tr("usage_date") + ":", self._usage_date)
        
        # Days used
        self._days_used = QSpinBox()
        self._days_used.setMinimum(1)
        self._days_used.setMaximum(30)
        self._days_used.setValue(1)
        layout.addRow(tr("days_used") + ":", self._days_used)
        
        # Reason/notes
        self._reason_notes = QPlainTextEdit()
        self._reason_notes.setMaximumHeight(80)
        layout.addRow(tr("reason_notes") + ":", self._reason_notes)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _populate_leave_types(self):
        """Populate the leave type combo box."""
        leave_types = get_special_leave_types(self._conn)
        
        for leave_type in leave_types:
            # Use Serbian names if current language is Serbian
            display_name = leave_type['name_sr'] if tr("language") != "Language" else leave_type['name_en']
            self._type_combo.addItem(display_name, leave_type['id'])
    
    def _on_accept(self):
        """Validate and save the special leave usage."""
        from datetime import date
        from database import add_special_leave_usage, get_special_leave_balance_for_employee
        
        type_id = self._type_combo.currentData()
        usage_date = self._usage_date.date().toString("yyyy-MM-dd")
        days_used = self._days_used.value()
        reason_notes = self._reason_notes.toPlainText().strip()
        
        # Check if employee has enough remaining days
        usage_year = self._usage_date.date().year()
        balances = get_special_leave_balance_for_employee(self._conn, self._employee_id, usage_year)
        
        if type_id in balances:
            remaining = balances[type_id]['remaining']
            if days_used > remaining:
                QMessageBox.warning(
                    self,
                    tr("insufficient_special_leave"),
                    f"Cannot use {days_used} days. Only {remaining} days remaining for this leave type."
                )
                return
        
        try:
            add_special_leave_usage(self._conn, self._employee_id, type_id, usage_date, days_used, reason_notes)
            QMessageBox.information(self, tr("success"), tr("special_leave_added"))  # Reusing existing translation
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))


class AdjustSpecialLeaveEntitlementsDialog(QDialog):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self._conn = conn
        
        self.setWindowTitle(tr("adjust_special_leave_entitlements"))
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Adjust the number of days entitled for each special leave type:")
        if tr("language") != "Language":  # Serbian
            instructions.setText("Подесите број дана на које запослени има право за сваку врсту плаћеног одсуства:")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Policy reminder
        policy_reminder = QLabel()
        if tr("language") == "Language":  # English
            policy_reminder.setText(
                "📅 Reminder: Special leave entitlements reset annually. "
                "Unused days are not transferred between years."
            )
        else:  # Serbian
            policy_reminder.setText(
                "📅 Подсетник: Права на плаћено одсуство се ресетују сваке године. "
                "Неискоришћени дани се не преносе између година."
            )
        policy_reminder.setWordWrap(True)
        policy_reminder.setStyleSheet("""
            background-color: #e3f2fd;
            border: 1px solid #90caf9;
            border-radius: 4px;
            padding: 8px;
            margin: 5px 0 10px 0;
            color: #1565c0;
            font-style: italic;
        """)
        layout.addWidget(policy_reminder)
        
        # Table for editing entitlements
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([
            tr("special_leave_type"),
            tr("days_entitled"),
            ""  # Save button column
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._close_button = QPushButton(tr("close"))
        self._close_button.clicked.connect(self.accept)
        button_layout.addWidget(self._close_button)
        
        layout.addLayout(button_layout)
        
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with current special leave types and entitlements."""
        leave_types = get_special_leave_types(self._conn)
        
        self._table.setRowCount(len(leave_types))
        for i, leave_type in enumerate(leave_types):
            # Use Serbian names if current language is Serbian
            type_name = leave_type['name_sr'] if tr("language") != "Language" else leave_type['name_en']
            
            # Type name (read-only)
            name_item = QTableWidgetItem(type_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 0, name_item)
            
            # Days entitled (editable via spinbox)
            days_spinbox = QSpinBox()
            days_spinbox.setMinimum(0)
            days_spinbox.setMaximum(365)
            days_spinbox.setValue(leave_type['days_entitled'])
            self._table.setCellWidget(i, 1, days_spinbox)
            
            # Update button
            update_btn = QPushButton(tr("save"))
            update_btn.clicked.connect(
                lambda checked, type_id=leave_type['id'], spinbox=days_spinbox: 
                self._update_entitlement(type_id, spinbox.value())
            )
            self._table.setCellWidget(i, 2, update_btn)
    
    def _update_entitlement(self, type_id: int, new_days: int):
        """Update the entitlement for a specific leave type."""
        try:
            update_special_leave_entitlement(self._conn, type_id, new_days)
            QMessageBox.information(self, tr("success"), tr("entitlements_updated"))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))
