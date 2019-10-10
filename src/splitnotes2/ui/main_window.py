import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from PySide2 import QtCore
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMenu

from .layouts import Ui_MainWindow
from ..note_parser import Notes

user_path = os.path.expanduser("~/Documents")
template_path = Path(__file__).parent / 'html'
default_template = 'default.html'
default_css = 'default.css'
default_font_size = 20


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.statusbar.showMessage("Not connected to server")

        self.notes = None
        self.rc_menu = None

        self.j2_environment = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=False  # select_autoescape(['html'])
        )
        self.template = None
        self.css = ''
        self.font_size = default_font_size

        self.load_template()
        self.load_css()

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

    def load_template(self, template=default_template):
        self.template = self.j2_environment.get_template(template)

    def load_css(self, css_file=default_css):
        self.css = (Path(template_path) / css_file).read_text()

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

            html = self.template.render(
                font_size=self.font_size,
                css=self.css,
                notes=self.notes.render_splits(0, 3)
            )

            self.ui.notes.setHtml(html)

    def open_settings(self):
        print("This will open settings")
