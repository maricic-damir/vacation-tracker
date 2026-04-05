"""Screen 2: Employee details, balance summary, used days table, earned days table, actions."""
from datetime import date

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QTextDocument
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

from ui.dialogs import (
    ScheduleVacationDialog,
    AddEarnedDaysDialog,
    ContractDialog,
    SetTransferredDaysDialog,
    warn_past_start_date,
)
from translations import tr


# Details + Year balance form rows — one shared label column width.
_FORM_ROW_LABELS = (
    "JMBG:",
    "First name:",
    "Last name:",
    "Contract start date:",
    "Contract end date:",
    "Status:",
    "Days at start:",
    "Transferred:",
    "Earned:",
    "Used:",
    "Left:",
)


def _form_label_column_width(font) -> int:
    fm = QFontMetrics(font)
    w = max(fm.horizontalAdvance(s) for s in _FORM_ROW_LABELS)
    return w + 12


def _form_row_label(text: str, column_width: int) -> QLabel:
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    lab.setFixedWidth(column_width)
    return lab


def _configure_form_columns(form: QFormLayout) -> None:
    """Two-column layout: labels and values aligned as distinct columns."""
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(16)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)


def _configure_balance_form(form: QFormLayout) -> None:
    """Year panel: tighter gap label→value; values stay compact (not stretched across the group)."""
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(30)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)


def _form_value_label(
    text: str,
    *,
    align_right: bool = False,
    word_wrap: bool = False,
    expand_field: bool = False,
) -> QLabel:
    lab = QLabel(text)
    h = Qt.AlignmentFlag.AlignRight if align_right else Qt.AlignmentFlag.AlignLeft
    v = Qt.AlignmentFlag.AlignTop if word_wrap else Qt.AlignmentFlag.AlignVCenter
    lab.setAlignment(h | v)
    lab.setWordWrap(word_wrap)
    if word_wrap or expand_field:
        # Fill the form value column so rows share the same width and wrapping works.
        lab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return lab


def _balance_numeric_label(text: str, value_column_width: int) -> QLabel:
    """Fixed-width value column so digits line up vertically, flush right."""
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    lab.setFixedWidth(value_column_width)
    lab.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    lab.setStyleSheet("padding: 4px 12px;")
    return lab


def _balance_transferred_field(value_column_width: int) -> tuple[QWidget, QLabel, QLabel]:
    """Same width as other balance values; number + optional note stacked and right-aligned."""
    wrap = QWidget()
    wrap.setFixedWidth(value_column_width)
    wrap.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    v = QVBoxLayout(wrap)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)
    num = QLabel("—")
    num.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    num.setFixedWidth(value_column_width)
    num.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    num.setStyleSheet("padding: 4px 12px;")
    note = QLabel("")
    note.setWordWrap(True)
    note.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
    note.setFixedWidth(value_column_width)
    note.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    note.setStyleSheet("padding: 2px 12px; font-size: 9pt;")
    note.hide()
    v.addWidget(num)
    v.addWidget(note)
    return wrap, num, note


def _table_item(text: str, h_align: Qt.AlignmentFlag) -> QTableWidgetItem:
    it = QTableWidgetItem(str(text))
    it.setTextAlignment(int(h_align | Qt.AlignmentFlag.AlignVCenter))
    return it


