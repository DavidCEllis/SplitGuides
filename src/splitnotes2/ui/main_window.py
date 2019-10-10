import os

from PySide2 import QtCore
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMenu

from .layouts import Ui_MainWindow
from ..note_parser import Notes

user_path = os.path.expanduser("~")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.statusbar.showMessage("Not connected to server")

        self.notes = None
        self.rc_menu = None

        self.build_menu()
        self.setup_actions()

    def setup_actions(self):
        self.ui.notes.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.notes.customContextMenuRequested.connect(self.show_menu)

    def build_menu(self):
        self.rc_menu = QMenu()
        open_notes = self.rc_menu.addAction("Open Notes")
        open_notes.triggered.connect(self.open_notes)

        open_settings = self.rc_menu.addAction("Settings")
        open_settings.triggered.connect(self.open_settings)

    def show_menu(self):
        if not self.rc_menu:
            self.build_menu()
        self.rc_menu.popup(QCursor.pos())

    def open_notes(self):
        notefile, _ = QFileDialog.getOpenFileName(self,
                                                  "Open Notes",
                                                  user_path,  # Starting Directory
                                                  "Note Files (*.txt *.md);;All Files (*.*)")

        if notefile:
            self.notes = Notes.from_file(notefile)
            self.ui.notes.setHtml(self.notes.render_split(0))

    def open_settings(self):
        print("This will open settings")
