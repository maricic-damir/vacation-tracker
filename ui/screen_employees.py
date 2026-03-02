"""Screen 1: Employee list table + add employee + schedule vacation + link to Screen 3."""
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt

from ui.dialogs import AddEmployeeDialog, ScheduleVacationDialog


class EmployeeListScreen(QWidget):
    def __init__(self, conn_getter, on_row_clicked, refresh_callback):
        super().__init__()
        self._conn = conn_getter
        self._on_row_clicked = on_row_clicked
        self._refresh = refresh_callback
        lay = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["JMBG", "First name", "Last name", "Contract type", "Active", "Vacation days left"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        lay.addWidget(self._table)

        btn_lay = QHBoxLayout()
        btn_add = QPushButton("Add employee")
        btn_add.clicked.connect(self._add_employee)
        btn_lay.addWidget(btn_add)
        btn_schedule = QPushButton("Schedule vacation / day off")
        btn_schedule.clicked.connect(self._schedule_vacation_from_list)
        btn_lay.addWidget(btn_schedule)
        btn_all_schedules = QPushButton("All scheduled / used days")
        btn_all_schedules.clicked.connect(self._go_to_all_schedules)
        btn_lay.addWidget(btn_all_schedules)
        btn_lay.addStretch()
        lay.addLayout(btn_lay)
        self._go_to_all_schedules_callback = None

    def set_go_to_all_schedules(self, callback):
        self._go_to_all_schedules_callback = callback

    def _go_to_all_schedules(self):
        if self._go_to_all_schedules_callback:
            self._go_to_all_schedules_callback()

    def _on_double_click(self, row: int, _col: int):
        eid = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if eid is not None and self._on_row_clicked:
            self._on_row_clicked(int(eid))

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from db_helpers import list_employees
        rows = list_employees(conn)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, self._cell(r.get("jmbg", ""), r.get("id")))
            self._table.setItem(i, 1, self._cell(r.get("first_name", "")))
            self._table.setItem(i, 2, self._cell(r.get("last_name", "")))
            ct = "Fixed term" if r.get("contract_type") == "fixed_term" else "Open-ended"
            if r.get("contract_end_date"):
                ct += f" (until {r['contract_end_date']})"
            self._table.setItem(i, 3, self._cell(ct))
            # Archive toggle (column 4)
            chk = QCheckBox()
            chk.setChecked(bool(r.get("is_active")))
            eid = r.get("id")
            chk.stateChanged.connect(lambda state, emp_id=eid: self._on_active_toggled(emp_id, state))
            self._table.setCellWidget(i, 4, chk)
            self._table.setItem(i, 5, self._cell(str(r.get("total_vacation_left", 0))))
        self._table.resizeRowsToContents()

    def _on_active_toggled(self, employee_id: int, state: int):
        conn = self._conn()
        if not conn:
            return
        is_checked = state == Qt.CheckState.Checked.value
        from db_helpers import set_employee_active
        try:
            set_employee_active(conn, int(employee_id), is_checked)
        except Exception as e:
            QMessageBox.critical(self, "Archive", str(e))
            return
        self._refresh()

    def _cell(self, text: str, user_data=None):
        it = QTableWidgetItem(str(text))
        if user_data is not None:
            it.setData(Qt.ItemDataRole.UserRole, user_data)
        return it

    def _add_employee(self):
        dlg = AddEmployeeDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        conn = self._conn()
        if not conn:
            return
        try:
            from datetime import date
            from db_helpers import insert_employee, set_days_at_start
            from database import ensure_year_balance
            year = date.today().year
            eid = insert_employee(
                conn, data["jmbg"], data["first_name"], data["last_name"],
                data["contract_type"], data["contract_end_date"],
            )
            ensure_year_balance(conn, eid, year, data["contract_type"])
            if data["contract_type"] == "fixed_term" and data.get("days_at_start", 0) > 0:
                set_days_at_start(conn, eid, year, data["days_at_start"])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._refresh()

    def _schedule_vacation_from_list(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select employee", "Select an employee row first, or go to employee details.")
            return
        eid = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if eid is None:
            return
        emp_name = f"{self._table.item(row, 1).text()} {self._table.item(row, 2).text()}"
        self._open_schedule_dialog(int(eid), emp_name)

    def _open_schedule_dialog(self, employee_id: int, employee_name: str):
        dlg = ScheduleVacationDialog(self, employee_name)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._save_vacation(employee_id, dlg.get_data())

    def _save_vacation(self, employee_id: int, data: dict):
        from datetime import date
        from ui.dialogs import warn_past_start_date
        from db_helpers import add_vacation_record, count_days_in_range
        from database import ensure_year_balance, run_completion_job
        conn = self._conn()
        if not conn:
            return
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
        if start > end:
            QMessageBox.warning(self, "Invalid dates", "Start date must be before or equal to end date.")
            return
        is_past = start < date.today()
        if is_past and not warn_past_start_date(self, start):
            return
        is_completed = end < date.today()
        try:
            add_vacation_record(
                conn, employee_id,
                data["booking_date"], data["start_date"], data["end_date"],
                is_completed=is_completed,
            )
            run_completion_job(conn)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self._refresh()
