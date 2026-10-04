import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from database.connection import DatabaseManager

class AppController:
    def __init__(self, db_path: str = None):
        self.db = DatabaseManager.get_instance(db_path)
        self.app = None
        self.window = None

    def run(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ControlPolicial")
        self.app.setOrganizationName("PNP")

        self.window = MainWindow()
        self.window.show()

        return self.app.exec()
