"""Screen 3: Table of all scheduled and used vacation/day-off records."""
from PyQt6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
)
from PyQt6.QtCore import Qt


class AllSchedulesScreen(QWidget):
    def __init__(self, conn_getter, refresh_callback, on_back):
        super().__init__()
        self._conn = conn_getter
        self._refresh = refresh_callback
        self._on_back = on_back
        lay = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["JMBG", "First name", "Last name", "Booking date", "Start date", "End date"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self._table)
        btn_back = QPushButton("Back to employee list")
        btn_back.clicked.connect(lambda: on_back() if on_back else None)
        lay.addWidget(btn_back)

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from db_helpers import list_vacation_records_all
        rows = list_vacation_records_all(conn)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(str(r.get("jmbg", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(str(r.get("first_name", ""))))
            self._table.setItem(i, 2, QTableWidgetItem(str(r.get("last_name", ""))))
            self._table.setItem(i, 3, QTableWidgetItem(str(r.get("booking_date", ""))))
            self._table.setItem(i, 4, QTableWidgetItem(str(r.get("start_date", ""))))
            self._table.setItem(i, 5, QTableWidgetItem(str(r.get("end_date", ""))))
        self._table.resizeRowsToContents()
