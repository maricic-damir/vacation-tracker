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

from translations import tr


class AllSchedulesScreen(QWidget):
    def __init__(self, conn_getter, refresh_callback, on_back):
        super().__init__()
        self._conn = conn_getter
        self._refresh = refresh_callback
        self._on_back = on_back
        self._sorting_enabled = False
        self._sort_order = {}
        lay = QVBoxLayout(self)
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(False)
        lay.addWidget(self._table)
        self._btn_back = QPushButton()
        self._btn_back.clicked.connect(lambda: on_back() if on_back else None)
        f = QFont(self._btn_back.font())
        f.setPointSizeF(max(8.5, f.pointSizeF() - 1.0))
        self._btn_back.setFont(f)
        self._btn_back.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._btn_back.setStyleSheet(
            "QPushButton { margin: 0px; padding: 10px 14px; min-width: 0px; min-height: 0px; }"
        )
        back_row = QHBoxLayout()
        back_row.addStretch(1)
        back_row.addWidget(self._btn_back, 0, Qt.AlignmentFlag.AlignHCenter)
        back_row.addStretch(1)
        lay.addLayout(back_row)

    def refresh(self):
        conn = self._conn()
        if not conn:
            return
        from db_helpers import list_vacation_records_all
        
        # Temporarily disable sorting while populating the table
        self._table.setSortingEnabled(False)
        
        # Update UI text
        self._btn_back.setText(tr("back_to_list"))
        self._table.setHorizontalHeaderLabels([
            tr("jmbg"), tr("first_name"), tr("last_name"),
            tr("booking_date"), tr("start"), tr("end")
        ])
        
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
        
        # Set up custom header click handling
        header = self._table.horizontalHeader()
        header.setSectionsClickable(True)
        if self._sorting_enabled:
            try:
                header.sectionClicked.disconnect()
            except:
                pass
        header.sectionClicked.connect(self._on_header_clicked)
        self._sorting_enabled = True
    
    def _on_header_clicked(self, logical_index):
        # Only allow sorting on columns 0 (JMBG), 1 (first name), 2 (last name), 4 (start date)
        if logical_index not in (3, 5):
            # Toggle sort order for this column
            current_order = self._sort_order.get(logical_index, Qt.SortOrder.DescendingOrder)
            new_order = Qt.SortOrder.AscendingOrder if current_order == Qt.SortOrder.DescendingOrder else Qt.SortOrder.DescendingOrder
            self._sort_order[logical_index] = new_order
            
            # Perform the sort
            self._table.setSortingEnabled(True)
            self._table.sortItems(logical_index, new_order)
            self._table.setSortingEnabled(False)