class EmployeeDetailScreen(QWidget):
    def __init__(self, conn_getter, refresh_callback, on_back):
        super().__init__()
        self._conn = conn_getter
        self._refresh = refresh_callback
        self._on_back = on_back
        self._employee_id = None
        lay = QVBoxLayout(self)

        # Header: employee name + back
        header = QHBoxLayout()
        self._employee_title = QLabel("")
        self._employee_title.setWordWrap(False)
        header.addWidget(self._employee_title, 1)
        self._btn_back = QPushButton()
        self._btn_back.clicked.connect(lambda: on_back() if on_back else None)
        header.addWidget(self._btn_back, 0)
        lay.addLayout(header)

        # Details (left) + current-year balance (right)
        details_row = QHBoxLayout()
        self._props_group = QGroupBox("Details")
        self._props_layout = QFormLayout(self._props_group)
        _configure_form_columns(self._props_layout)
        details_row.addWidget(self._props_group, 1, Qt.AlignmentFlag.AlignTop)

        self._balance_group = QGroupBox("")
        self._balance_form = QFormLayout(self._balance_group)
        _configure_balance_form(self._balance_form)
        fm = QFontMetrics(self.font())
        bal_val_w = fm.horizontalAdvance("888 (888 left)") + 60
        self._bal_days_start = _balance_numeric_label("—", bal_val_w)
        transferred_wrap, self._bal_transferred_num, self._bal_transferred_note = _balance_transferred_field(
            bal_val_w
        )
        self._bal_earned = _balance_numeric_label("—", bal_val_w)
        self._bal_used = _balance_numeric_label("—", bal_val_w)
        self._bal_left = _balance_numeric_label("—", bal_val_w)
        lw = _form_label_column_width(self.font())
        self._form_label_w = lw
        self._balance_form.addRow(_form_row_label("Days at start:", lw), self._bal_days_start)
        self._balance_form.addRow(_form_row_label("Transferred:", lw), transferred_wrap)
        self._balance_form.addRow(_form_row_label("Earned:", lw), self._bal_earned)
        self._balance_form.addRow(_form_row_label("Used:", lw), self._bal_used)
        self._balance_form.addRow(_form_row_label("Left:", lw), self._bal_left)
        details_row.addWidget(self._balance_group, 1, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(details_row)

        # Used days off table
        self._used_group = QGroupBox()
        self._used_table = QTableWidget()
        self._used_table.setColumnCount(4)
        used_layout = QVBoxLayout(self._used_group)
        used_layout.addWidget(self._used_table)
        lay.addWidget(self._used_group)

        # Earned days table
        self._earned_group = QGroupBox()
        self._earned_table = QTableWidget()
        self._earned_table.setColumnCount(4)
        self._earned_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        earned_layout = QVBoxLayout(self._earned_group)
        earned_layout.addWidget(self._earned_table)
        lay.addWidget(self._earned_group)

        # First row buttons: Schedule vacation and Special leave entitlements
        first_row_lay = QHBoxLayout()
        self._btn_schedule = QPushButton()
        self._btn_schedule.clicked.connect(self._schedule_vacation)
        first_row_lay.addWidget(self._btn_schedule)
        self._btn_special_leaves = QPushButton()
        self._btn_special_leaves.clicked.connect(self._schedule_special_leave)
        first_row_lay.addWidget(self._btn_special_leaves)
        first_row_lay.addStretch()
        lay.addLayout(first_row_lay)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("margin: 10px 0px;")
        lay.addWidget(divider)
        
        # Label for configuration buttons
        self._config_label = QLabel()
        self._config_label.setStyleSheet("font-weight: bold;")
        lay.addWidget(self._config_label)

        # Second row buttons: Contract, Transferred days, Earned days (left), Print (right)
        second_row_lay = QHBoxLayout()
        self._btn_contract = QPushButton()
        self._btn_contract.clicked.connect(self._edit_contract)
        second_row_lay.addWidget(self._btn_contract)
        self._btn_transferred = QPushButton()
        self._btn_transferred.clicked.connect(self._set_transferred_days)
        second_row_lay.addWidget(self._btn_transferred)
        self._btn_earned = QPushButton()
        self._btn_earned.clicked.connect(self._add_earned_days)
        second_row_lay.addWidget(self._btn_earned)
        second_row_lay.addStretch()  # This pushes the print button to the right
        self._btn_print = QPushButton()
        self._btn_print.clicked.connect(self._print_employee)
        self._btn_print.setMinimumSize(120, 32)  # Make print button bigger and more visible
        second_row_lay.addWidget(self._btn_print)
        lay.addLayout(second_row_lay)

    def set_employee(self, employee_id: int):
        self._employee_id = employee_id
        self._load()
    
    def _update_ui_text(self):
        """Update all UI text with translations."""
        self._btn_back.setText(tr("back_to_list"))
        self._props_group.setTitle(tr("details"))
        self._used_group.setTitle(tr("used_days_off"))
        self._earned_group.setTitle(tr("earned_days"))
        self._btn_contract.setText(tr("contract_date_type"))
        self._btn_transferred.setText(tr("set_transferred_days"))
        self._btn_schedule.setText(tr("schedule_vacation"))
        self._btn_special_leaves.setText(tr("special_leaves"))
        self._btn_earned.setText(tr("add_earned_days"))
        self._btn_print.setText(tr("print"))
        
        # Configuration section label
        if tr("language") == "Language":  # English
            self._config_label.setText("Configuration:")
        else:  # Serbian
            self._config_label.setText("Конфигурација:")
        
        # Update table headers
        self._used_table.setHorizontalHeaderLabels([
            tr("booking_date"), tr("start"), tr("end"), tr("days")
        ])
        self._earned_table.setHorizontalHeaderLabels([
            tr("date_earned"), tr("days"), tr("reason_notes"), tr("created")
        ])

    def _load(self):
        conn = self._conn()
        if not conn or not self._employee_id:
            return
        from db_helpers import get_employee, get_year_balance, list_vacation_records_employee, list_earned_days
        from database import ensure_year_balance

        # Update UI text
        self._update_ui_text()

        emp = get_employee(conn, self._employee_id)
        if not emp:
            return
        full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        self._employee_title.setText(full_name)

        year = date.today().year
        ensure_year_balance(conn, self._employee_id, year, emp["contract_type"])
        balance = get_year_balance(conn, self._employee_id, year)

        # Clear and fill props
        while self._props_layout.rowCount():
            self._props_layout.removeRow(0)
        lw = self._form_label_w
        self._props_layout.addRow(
            _form_row_label(tr("jmbg") + ":", lw), _form_value_label(emp.get("jmbg", ""), expand_field=True)
        )
        self._props_layout.addRow(
            _form_row_label(tr("first_name") + ":", lw), _form_value_label(emp.get("first_name", ""), expand_field=True)
        )
        self._props_layout.addRow(
            _form_row_label(tr("last_name") + ":", lw), _form_value_label(emp.get("last_name", ""), expand_field=True)
        )
        
        # Contract start date
        start_date = emp.get("start_contract_date", "")
        self._props_layout.addRow(
            _form_row_label(tr("contract_start_date") + ":", lw), 
            _form_value_label(start_date if start_date else "-", expand_field=True)
        )
        
        # Contract end date
        ct = tr("fixed_term") if emp.get("contract_type") == "fixed_term" else tr("open_ended")
        if emp.get("contract_end_date"):
            ct += f" ({tr('until')} {emp['contract_end_date']})"
        self._props_layout.addRow(
            _form_row_label(tr("contract_end_date") + ":", lw), _form_value_label(ct, word_wrap=True, expand_field=True)
        )
        
        self._props_layout.addRow(
            _form_row_label(tr("status") + ":", lw),
            _form_value_label(tr("active") if emp.get("is_active") else tr("archived"), expand_field=True),
        )
        
        # Working days per week
        working_days = emp.get("working_days_per_week", 6)
        if tr("language") == "Language":  # English
            working_days_text = f"{working_days} days per week" + (" (Mon-Fri)" if working_days == 5 else "")
        else:  # Serbian
            working_days_text = f"{working_days} дана недељно" + (" (пон-пет)" if working_days == 5 else "")
        self._props_layout.addRow(
            _form_row_label(tr("working_days_per_week") + ":", lw),
            _form_value_label(working_days_text, expand_field=True),
        )

        # Balance (right column; title shows year)
        self._balance_group.setTitle(f"{tr('year')} {year}")
        self._bal_days_start.setText(f"{balance['days_at_start']} ({balance['at_start_left']} {tr('left')})")
        self._bal_transferred_num.setText(f"{balance['days_transferred']} ({balance['transferred_left']} {tr('left')})")
        # Show note if transferred days have expired (after December 31 of their year)
        today = date.today()
        if today > date(year, 12, 31):
            self._bal_transferred_note.setText(tr("transferred_note"))
            self._bal_transferred_note.show()
        else:
            self._bal_transferred_note.clear()
            self._bal_transferred_note.hide()
        self._bal_earned.setText(f"{balance['days_earned']} ({balance['earned_left']} {tr('left')})")
        self._bal_used.setText(str(balance["days_used"]))
        self._bal_left.setText(str(balance["days_left"]))

        # Used days
        records = list_vacation_records_employee(conn, self._employee_id)
        from db_helpers import count_days_in_range
        self._used_table.setRowCount(len(records))
        for i, r in enumerate(records):
            self._used_table.setItem(i, 0, _table_item(r.get("booking_date", ""), Qt.AlignmentFlag.AlignLeft))
            self._used_table.setItem(i, 1, _table_item(r.get("start_date", ""), Qt.AlignmentFlag.AlignLeft))
            self._used_table.setItem(i, 2, _table_item(r.get("end_date", ""), Qt.AlignmentFlag.AlignLeft))
            days = count_days_in_range(r["start_date"], r["end_date"])
            self._used_table.setItem(i, 3, _table_item(days, Qt.AlignmentFlag.AlignRight))
        self._used_table.resizeRowsToContents()

        # Earned days
        earned = list_earned_days(conn, self._employee_id)
        self._earned_table.setRowCount(len(earned))
        for i, r in enumerate(earned):
            self._earned_table.setItem(i, 0, _table_item(r.get("earned_date", ""), Qt.AlignmentFlag.AlignLeft))
            self._earned_table.setItem(i, 1, _table_item(r.get("number_of_days", ""), Qt.AlignmentFlag.AlignRight))
            self._earned_table.setItem(i, 2, _table_item(r.get("reason_notes", ""), Qt.AlignmentFlag.AlignLeft))
            self._earned_table.setItem(i, 3, _table_item(str(r.get("created_at", ""))[:10], Qt.AlignmentFlag.AlignLeft))
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
            current_religion=emp.get("religion", "orthodox"),
            current_working_days_per_week=emp.get("working_days_per_week", 6),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        try:
            update_employee_contract(conn, self._employee_id, data["contract_type"], data["contract_end_date"], data["religion"], data["working_days_per_week"])
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
        from db_helpers import (get_employee, add_vacation_record, count_working_days_in_range,
                                 count_total_deductible_days, get_available_days_for_deduction, 
                                 calculate_deduction_breakdown)
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
            QMessageBox.warning(self, tr("invalid_dates"), tr("start_before_end"))
            return
        if start < date.today() and not warn_past_start_date(self, start):
            return
        is_completed = end < date.today()
        
        year = start.year
        days_needed = count_total_deductible_days(conn, data["start_date"], data["end_date"], self._employee_id)
        available = get_available_days_for_deduction(conn, self._employee_id, year)
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
                conn, self._employee_id,
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
            QMessageBox.critical(self, tr("error"), str(e))
            return
        self._load()
        self._refresh()

    def _schedule_special_leave(self):
        """Open the special leave dialog for this employee."""
        if not self._employee_id:
            return
        conn = self._conn()
        if not conn:
            return
        from db_helpers import get_employee
        from ui.dialogs import SpecialLeaveDialog
        
        emp = get_employee(conn, self._employee_id)
        if not emp:
            return
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        
        dialog = SpecialLeaveDialog(self, conn, self._employee_id, emp_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load()  # Refresh the screen to show any changes
            self._refresh()  # Refresh the parent screen as well

    def refresh(self):
        if self._employee_id:
            self._load()

    def _print_employee(self):
        """Print employee details with the same layout as displayed on screen."""
        if not self._employee_id:
            return
        
        conn = self._conn()
        if not conn:
            return
        
        from db_helpers import get_employee, get_year_balance, list_vacation_records_employee, list_earned_days, count_days_in_range
        from database import ensure_year_balance
        
        emp = get_employee(conn, self._employee_id)
        if not emp:
            return
        
        year = date.today().year
        ensure_year_balance(conn, self._employee_id, year, emp["contract_type"])
        balance = get_year_balance(conn, self._employee_id, year)
        
        full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 9pt; }}
                h1 {{ font-size: 13.5pt; margin-bottom: 20px; }}
                h2 {{ font-size: 10.5pt; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #ccc; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 9pt; }}
                th {{ background-color: #f0f0f0; text-align: left; padding: 8px; border: 1px solid #ddd; font-weight: bold; }}
                td {{ padding: 8px; border: 1px solid #ddd; }}
                .right-align {{ text-align: right; }}
                .label-cell {{ font-weight: bold; width: 150px; }}
                .top-table {{ width: 100%; margin-bottom: 30px; }}
                .gap-cell {{ width: 30px; border: none; background: none; }}
            </style>
        </head>
        <body>
            <h1>{full_name}</h1>
            
            <table class="top-table">
                <tr>
                    <th colspan="2">{tr('details')}</th>
                    <td class="gap-cell"></td>
                    <th colspan="2">{tr('year')} {year}</th>
                </tr>
                <tr>
                    <td class="label-cell">{tr('jmbg')}:</td>
                    <td>{emp.get('jmbg', '')}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell">{tr('days_at_start')}:</td>
                    <td>{balance['days_at_start']} ({balance['at_start_left']} {tr('left')})</td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('first_name')}:</td>
                    <td>{emp.get('first_name', '')}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell">{tr('transferred')}:</td>
                    <td>{balance['days_transferred']} ({balance['transferred_left']} {tr('left')})</td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('last_name')}:</td>
                    <td>{emp.get('last_name', '')}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell">{tr('earned')}:</td>
                    <td>{balance['days_earned']} ({balance['earned_left']} {tr('left')})</td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('contract_start_date')}:</td>
                    <td>{emp.get('start_contract_date', '') or '-'}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell">{tr('used')}:</td>
                    <td>{balance['days_used']}</td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('contract_end_date')}:</td>
                    <td>{tr('fixed_term') if emp.get('contract_type') == 'fixed_term' else tr('open_ended')}{f" ({tr('until')} {emp['contract_end_date']})" if emp.get('contract_end_date') else ''}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell">{tr('left')}:</td>
                    <td>{balance['days_left']}</td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('status')}:</td>
                    <td>{tr('active') if emp.get('is_active') else tr('archived')}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell"></td>
                    <td></td>
                </tr>
                <tr>
                    <td class="label-cell">{tr('working_days_per_week')}:</td>
                    <td>{emp.get('working_days_per_week', 6)} {'days per week' if tr('language') == 'Language' else 'дана недељно'}{' (Mon-Fri)' if emp.get('working_days_per_week', 6) == 5 and tr('language') == 'Language' else ' (пон-пет)' if emp.get('working_days_per_week', 6) == 5 else ''}</td>
                    <td class="gap-cell"></td>
                    <td class="label-cell"></td>
                    <td></td>
                </tr>
            </table>
            
            <h2>{tr('used_days_off')}</h2>
            <table>
                <thead>
                    <tr>
                        <th>{tr('booking_date')}</th>
                        <th>{tr('start')}</th>
                        <th>{tr('end')}</th>
                        <th class="right-align">{tr('days')}</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        records = list_vacation_records_employee(conn, self._employee_id)
        for r in records:
            days = count_days_in_range(r["start_date"], r["end_date"])
            html += f"""
                    <tr>
                        <td>{r.get('booking_date', '')}</td>
                        <td>{r.get('start_date', '')}</td>
                        <td>{r.get('end_date', '')}</td>
                        <td class="right-align">{days}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <h2>{}</h2>
            <table>
                <thead>
                    <tr>
                        <th>{}</th>
                        <th class="right-align">{}</th>
                        <th>{}</th>
                        <th>{}</th>
                    </tr>
                </thead>
                <tbody>
        """.format(tr('earned_days'), tr('date_earned'), tr('days'), tr('reason_notes'), tr('created'))
        
        earned = list_earned_days(conn, self._employee_id)
        for r in earned:
            html += f"""
                    <tr>
                        <td>{r.get('earned_date', '')}</td>
                        <td class="right-align">{r.get('number_of_days', '')}</td>
                        <td>{r.get('reason_notes', '')}</td>
                        <td>{str(r.get('created_at', ''))[:10]}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            document = QTextDocument()
            document.setHtml(html)
            document.print(printer)
