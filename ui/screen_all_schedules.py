"""Screen 3: Table of all scheduled and used vacation/day-off records."""
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


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
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(self._table)
        btn_back = QPushButton("← Back to employee list")
        btn_back.clicked.connect(lambda: on_back() if on_back else None)
        f = QFont(btn_back.font())
        f.setPointSizeF(max(8.5, f.pointSizeF() - 1.0))
        btn_back.setFont(f)
        btn_back.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        # Comfortable inset between the frame and the caption (Qt Style Sheets: `padding`).
        btn_back.setStyleSheet(
            "QPushButton { margin: 0px; padding: 10px 14px; min-width: 0px; min-height: 0px; }"
        )
        back_row = QHBoxLayout()
        back_row.addStretch(1)
        back_row.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignHCenter)
        back_row.addStretch(1)
        lay.addLayout(back_row)

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from db_helpers import list_vacation_records_all
        rows = list_vacation_records_all(conn)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for col, key in enumerate(
                ("jmbg", "first_name", "last_name", "booking_date", "start_date", "end_date")
            ):
                it = QTableWidgetItem(str(r.get(key, "")))
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(i, col, it)
        self._table.resizeRowsToContents()
