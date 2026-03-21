"""Screen 1: Employee list table + add employee + schedule vacation + link to Screen 3."""
from PyQt6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette

from ui.dialogs import AddEmployeeDialog, ScheduleVacationDialog


class EmployeeListScreen(QWidget):
    def __init__(self, conn_getter, on_row_clicked, refresh_callback):
        super().__init__()
        self._conn = conn_getter
        self._on_row_clicked = on_row_clicked
        self._refresh = refresh_callback
        lay = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["JMBG", "First name", "Last name", "Contract type", "Vacation days left"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        lay.addWidget(self._table)

        self._selection_label = QLabel()
        self._selection_label.setWordWrap(True)
        self._table.itemSelectionChanged.connect(self._update_selection_hint)
        lay.addWidget(self._selection_label)

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
        self._update_selection_hint()

    def set_go_to_all_schedules(self, callback):
        self._go_to_all_schedules_callback = callback

    def _go_to_all_schedules(self):
        if self._go_to_all_schedules_callback:
            self._go_to_all_schedules_callback()

    def _on_double_click(self, row: int, _col: int):
        eid = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if eid is not None and self._on_row_clicked:
            self._on_row_clicked(int(eid))

    def _update_selection_hint(self):
        sel = self._table.selectionModel().selectedRows()
        if not sel:
            self._selection_label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
            self._selection_label.setText(
                'No employee selected. Click a row in the table, then use "Schedule vacation / day off".'
            )
            return
        row = sel[0].row()
        jmbg_item = self._table.item(row, 0)
        first_item = self._table.item(row, 1)
        last_item = self._table.item(row, 2)
        if not jmbg_item or not first_item or not last_item:
            return
        self._selection_label.setForegroundRole(QPalette.ColorRole.WindowText)
        self._selection_label.setText(
            f"Scheduling will use: {first_item.text()} {last_item.text()} (JMBG {jmbg_item.text()})"
        )

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from db_helpers import list_employees

        prev_eid = None
        for idx in self._table.selectionModel().selectedRows():
            it = self._table.item(idx.row(), 0)
            if it is not None:
                prev_eid = it.data(Qt.ItemDataRole.UserRole)
                break

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
            self._table.setItem(i, 4, self._cell(str(r.get("total_vacation_left", 0))))
        if prev_eid is not None:
            for i, r in enumerate(rows):
                if r.get("id") == prev_eid:
                    self._table.selectRow(i)
                    break
        self._table.resizeRowsToContents()
        self._update_selection_hint()

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
        sel = self._table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(
                self,
                "Select employee",
                "Click a row in the employee table to choose who to schedule, then try again. "
                "You can also open an employee with double-click and schedule from their detail page.",
            )
            return
        row = sel[0].row()
        id_item = self._table.item(row, 0)
        first_item = self._table.item(row, 1)
        last_item = self._table.item(row, 2)
        if id_item is None or first_item is None or last_item is None:
            return
        eid = id_item.data(Qt.ItemDataRole.UserRole)
        if eid is None:
            return
        emp_name = f"{first_item.text()} {last_item.text()}"
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
