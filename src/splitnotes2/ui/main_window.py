import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader
from PySide2 import QtCore
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMenu, QMessageBox

from .layouts import Ui_MainWindow
from ..note_parser import Notes
from ..livesplit_client import get_client


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
            autoescape=False
        )
        self.template = None
        self.css = ''
        self.font_size = default_font_size
        self.load_template()
        self.load_css()

        self.build_menu()
        self.setup_actions()

        self.ls = LivesplitLink(get_client(), self)
        self.split_index = 0

        self.start_loops()

    def start_loops(self):
        self.ls.start_loops()
        print("Loops Started")

    def closeEvent(self, event):
        self.ls.close()
        event.accept()

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

        # Reset split index and load notes
        self.update_notes(idx=0, refresh=True)

    def update_notes(self, idx, refresh=False):
        idx = max(idx, 0)
        if self.notes and idx != self.split_index or refresh:
            html = self.template.render(
                font_size=self.font_size,
                css=self.css,
                notes=self.notes.render_splits(idx, idx + 3)
            )

            self.ui.notes.setHtml(html)
            self.split_index = idx

    def open_settings(self):
        msgbox = QMessageBox()
        msgbox.setText("Soon (TM)")
        msgbox.exec_()


class LivesplitLink(QtCore.QObject):
    """
    Handle the loop running the livesplit connection and linking to the main window
    """
    # Have to message via signals or the program crashes
    note_signal = QtCore.Signal(int)

    def __init__(self, client, main_window):
        super().__init__()
        self.client = client
        self.main_window = main_window  # type: MainWindow
        self.connected = False
        self.break_loop = False
        self.pool = None
        # noinspection PyUnresolvedReferences
        self.note_signal.connect(self.main_window.update_notes)

    def start_loops(self):
        self.break_loop = False
        self.pool = ThreadPoolExecutor(max_workers=1)
        if self.connected:
            self.pool.submit(self.loop_update_split)
        else:
            self.pool.submit(self.connect_and_update)

    def stop_loops(self):
        self.break_loop = True
        self.pool.shutdown(wait=False)

    def close(self):
        self.stop_loops()
        self.client.close()

    def update_status(self, message):
        self.main_window.ui.statusbar.showMessage(message)

    def connect_and_update(self):
        self.loop_connect()
        self.loop_update_split()

    def loop_connect(self):
        self.update_status("Trying to connect to Livesplit.")

        while not self.connected:
            if self.break_loop:
                break
            self.connected = self.client.connect()
        else:
            self.update_status("Connected to Livesplit.")

        if not self.connected:
            self.update_status("Not Connected to Livesplit.")

    def loop_update_split(self):
        if not self.connected:
            self.loop_connect()

        while (not self.break_loop) and self.connected:
            try:
                split_index = self.client.get_split_index()
            except (ConnectionAbortedError, TimeoutError):
                self.connected = False
                self.client.close()
                self.connect_and_update()
            else:
                # noinspection PyUnresolvedReferences
                self.note_signal.emit(split_index)
            time.sleep(1)
