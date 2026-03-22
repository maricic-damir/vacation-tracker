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
        n = prorated_vacation_entitlement_for_year(start_date, end_str)
        if tr("language") == "Language":  # English
            self._prorated_label.setText(
                str(n)
                + " (based on start contract date, contract type, and end of employment within this year)"
            )
        else:  # Serbian
            self._prorated_label.setText(
                str(n)
                + " (на основу датума почетка уговора, типа уговора и краја запослења у овој години)"
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
        days_at_start = prorated_vacation_entitlement_for_year(start_date, end_date)
        religion_idx = self.religion.currentIndex()
        religion = "orthodox" if religion_idx == 0 else "catholic"
        return {
            "jmbg": self.jmbg.text().strip(),
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "religion": religion,
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
        current_days_at_start: int = 0,
        current_religion: str = "orthodox",
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("edit_contract"))
        lay = QFormLayout(self)
        self.religion = QComboBox()
        self.religion.addItems([tr("orthodox"), tr("catholic")])
        rel_idx = 0 if current_religion == "orthodox" else 1
        self.religion.setCurrentIndex(rel_idx)
        lay.addRow(tr("religion") + ":", self.religion)
        self.contract_type = QComboBox()
        if tr("language") == "Language":  # English
            self.contract_type.addItems(["Fixed term (with end date)", "Open-ended (no end date)"])
        else:  # Serbian
            self.contract_type.addItems(["Одређено (са датумом истека)", "Неодређено (без датума истека)"])
        idx = 0 if current_type == "fixed_term" else 1
        self.contract_type.setCurrentIndex(idx)
        self.contract_type.currentIndexChanged.connect(self._on_type_changed)
        lay.addRow(tr("contract_type") + ":", self.contract_type)
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
        lay.addRow(tr("contract_end_date") + ":", self.contract_end_date)
        self.days_at_start = QSpinBox()
        self.days_at_start.setMinimum(0)
        self.days_at_start.setMaximum(365)
        self.days_at_start.setValue(current_days_at_start)
        if tr("language") == "Language":  # English
            lay.addRow("Days at start (this year):", self.days_at_start)
        else:  # Serbian
            lay.addRow("Дани на почетку (ова година):", self.days_at_start)
        self._on_type_changed(idx)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _on_type_changed(self, idx: int):
        is_fixed = idx == 0
        self.contract_end_date.setEnabled(is_fixed)
        self.days_at_start.setEnabled(is_fixed)

    def get_data(self) -> dict:
        idx = self.contract_type.currentIndex()
        rel_idx = self.religion.currentIndex()
        return {
            "religion": "orthodox" if rel_idx == 0 else "catholic",
            "contract_type": "fixed_term" if idx == 0 else "open_ended",
            "contract_end_date": self.contract_end_date.date().toString("yyyy-MM-dd") if idx == 0 else None,
            "days_at_start": self.days_at_start.value() if idx == 0 else 0,
        }


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
        
        # Year selection and fetch button
        top_layout = QHBoxLayout()
        if tr("language") == "Language":  # English
            top_layout.addWidget(QLabel("Year:"))
        else:  # Serbian
            top_layout.addWidget(QLabel("Година:"))
        
        self.year_combo = QComboBox()
        current_year = date.today().year
        for year in range(current_year - 2, current_year + 5):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self._on_year_changed)
        top_layout.addWidget(self.year_combo)
        
        if tr("language") == "Language":  # English
            fetch_text = "Fetch from Ministry Website"
        else:  # Serbian
            fetch_text = "Преузми са сајта министарства"
        self.fetch_btn = QPushButton(fetch_text)
        self.fetch_btn.clicked.connect(self._fetch_holidays)
        top_layout.addWidget(self.fetch_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Source info label
        self.source_label = QLabel("")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        
        # Table for holidays
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Include", "Date", "Name (Serbian)", "Name (English)", "Type", "Applies To", "ID"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Make columns resizable
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Hide ID column (used internally)
        self.table.setColumnHidden(6, True)
        
        layout.addWidget(self.table)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Custom Holiday")
        self.add_btn.clicked.connect(self._add_custom_holiday)
        btn_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_holidays)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load existing holidays for current year
        self._load_existing_holidays()
    
    def _on_year_changed(self, year_text: str):
        """Load existing holidays when year changes."""
        self._load_existing_holidays()
    
    def _load_existing_holidays(self):
        """Load existing holidays from database for selected year."""
        if not self._conn:
            return
        
        from database import get_non_working_days
        
        year = int(self.year_combo.currentText())
        self._holidays = get_non_working_days(self._conn, year)
        
        if self._holidays:
            self.source_label.setText(f"Loaded {len(self._holidays)} existing holidays from database")
            self._populate_table()
        else:
            self.source_label.setText("No holidays in database for this year. Click 'Fetch from Ministry Website' to load.")
            self.table.setRowCount(0)
    
    def _fetch_holidays(self):
        """Fetch holidays from web sources."""
        year = int(self.year_combo.currentText())
        
        # Show progress dialog
        progress = QProgressDialog("Fetching holidays...", None, 0, 0, self)
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
                    "No Data",
                    f"Could not fetch holidays for {year}.\n\n{source}\n\nYou can add holidays manually."
                )
                return
            
            self._holidays = holidays
            self.source_label.setText(f"Source: {source}")
            self._populate_table()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to fetch holidays: {str(e)}"
            )
    
    def _populate_table(self):
        """Populate table with current holidays list."""
        self.table.setRowCount(len(self._holidays))
        
        for row, holiday in enumerate(self._holidays):
            # Checkbox for include/exclude
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, cell_widget)
            
            # Date
            date_item = QTableWidgetItem(holiday['date'])
            self.table.setItem(row, 1, date_item)
            
            # Name (Serbian) - editable
            name_sr_item = QTableWidgetItem(holiday['name_sr'])
            self.table.setItem(row, 2, name_sr_item)
            
            # Name (English) - editable
            name_en_item = QTableWidgetItem(holiday.get('name_en', ''))
            self.table.setItem(row, 3, name_en_item)
            
            # Type - combo box
            type_combo = QComboBox()
            type_combo.addItems(['state', 'orthodox', 'catholic', 'other_religious'])
            type_combo.setCurrentText(holiday['holiday_type'])
            self.table.setCellWidget(row, 4, type_combo)
            
            # Applies To - non-editable label
            holiday_type = holiday['holiday_type']
            if holiday_type == 'state':
                applies_to = "Everyone"
            elif holiday_type == 'orthodox':
                applies_to = "Orthodox only"
            elif holiday_type == 'catholic':
                applies_to = "Catholic only"
            else:
                applies_to = "Other"
            applies_item = QTableWidgetItem(applies_to)
            applies_item.setFlags(applies_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, applies_item)
            
            # ID (hidden)
            id_item = QTableWidgetItem(str(holiday.get('id', '')))
            self.table.setItem(row, 6, id_item)
    
    def _add_custom_holiday(self):
        """Add a custom holiday row."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        cell_widget = QWidget()
        layout = QHBoxLayout(cell_widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, cell_widget)
        
        # Date - use current year
        year = self.year_combo.currentText()
        date_item = QTableWidgetItem(f"{year}-01-01")
        self.table.setItem(row, 1, date_item)
        
        # Names
        self.table.setItem(row, 2, QTableWidgetItem(""))
        self.table.setItem(row, 3, QTableWidgetItem(""))
        
        # Type
        type_combo = QComboBox()
        type_combo.addItems(['state', 'orthodox', 'catholic', 'other_religious'])
        self.table.setCellWidget(row, 4, type_combo)
        
        # Applies To
        applies_item = QTableWidgetItem("Everyone")
        applies_item.setFlags(applies_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 5, applies_item)
        
        # ID
        self.table.setItem(row, 6, QTableWidgetItem(""))
    
    def _delete_selected(self):
        """Delete selected rows."""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select rows to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} selected holiday(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                self.table.removeRow(row)
    
    def _save_holidays(self):
        """Save holidays to database."""
        if not self._conn:
            QMessageBox.critical(self, "Error", "No database connection.")
            return
        
        # Collect holidays from table
        holidays_to_save = []
        
        for row in range(self.table.rowCount()):
            # Check if included
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if not checkbox or not checkbox.isChecked():
                continue
            
            date_str = self.table.item(row, 1).text().strip()
            name_sr = self.table.item(row, 2).text().strip()
            name_en = self.table.item(row, 3).text().strip()
            type_combo = self.table.cellWidget(row, 4)
            holiday_type = type_combo.currentText()
            
            # Validate
            if not date_str or not name_sr:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Row {row + 1}: Date and Serbian name are required."
                )
                return
            
            try:
                date.fromisoformat(date_str)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Row {row + 1}: Invalid date format. Use YYYY-MM-DD."
                )
                return
            
            holidays_to_save.append({
                'date': date_str,
                'name_sr': name_sr,
                'name_en': name_en,
                'holiday_type': holiday_type
            })
        
        if not holidays_to_save:
            QMessageBox.information(self, "No Holidays", "No holidays selected to save.")
            return
        
        # Confirm save
        year = self.year_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Confirm Save",
            f"Save {len(holidays_to_save)} non-working day(s) for {year}?\n\n"
            f"This will update the database and recalculate all vacation records.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from database import save_non_working_days, recalculate_all_vacation_records_with_working_days
            
            count = save_non_working_days(self._conn, holidays_to_save)
            
            # Recalculate all vacation records with new holiday data
            progress = QProgressDialog("Recalculating vacation records...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            recalculate_all_vacation_records_with_working_days(self._conn)
            
            progress.close()
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully saved {count} non-working day(s) for {year}.\n\n"
                f"All vacation records have been recalculated."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save holidays: {str(e)}"
            )
