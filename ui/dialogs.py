"""Dialogs: DB path (choose/create, locate), add employee, schedule vacation, add earned days, contract extension."""
from datetime import date

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
    QWidget,
)
from PyQt6.QtCore import QDate
from typing import Optional

from entitlement import prorated_vacation_entitlement_for_year


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


# ---------- Add employee ----------


class AddEmployeeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add employee")
        lay = QFormLayout(self)
        self.jmbg = QLineEdit()
        self.jmbg.setPlaceholderText("13 digits")
        lay.addRow("JMBG:", self.jmbg)
        self.first_name = QLineEdit()
        lay.addRow("First name:", self.first_name)
        self.last_name = QLineEdit()
        lay.addRow("Last name:", self.last_name)
        self.contract_type = QComboBox()
        self.contract_type.addItems(["Fixed term (with end date)", "Open-ended (no end date)"])
        self.contract_type.currentIndexChanged.connect(self._on_contract_type_changed)
        lay.addRow("Contract type:", self.contract_type)
        self.contract_end_date = QDateEdit()
        self.contract_end_date.setCalendarPopup(True)
        self.contract_end_date.setDate(QDate.currentDate().addYears(1))
        self.contract_end_date.dateChanged.connect(lambda _d: self._update_prorated_label())
        lay.addRow("Contract end date:", self.contract_end_date)
        self._prorated_label = QLabel()
        self._prorated_label.setWordWrap(True)
        lay.addRow("Vacation days (this year, prorated):", self._prorated_label)
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
        n = prorated_vacation_entitlement_for_year(date.today(), end_str)
        self._prorated_label.setText(
            str(n)
            + " (based on today's date, contract type, and end of employment within this year)"
        )

    def _validate_jmbg(self) -> Optional[str]:
        """Return None if valid, else error message."""
        j = self.jmbg.text().strip()
        if len(j) != 13 or not j.isdigit():
            return "JMBG must be exactly 13 digits."
        return None

    def _on_accept(self):
        err = self._validate_jmbg()
        if err:
            QMessageBox.warning(self, "Validation", err)
            return
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            QMessageBox.warning(self, "Validation", "First name and last name are required.")
            return
        self.accept()

    def get_data(self) -> dict:
        idx = self.contract_type.currentIndex()
        contract_type = "fixed_term" if idx == 0 else "open_ended"
        end_date = self.contract_end_date.date().toString("yyyy-MM-dd") if idx == 0 else None
        days_at_start = prorated_vacation_entitlement_for_year(date.today(), end_date)
        return {
            "jmbg": self.jmbg.text().strip(),
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "contract_type": contract_type,
            "contract_end_date": end_date,
            "days_at_start": days_at_start,
        }


# ---------- Schedule vacation / day off ----------


class ScheduleVacationDialog(QDialog):
    def __init__(self, parent=None, employee_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Schedule vacation / day off" + (f" – {employee_name}" if employee_name else ""))
        lay = QFormLayout(self)
        self.booking_date = QDateEdit()
        self.booking_date.setDate(QDate.currentDate())
        self.booking_date.setCalendarPopup(True)
        lay.addRow("Booking date:", self.booking_date)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        lay.addRow("Start date:", self.start_date)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        lay.addRow("End date:", self.end_date)
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
        self.setWindowTitle("Add earned vacation days")
        lay = QFormLayout(self)
        self.earned_date = QDateEdit()
        self.earned_date.setDate(QDate.currentDate())
        self.earned_date.setCalendarPopup(True)
        lay.addRow("Date earned:", self.earned_date)
        self.number_of_days = QSpinBox()
        self.number_of_days.setMinimum(1)
        self.number_of_days.setMaximum(365)
        self.number_of_days.setValue(1)
        lay.addRow("Number of days:", self.number_of_days)
        self.reason_notes = QPlainTextEdit()
        self.reason_notes.setPlaceholderText("e.g. blood donation, overtime, stepping in, public holiday…")
        self.reason_notes.setMaximumHeight(80)
        lay.addRow("Reason / notes:", self.reason_notes)
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
    ):
        super().__init__(parent)
        self.setWindowTitle("Contract date / type")
        lay = QFormLayout(self)
        self.contract_type = QComboBox()
        self.contract_type.addItems(["Fixed term (with end date)", "Open-ended (no end date)"])
        idx = 0 if current_type == "fixed_term" else 1
        self.contract_type.setCurrentIndex(idx)
        self.contract_type.currentIndexChanged.connect(self._on_type_changed)
        lay.addRow("Contract type:", self.contract_type)
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
        lay.addRow("Contract end date:", self.contract_end_date)
        self.days_at_start = QSpinBox()
        self.days_at_start.setMinimum(0)
        self.days_at_start.setMaximum(365)
        self.days_at_start.setValue(current_days_at_start)
        lay.addRow("Days at start (this year):", self.days_at_start)
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
        return {
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
        self.setWindowTitle(f"Set transferred days (from previous year) – {self._year}")
        lay = QFormLayout(self)
        self.days = QSpinBox()
        self.days.setMinimum(0)
        self.days.setMaximum(365)
        self.days.setValue(current_days)
        lay.addRow("Days transferred:", self.days)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def get_days(self) -> int:
        return self.days.value()
