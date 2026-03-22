"""Main window: stacked screens, DB connection, startup DB path resolution."""
import sys
import sqlite3
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
)
from PyQt6.QtCore import Qt
from database import get_connection, resolve_db_path, run_completion_job
from ui.dialogs import choose_or_create_db_path, locate_db_path
from ui.screen_employees import EmployeeListScreen
from ui.screen_employee_detail import EmployeeDetailScreen
from ui.screen_all_schedules import AllSchedulesScreen
from translations import tr, set_language as set_app_language, get_language
import config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._db_path: Optional[str] = None
        self._conn: Optional[sqlite3.Connection] = None
        
        # Load saved language
        saved_lang = config.get_language()
        set_app_language(saved_lang)
        
        self.setWindowTitle(tr("app_title"))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Top bar with language selector
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        lang_label = QLabel(tr("language") + ":")
        top_bar.addWidget(lang_label)
        
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("English", "en")
        self._lang_combo.addItem("Српски", "sr")
        
        # Set current language
        idx = self._lang_combo.findData(saved_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        top_bar.addWidget(self._lang_combo)
        
        layout.addLayout(top_bar)
        
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Screens
        self._list_screen = EmployeeListScreen(
            conn_getter=self._get_conn,
            on_row_clicked=self._open_employee_detail,
            refresh_callback=self._refresh_current,
        )
        self._detail_screen = EmployeeDetailScreen(
            conn_getter=self._get_conn,
            refresh_callback=self._refresh_current,
            on_back=self._go_list,
        )
        self._all_schedules_screen = AllSchedulesScreen(
            conn_getter=self._get_conn,
            refresh_callback=self._refresh_current,
            on_back=self._go_list,
        )

        self._stack.addWidget(self._list_screen)
        self._stack.addWidget(self._detail_screen)
        self._stack.addWidget(self._all_schedules_screen)

        self._list_screen.set_go_to_all_schedules(self._go_all_schedules)

        self.resize(900, 600)

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        return self._conn
    
    def _on_language_changed(self):
        """Handle language change."""
        lang_code = self._lang_combo.currentData()
        if lang_code:
            set_app_language(lang_code)
            config.set_language(lang_code)
            self._refresh_ui()
    
    def _refresh_ui(self):
        """Refresh all UI text after language change."""
        self.setWindowTitle(tr("app_title"))
        # Refresh all screens
        self._list_screen.refresh()
        self._detail_screen.refresh()
        self._all_schedules_screen.refresh()

    def _refresh_current(self):
        idx = self._stack.currentIndex()
        if idx == 0:
            self._list_screen.refresh()
        elif idx == 1:
            self._detail_screen.refresh()
        elif idx == 2:
            self._all_schedules_screen.refresh()

    def _open_employee_detail(self, employee_id: int):
        self._detail_screen.set_employee(employee_id)
        self._stack.setCurrentWidget(self._detail_screen)

    def _go_list(self):
        self._list_screen.refresh()
        self._stack.setCurrentWidget(self._list_screen)

    def _go_all_schedules(self):
        self._all_schedules_screen.refresh()
        self._stack.setCurrentWidget(self._all_schedules_screen)

    def ensure_db(self) -> bool:
        """Resolve DB path (find or create). Open connection and run completion job. Return True if ready."""
        def choose():
            return choose_or_create_db_path(self)

        def locate():
            return locate_db_path(self)

        path = resolve_db_path(choose, locate)
        if not path:
            QMessageBox.information(
                self,
                tr("database_required"),
                tr("no_database_selected"),
            )
            return False
        self._db_path = path
        self._conn = get_connection(path)
        run_completion_job(self._conn)
        self._list_screen.refresh()
        return True

    def closeEvent(self, event):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        event.accept()


def run_app():
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = MainWindow()
    if not win.ensure_db():
        return 1
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
