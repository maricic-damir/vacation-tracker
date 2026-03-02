"""Screen 2: Employee details, balance summary, used days table, earned days table, actions."""
from datetime import date

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QDialog,
)
from PyQt6.QtCore import Qt

from ui.dialogs import (
    ScheduleVacationDialog,
    AddEarnedDaysDialog,
    ContractDialog,
    SetTransferredDaysDialog,
    warn_past_start_date,
)


class EmployeeDetailScreen(QWidget):
    def __init__(self, conn_getter, refresh_callback, on_back):
        super().__init__()
        self._conn = conn_getter
        self._refresh = refresh_callback
        self._on_back = on_back
        self._employee_id = None
        lay = QVBoxLayout(self)

        # Back
        btn_back = QPushButton("← Back to list")
        btn_back.clicked.connect(lambda: on_back() if on_back else None)
        lay.addWidget(btn_back)

        # Properties (list)
        self._props_group = QGroupBox("Employee")
        self._props_layout = QFormLayout(self._props_group)
        lay.addWidget(self._props_group)

        # Balance summary
        self._balance_label = QLabel("")
        lay.addWidget(self._balance_label)

        # Used days off table
        used_group = QGroupBox("Used days off")
        self._used_table = QTableWidget()
        self._used_table.setColumnCount(4)
        self._used_table.setHorizontalHeaderLabels(["Booking date", "Start", "End", "Days"])
        self._used_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        used_layout = QVBoxLayout(used_group)
        used_layout.addWidget(self._used_table)
        lay.addWidget(used_group)

        # Earned days table
        earned_group = QGroupBox("Earned days")
        self._earned_table = QTableWidget()
        self._earned_table.setColumnCount(4)
        self._earned_table.setHorizontalHeaderLabels(["Date earned", "Days", "Reason / notes", "Created"])
        self._earned_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        earned_layout = QVBoxLayout(earned_group)
        earned_layout.addWidget(self._earned_table)
        lay.addWidget(earned_group)

        # Buttons
        btn_lay = QHBoxLayout()
        btn_contract = QPushButton("Contract date / type")
        btn_contract.clicked.connect(self._edit_contract)
        btn_lay.addWidget(btn_contract)
        btn_transferred = QPushButton("Set transferred days")
        btn_transferred.clicked.connect(self._set_transferred_days)
        btn_lay.addWidget(btn_transferred)
        btn_schedule = QPushButton("Schedule vacation / day off")
        btn_schedule.clicked.connect(self._schedule_vacation)
        btn_lay.addWidget(btn_schedule)
        btn_earned = QPushButton("Add earned days")
        btn_earned.clicked.connect(self._add_earned_days)
        btn_lay.addWidget(btn_earned)
        btn_lay.addStretch()
        lay.addLayout(btn_lay)

    def set_employee(self, employee_id: int):
        self._employee_id = employee_id
        self._load()

    def _load(self):
        conn = self._conn()
        if not conn or not self._employee_id:
            return
        from db_helpers import get_employee, get_year_balance, list_vacation_records_employee, list_earned_days
        from database import ensure_year_balance

        emp = get_employee(conn, self._employee_id)
        if not emp:
            return
        year = date.today().year
        ensure_year_balance(conn, self._employee_id, year, emp["contract_type"])
        balance = get_year_balance(conn, self._employee_id, year)

        # Clear and fill props
        while self._props_layout.rowCount():
            self._props_layout.removeRow(0)
        self._props_layout.addRow("JMBG:", QLabel(emp.get("jmbg", "")))
        self._props_layout.addRow("First name:", QLabel(emp.get("first_name", "")))
        self._props_layout.addRow("Last name:", QLabel(emp.get("last_name", "")))
        ct = "Fixed term" if emp.get("contract_type") == "fixed_term" else "Open-ended"
        if emp.get("contract_end_date"):
            ct += f" (until {emp['contract_end_date']})"
        self._props_layout.addRow("Contract:", QLabel(ct))
        self._props_layout.addRow("Status:", QLabel("Active" if emp.get("is_active") else "Archived"))

        # Balance text
        trans_note = ""
        if date.today().month > 6:
            trans_note = " (transferred from previous year must be used by June; not counted after June)"
        self._balance_label.setText(
            f"Year {year}: Days at start: {balance['days_at_start']} | "
            f"Transferred from previous: {balance['days_transferred']}{trans_note} | "
            f"Earned: {balance['days_earned']} | Used: {balance['days_used']} | Left: {balance['days_left']}"
        )

        # Used days
        records = list_vacation_records_employee(conn, self._employee_id)
        from db_helpers import count_days_in_range
        self._used_table.setRowCount(len(records))
        for i, r in enumerate(records):
            self._used_table.setItem(i, 0, QTableWidgetItem(str(r.get("booking_date", ""))))
            self._used_table.setItem(i, 1, QTableWidgetItem(str(r.get("start_date", ""))))
            self._used_table.setItem(i, 2, QTableWidgetItem(str(r.get("end_date", ""))))
            days = count_days_in_range(r["start_date"], r["end_date"])
            self._used_table.setItem(i, 3, QTableWidgetItem(str(days)))
        self._used_table.resizeRowsToContents()

        # Earned days
        earned = list_earned_days(conn, self._employee_id)
        self._earned_table.setRowCount(len(earned))
        for i, r in enumerate(earned):
            self._earned_table.setItem(i, 0, QTableWidgetItem(str(r.get("earned_date", ""))))
            self._earned_table.setItem(i, 1, QTableWidgetItem(str(r.get("number_of_days", ""))))
            self._earned_table.setItem(i, 2, QTableWidgetItem(str(r.get("reason_notes", ""))))
            self._earned_table.setItem(i, 3, QTableWidgetItem(str(r.get("created_at", ""))[:10]))
        self._earned_table.resizeRowsToContents()

    def _set_transferred_days(self):
        if not self._employee_id:
            return
        conn = self._conn()
        if not conn:
            return
        from db_helpers import set_transferred_days, get_year_balance
        year = date.today().year
        balance = get_year_balance(conn, self._employee_id, year)
        dlg = SetTransferredDaysDialog(self, year, balance.get("days_transferred", 0))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            set_transferred_days(conn, self._employee_id, year, dlg.get_days())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load()
        self._refresh()

    def _edit_contract(self):
        if not self._employee_id:
            return
        conn = self._conn()
        if not conn:
            return
        from db_helpers import get_employee, get_year_balance, update_employee_contract, set_days_at_start
        emp = get_employee(conn, self._employee_id)
        if not emp:
            return
        year = date.today().year
        balance = get_year_balance(conn, self._employee_id, year)
        dlg = ContractDialog(
            self,
            current_type=emp.get("contract_type", "fixed_term"),
            current_end_date=emp.get("contract_end_date") or None,
            current_days_at_start=balance.get("days_at_start", 0),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            update_employee_contract(conn, self._employee_id, data["contract_type"], data["contract_end_date"])
            if data["contract_type"] == "fixed_term":
                set_days_at_start(conn, self._employee_id, year, data.get("days_at_start", 0))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load()
        self._refresh()

    def _schedule_vacation(self):
        if not self._employee_id:
            return
        conn = self._conn()
        if not conn:
            return
        from db_helpers import get_employee, add_vacation_record
        from database import run_completion_job
        emp = get_employee(conn, self._employee_id)
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}" if emp else ""
        dlg = ScheduleVacationDialog(self, name)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
        if start > end:
            QMessageBox.warning(self, "Invalid dates", "Start date must be before or equal to end date.")
            return
        if start < date.today() and not warn_past_start_date(self, start):
            return
        is_completed = end < date.today()
        try:
            add_vacation_record(
                conn, self._employee_id,
                data["booking_date"], data["start_date"], data["end_date"],
                is_completed=is_completed,
            )
            run_completion_job(conn)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load()
        self._refresh()

    def _add_earned_days(self):
        if not self._employee_id:
            return
        conn = self._conn()
        if not conn:
            return
        dlg = AddEarnedDaysDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        from db_helpers import add_earned_days
        try:
            add_earned_days(
                conn, self._employee_id,
                data["earned_date"], data["number_of_days"], data["reason_notes"],
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load()
        self._refresh()

    def refresh(self):
        if self._employee_id:
            self._load()
