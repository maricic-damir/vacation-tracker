"""Screen 3: Table of all scheduled and used vacation/day-off records."""
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
        self._all_rows = []
        
        lay = QVBoxLayout(self)
        
        # Add filter section with two rows
        # First row: First Name and Last Name
        first_row_layout = QHBoxLayout()
        
        # First Name filter
        self._first_name_filter_label = QLabel()
        self._first_name_filter = QLineEdit()
        self._first_name_filter.setPlaceholderText("Filter...")
        self._first_name_filter.textChanged.connect(self._apply_filters)
        first_row_layout.addWidget(self._first_name_filter_label)
        first_row_layout.addWidget(self._first_name_filter)
        
        # Last Name filter
        self._last_name_filter_label = QLabel()
        self._last_name_filter = QLineEdit()
        self._last_name_filter.setPlaceholderText("Filter...")
        self._last_name_filter.textChanged.connect(self._apply_filters)
        first_row_layout.addWidget(self._last_name_filter_label)
        first_row_layout.addWidget(self._last_name_filter)
        
        first_row_layout.addStretch()
        lay.addLayout(first_row_layout)
        
        # Second row: JMBG and Month/Year filter
        second_row_layout = QHBoxLayout()
        
        # JMBG filter
        self._jmbg_filter_label = QLabel()
        self._jmbg_filter = QLineEdit()
        self._jmbg_filter.setPlaceholderText("Filter...")
        self._jmbg_filter.textChanged.connect(self._apply_filters)
        second_row_layout.addWidget(self._jmbg_filter_label)
        second_row_layout.addWidget(self._jmbg_filter)
        
        # Month/Year filter
        self._month_year_filter_label = QLabel()
        self._month_year_filter = QComboBox()
        self._month_year_filter.currentTextChanged.connect(self._apply_filters)
        second_row_layout.addWidget(self._month_year_filter_label)
        second_row_layout.addWidget(self._month_year_filter)
        
        second_row_layout.addStretch()
        lay.addLayout(second_row_layout)
        
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
        
        # Update UI text
        self._btn_back.setText(tr("back_to_list"))
        self._first_name_filter_label.setText(tr("first_name") + ":")
        self._last_name_filter_label.setText(tr("last_name") + ":")
        self._jmbg_filter_label.setText(tr("jmbg") + ":")
        self._month_year_filter_label.setText(tr("month_year_filter") + ":")
        self._table.setHorizontalHeaderLabels([
            tr("jmbg"), tr("first_name"), tr("last_name"),
            tr("booking_date"), tr("start"), tr("end")
        ])
        
        # Store all rows for filtering
        self._all_rows = list_vacation_records_all(conn)
        
        # Populate month/year filter
        self._populate_month_year_filter()
        
        # Apply filters and populate table
        self._apply_filters()
        
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
    
    def _populate_month_year_filter(self):
        """Populate the month/year filter with available options based on vacation start dates."""
        from datetime import datetime
        
        # Clear existing items
        self._month_year_filter.clear()
        
        # Add "All months" option
        self._month_year_filter.addItem(tr("all_months"))
        
        # Extract unique month/year combinations from start dates
        month_years = set()
        for row in self._all_rows:
            start_date_str = row.get("start_date", "")
            if start_date_str:
                try:
                    # Parse date (assuming YYYY-MM-DD format)
                    date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                    month_year = f"{date_obj.year}-{date_obj.month:02d}"
                    month_years.add(month_year)
                except ValueError:
                    continue
        
        # Sort and add to combo box
        for month_year in sorted(month_years, reverse=True):
            year, month = month_year.split("-")
            # Format as "Month YYYY" (e.g., "January 2024")
            month_names = [
                tr("january"), tr("february"), tr("march"), tr("april"),
                tr("may"), tr("june"), tr("july"), tr("august"),
                tr("september"), tr("october"), tr("november"), tr("december")
            ]
            try:
                month_name = month_names[int(month) - 1] if int(month) <= 12 else month
                display_text = f"{month_name} {year}"
            except (ValueError, IndexError):
                display_text = month_year
            
            self._month_year_filter.addItem(display_text, month_year)
    
    def _apply_filters(self):
        from datetime import datetime
        
        # Get filter values
        jmbg_filter = self._jmbg_filter.text().lower()
        first_name_filter = self._first_name_filter.text().lower()
        last_name_filter = self._last_name_filter.text().lower()
        
        # Get selected month/year filter
        selected_month_year = None
        if self._month_year_filter.currentData():
            selected_month_year = self._month_year_filter.currentData()
        
        # Filter rows
        filtered_rows = []
        for r in self._all_rows:
            jmbg_match = jmbg_filter in str(r.get("jmbg", "")).lower()
            first_name_match = first_name_filter in str(r.get("first_name", "")).lower()
            last_name_match = last_name_filter in str(r.get("last_name", "")).lower()
            
            # Month/year filter
            month_year_match = True
            if selected_month_year:
                start_date_str = r.get("start_date", "")
                if start_date_str:
                    try:
                        date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                        row_month_year = f"{date_obj.year}-{date_obj.month:02d}"
                        month_year_match = (row_month_year == selected_month_year)
                    except ValueError:
                        month_year_match = False
                else:
                    month_year_match = False
            
            if jmbg_match and first_name_match and last_name_match and month_year_match:
                filtered_rows.append(r)
        
        # Temporarily disable sorting while populating the table
        self._table.setSortingEnabled(False)
        
        # Populate table with filtered rows
        self._table.setRowCount(len(filtered_rows))
        for i, r in enumerate(filtered_rows):
            for col, key in enumerate(
                ("jmbg", "first_name", "last_name", "booking_date", "start_date", "end_date")
            ):
                it = QTableWidgetItem(str(r.get(key, "")))
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(i, col, it)
        self._table.resizeRowsToContents()
    
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
