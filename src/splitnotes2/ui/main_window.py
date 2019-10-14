import time
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader
from PySide2 import QtCore
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMenu

from .settings import Settings, SettingsDialog
from .layouts import Ui_MainWindow
from ..note_parser import Notes
from ..livesplit_client import get_client


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.statusbar.showMessage("Not connected to server")

        # Get settings
        self.settings = Settings()
        self.settings_dialog = SettingsDialog(self.settings)

        # Always on Top
        self.menu_on_top = None
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self.settings.on_top)

        self.notes = None

        self.rc_menu = None

        self.j2_environment = Environment(
            loader=FileSystemLoader(str(self.settings.template_path)),
            autoescape=False
        )
        self.template = None
        self.css = ''
        self.load_template()
        self.load_css()

        self.build_menu()
        self.setup_actions()

        self.ls = LivesplitLink(get_client(), self)
        self.split_index = 0

        self.start_loops()

    def toggle_on_top(self):
        self.settings.on_top = not self.settings.on_top
        self.menu_on_top.setChecked(self.settings.on_top)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self.settings.on_top)
        self.show()

    def start_loops(self):
        self.ls.start_loops()

    def closeEvent(self, event):
        self.settings.save()
        self.ls.close()
        event.accept()

    def resizeEvent(self, event):
        # Store the new width and height to keep it
        # between launches
        self.settings.width = self.width()
        self.settings.height = self.height()
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

        self.menu_on_top = self.rc_menu.addAction("Always on top")
        self.menu_on_top.setCheckable(True)
        self.menu_on_top.setChecked(self.settings.on_top)
        self.menu_on_top.triggered.connect(self.toggle_on_top)

    def load_template(self):
        self.template = self.j2_environment.get_template(
            str(self.settings.full_template_path)
        )

    def load_css(self):
        self.css = self.settings.full_css_path.read_text()

    def show_menu(self):
        if not self.rc_menu:
            self.build_menu()
        self.rc_menu.popup(QCursor.pos())

    def open_notes(self):
        notefile, _ = QFileDialog.getOpenFileName(self,
                                                  "Open Notes",
                                                  self.settings.notes_folder,
                                                  "Note Files (*.txt *.md);;All Files (*.*)")

        if notefile:
            self.notes = Notes.from_file(notefile)

        # Reset split index and load notes
        self.update_notes(idx=0, refresh=True)

    def update_notes(self, idx, refresh=False):
        idx = max(idx, 0)

        if self.notes and idx != self.split_index or refresh:
            start = idx - self.settings.previous_splits
            end = idx + self.settings.next_splits + 1

            html = self.template.render(
                font_size=self.settings.font_size,
                css=self.css,
                notes=self.notes.render_splits(start, end)
            )

            self.ui.notes.setHtml(html)
            self.split_index = idx

    def open_settings(self):
        self.settings_dialog.exec_()


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
        self.pool.submit(self.loop_update_split)

    def stop_loops(self):
        self.break_loop = True
        self.pool.shutdown(wait=False)

    def close(self):
        self.stop_loops()
        self.client.close()

    def update_status(self, message):
        self.main_window.ui.statusbar.showMessage(message)

    def ls_connect(self):
        self.update_status("Trying to connect to Livesplit.")
        self.connected = self.client.connect()
        if self.connected:
            self.update_status("Connected to Livesplit.")

    def loop_update_split(self):
        while not self.break_loop:
            # If not connected attempt to connect
            if self.connected:
                try:
                    split_index = self.client.get_split_index()
                except (ConnectionError, ConnectionAbortedError, TimeoutError):
                    self.connected = False
                    self.client.close()
                else:
                    # noinspection PyUnresolvedReferences
                    self.note_signal.emit(split_index)
            else:
                self.ls_connect()
            time.sleep(0.5)
