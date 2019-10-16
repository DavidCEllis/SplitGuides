import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader
from PySide2 import QtCore
from PySide2.QtGui import QCursor, QIcon
from PySide2.QtWidgets import QMainWindow, QFileDialog, QMenu

from .settings import Settings, SettingsDialog
from .layouts import Ui_MainWindow
from ..note_parser import Notes
from ..livesplit_client import get_client


if getattr(sys, "frozen", False):
    base_path = Path(sys.executable).parent
    icon_file = str(base_path / "logo_alpha.png")
else:
    base_path = Path(__file__).parent
    icon_file = str(base_path.parents[2] / "resources" / "logo_alpha.png")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.icon = QIcon(icon_file)
        self.setWindowIcon(self.icon)

        self.ui.statusbar.showMessage("Not connected to server")

        # Get settings
        self.settings = Settings()

        # Window size
        self.resize(self.settings.width, self.settings.height)

        # Always on Top
        self.menu_on_top = None
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self.settings.on_top)

        self.notefile = None
        self.notes = None

        self.rc_menu = None

        self.j2_environment = Environment(
            loader=FileSystemLoader(str(self.settings.html_template_folder)),
            autoescape=False,
        )
        self.template = None
        self.css = ""
        self.load_template()
        self.load_css()

        self.build_menu()
        self.setup_actions()

        self.render_blank()

        self.client = get_client(self.settings.hostname, self.settings.port)

        self.ls = LivesplitLink(self.client, self)
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
            str(self.settings.html_template_file)
        )

    def load_css(self):
        self.css = self.settings.full_css_path.read_text()

    def show_menu(self):
        if not self.rc_menu:
            self.build_menu()
        self.rc_menu.popup(QCursor.pos())

    def open_notes(self):
        notefile, _ = QFileDialog.getOpenFileName(
            self,
            "Open Notes",
            self.settings.notes_folder,
            "Note Files (*.txt *.md);;All Files (*.*)",
        )

        if notefile:
            self.notefile = notefile
            # Reset split index and load notes
            self.notes = Notes.from_file(
                notefile, separator=self.settings.split_separator
            )
            self.settings.notes_folder = str(Path(notefile).parent)
            self.update_notes(idx=0, refresh=True)

    def render_blank(self):
        html = self.template.render(
            font_size=self.settings.font_size,
            font_color=self.settings.font_color,
            bg_color=self.settings.background_color,
            css=self.css,
            notes=["<h1>Right Click to Load Notes</h1>"],
        )
        self.ui.notes.setHtml(html)

    def update_notes(self, idx, refresh=False):
        idx = max(idx, 0)

        if self.notes and idx != self.split_index or refresh:
            start = idx - self.settings.previous_splits
            end = idx + self.settings.next_splits + 1

            html = self.template.render(
                font_size=self.settings.font_size,
                font_color=self.settings.font_color,
                bg_color=self.settings.background_color,
                css=self.css,
                notes=self.notes.render_splits(start, end),
            )

            self.ui.notes.setHtml(html)
            self.split_index = idx

    def open_settings(self):
        settings_dialog = SettingsDialog(parent=self, settings=self.settings)
        settings_dialog.setWindowIcon(self.icon)
        settings_dialog.exec_()
        if settings_dialog.result() == 1:
            settings_dialog.store_settings()
            # Kill and restart connection if server ip or port change
            if (
                self.client.connection.server != self.settings.hostname
                or self.client.connection.port != self.settings.port
            ):
                self.ls.close()
                self.client = get_client(self.settings.hostname, self.settings.port)
                self.ls = LivesplitLink(self.client, self)
                self.ls.start_loops()

            # Reread notes with separator
            if self.notefile:
                self.notes = Notes.from_file(
                    self.notefile, separator=self.settings.split_separator
                )
                self.update_notes(self.split_index, refresh=True)


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
