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
from translations import tr


class EmployeeListScreen(QWidget):
    def __init__(self, conn_getter, on_row_clicked, refresh_callback):
        super().__init__()
        self._conn = conn_getter
        self._on_row_clicked = on_row_clicked
        self._refresh = refresh_callback
        lay = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._update_table_headers()
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        
        # Enable word wrap for cells
        self._table.setWordWrap(True)
        
        # Auto-resize rows to fit content
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Add cell padding for better readability
        self._table.setStyleSheet("""
            QTableWidget::item {
                padding: 8px;
            }
        """)
        
        lay.addWidget(self._table)

        self._selection_label = QLabel()
        self._selection_label.setWordWrap(True)
        self._table.itemSelectionChanged.connect(self._update_selection_hint)
        lay.addWidget(self._selection_label)

        btn_lay = QHBoxLayout()
        self._btn_add = QPushButton()
        self._btn_add.clicked.connect(self._add_employee)
        btn_lay.addWidget(self._btn_add)
        self._btn_schedule = QPushButton()
        self._btn_schedule.clicked.connect(self._schedule_vacation_from_list)
        btn_lay.addWidget(self._btn_schedule)
        self._btn_all_schedules = QPushButton()
        self._btn_all_schedules.clicked.connect(self._go_to_all_schedules)
        btn_lay.addWidget(self._btn_all_schedules)
        self._btn_rollover = QPushButton()
        self._btn_rollover.clicked.connect(self._rollover_year)
        btn_lay.addWidget(self._btn_rollover)
        self._btn_holidays = QPushButton()
        self._btn_holidays.clicked.connect(self._manage_holidays)
        btn_lay.addWidget(self._btn_holidays)
        btn_lay.addStretch()
        lay.addLayout(btn_lay)
        self._go_to_all_schedules_callback = None
        self._update_button_text()
        self._update_selection_hint()
    
    def _update_table_headers(self):
        """Update table headers with translated text."""
        self._table.setHorizontalHeaderLabels([
            tr("jmbg"),
            tr("first_name"),
            tr("last_name"),
            tr("contract_start_date"),
            tr("contract_end_date"),
            tr("days_left")
        ])
    
    def _update_button_text(self):
        """Update button text with translations."""
        self._btn_add.setText(tr("add_employee"))
        self._btn_schedule.setText(tr("schedule_vacation"))
        self._btn_all_schedules.setText(tr("all_schedules"))
        self._btn_holidays.setText(tr("holidays_settings"))

    def set_go_to_all_schedules(self, callback):
        self._go_to_all_schedules_callback = callback
    
    def get_optimal_table_width(self):
        """Calculate the optimal width needed to display all columns without wrapping."""
        total_width = 0
        for i in range(self._table.columnCount()):
            total_width += self._table.columnWidth(i)
        # Add vertical header width and some padding
        total_width += self._table.verticalHeader().width() + 40
        return total_width

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
            if tr("language") == "Language":  # English
                self._selection_label.setText(
                    'No employee selected. Click a row in the table, then use "Schedule vacation / day off".'
                )
            else:  # Serbian
                self._selection_label.setText(
                    'Запослени није изабран. Кликните ред у табели, затим користите "Закажи годишњи / одсуство".'
                )
            return
        row = sel[0].row()
        jmbg_item = self._table.item(row, 0)
        first_item = self._table.item(row, 1)
        last_item = self._table.item(row, 2)
        if not jmbg_item or not first_item or not last_item:
            return
        self._selection_label.setForegroundRole(QPalette.ColorRole.WindowText)
        if tr("language") == "Language":  # English
            self._selection_label.setText(
                f"Scheduling will use: {first_item.text()} {last_item.text()} (JMBG {jmbg_item.text()})"
            )
        else:  # Serbian
            self._selection_label.setText(
                f"Закаживање ће користити: {first_item.text()} {last_item.text()} (ЈМБГ {jmbg_item.text()})"
            )

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from datetime import date
        from db_helpers import list_employees
        from database import is_rollover_complete

        # Update UI text
        self._update_table_headers()
        self._update_button_text()

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
            
            # Contract start date
            start_date = r.get("start_contract_date", "")
            self._table.setItem(i, 3, self._cell(start_date if start_date else "-"))
            
            # Contract end date with type
            ct = tr("fixed_term") if r.get("contract_type") == "fixed_term" else tr("open_ended")
            if r.get("contract_end_date"):
                ct += f" ({tr('until')} {r['contract_end_date']})"
            self._table.setItem(i, 4, self._cell(ct))
            
            self._table.setItem(i, 5, self._cell(str(r.get("total_vacation_left", 0))))
        if prev_eid is not None:
            for i, r in enumerate(rows):
                if r.get("id") == prev_eid:
                    self._table.selectRow(i)
                    break
        
        # Resize columns to fit content, then stretch to fill available width
        self._table.resizeColumnsToContents()
        
        self._update_selection_hint()
        
        current_year = date.today().year
        rollover_done = is_rollover_complete(conn, current_year)
        if tr("language") == "Language":  # English
            self._btn_rollover.setText(f"Roll over to {current_year}")
        else:  # Serbian
            self._btn_rollover.setText(f"Пренос на {current_year}")
        self._btn_rollover.setEnabled(not rollover_done)

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
                data["contract_type"], data["contract_end_date"], data["religion"],
                data["start_contract_date"],
            )
            ensure_year_balance(conn, eid, year, data["contract_type"])
            set_days_at_start(conn, eid, year, data["days_at_start"])
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))
            return
        self._refresh()

    def _schedule_vacation_from_list(self):
        sel = self._table.selectionModel().selectedRows()
        if not sel:
            if tr("language") == "Language":  # English
                QMessageBox.information(
                    self,
                    "Select employee",
                    "Click a row in the employee table to choose who to schedule, then try again. "
                    "You can also open an employee with double-click and schedule from their detail page.",
                )
            else:  # Serbian
                QMessageBox.information(
                    self,
                    "Изаберите запосленог",
                    "Кликните ред у табели запослених да бисте изабрали за кога да закажете, затим покушајте поново. "
                    "Такође можете отворити запосленог двокликом и заказати са њихове странице детаља.",
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
        from db_helpers import (add_vacation_record, count_working_days_in_range, 
                                 count_total_deductible_days, get_available_days_for_deduction, 
                                 calculate_deduction_breakdown)
        from database import ensure_year_balance, run_completion_job
        conn = self._conn()
        if not conn:
            return
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
        if start > end:
            QMessageBox.warning(self, tr("invalid_dates"), tr("start_before_end"))
            return
        is_past = start < date.today()
        if is_past and not warn_past_start_date(self, start):
            return
        is_completed = end < date.today()
        
        year = start.year
        days_needed = count_total_deductible_days(conn, data["start_date"], data["end_date"], employee_id)
        available = get_available_days_for_deduction(conn, employee_id, year)
        total_available = available['transferred'] + available['at_start'] + available['earned']
        
        if days_needed > total_available:
            if tr("language") == "Language":
                QMessageBox.warning(
                    self,
                    "Insufficient Days",
                    f"Cannot schedule vacation.\n\n"
                    f"Days needed: {days_needed}\n"
                    f"Days available: {total_available}\n\n"
                    f"Shortage: {days_needed - total_available} days"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Недовољно дана",
                    f"Не може се заказати одсуство.\n\n"
                    f"Потребно дана: {days_needed}\n"
                    f"Доступно дана: {total_available}\n\n"
                    f"Недостаје: {days_needed - total_available} дана"
                )
            return
        
        days_from_transferred = 0
        days_from_at_start = 0
        days_from_earned = 0
        
        if is_completed:
            breakdown = calculate_deduction_breakdown(
                days_needed,
                available['transferred'],
                available['at_start'],
                available['earned']
            )
            days_from_transferred = breakdown['transferred']
            days_from_at_start = breakdown['at_start']
            days_from_earned = breakdown['earned']
        
        try:
            add_vacation_record(
                conn, employee_id,
                data["booking_date"], data["start_date"], data["end_date"],
                is_completed=is_completed,
                days_from_transferred=days_from_transferred,
                days_from_at_start=days_from_at_start,
                days_from_earned=days_from_earned,
            )
            run_completion_job(conn)
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))
            return
        self._refresh()

    def _rollover_year(self):
        from datetime import date
        from database import rollover_all_employees
        
        conn = self._conn()
        if not conn:
            return
        
        current_year = date.today().year
        previous_year = current_year - 1
        
        if tr("language") == "Language":  # English
            reply = QMessageBox.question(
                self,
                "Confirm Year Rollover",
                f"Roll over all active employees from {previous_year} to {current_year}?\n\n"
                f"This will:\n"
                f"- Transfer all unused days from {previous_year} to {current_year}\n"
                f"- Calculate new days at start for {current_year} based on contract end dates\n"
                f"- Process all active employees\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:  # Serbian
            reply = QMessageBox.question(
                self,
                "Потврдите пренос године",
                f"Пренети све активне запослене са {previous_year} на {current_year}?\n\n"
                f"Ово ће:\n"
                f"- Пренети све неискоришћене дане са {previous_year} на {current_year}\n"
                f"- Израчунати нове дане на почетку за {current_year} на основу датума истека уговора\n"
                f"- Обрадити све активне запослене\n\n"
                f"Ова акција се не може поништити.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            count = rollover_all_employees(conn, previous_year, current_year)
            if tr("language") == "Language":  # English
                QMessageBox.information(
                    self,
                    "Rollover Complete",
                    f"Successfully rolled over {count} employee(s) to {current_year}."
                )
            else:  # Serbian
                QMessageBox.information(
                    self,
                    "Пренос завршен",
                    f"Успешно пренето {count} запослени(х) на {current_year}."
                )
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))
            return
    
    def _manage_holidays(self):
        """Open the manage non-working days dialog."""
        from ui.dialogs import ManageNonWorkingDaysDialog
        
        conn = self._conn()
        if not conn:
            return
        
        dialog = ManageNonWorkingDaysDialog(self, conn)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh()
