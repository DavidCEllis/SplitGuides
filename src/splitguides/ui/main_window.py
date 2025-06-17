import sys
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader, Template
from PySide6 import QtCore
from PySide6.QtGui import QColorConstants, QCursor, QIcon, QMouseEvent, QAction
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMenu, QErrorMessage

from .color import rgba_to_qss
from .custom_elements import ExtLinkWebEnginePage
from .hotkey_manager import HotkeyManager
from .layouts import Ui_MainWindow
from .settings_ui import SettingsDialog

from ..livesplit_client import get_client
from ..note_parser import Notes
from ..settings import DesktopSettings


# Get correct paths
if getattr(sys, "frozen", False):  # pragma: nocover
    # PyInstaller .exe
    base_path = Path(sys.executable).parent
    icon_file = str(base_path / "logo_alpha.png")
else:
    # Running locally
    base_path = Path(__file__).parent
    icon_file = str(base_path.parents[2] / "resources" / "logo_alpha.png")


IS_WINDOWS = sys.platform == "win32"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Setup the UI and get an icon
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.icon = QIcon(icon_file)
        self.setWindowIcon(self.icon)

        # Initial statusbar message
        self.ui.statusbar.showMessage("Not connected to server.")

        # Get settings
        self.settings = DesktopSettings.load()

        # Window size
        self.resize(self.settings.width, self.settings.height)

        # Always on Top
        self.menu_on_top: None | QAction = None
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, self.settings.on_top)

        # Transparency
        self.menu_transparency: None | QAction = None
        
        # WA_TranslucentBackground attribute required to enable transparency
        # QT Docs state "Toggling this attribute after the widget has been shown is not uniformly supported"
        # So this is only set once to True in __init__ unlike the other transparency settings
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.refresh_transparency()

        # Setup notes variables
        self.notefile: None | str = None
        self.notes: None | Notes = None

        # Right Click Menu
        self.rc_menu: None | QMenu = None
        self.hotkeys_toggle: None | QAction = None

        self.build_menu()
        self.setup_actions()

        self.j2_environment = Environment(
            loader=FileSystemLoader(self.settings.html_template_folder),
            autoescape=False,
        )

        self.template: None | Template = None
        self.load_template()

        self.css = ""
        self.load_css()

        self.render_blank()

        self.client = get_client(self.settings.hostname, self.settings.port)

        self.ls = LivesplitLink(self.client, self)
        self.split_index = 0

        self.split_offset = 0  # Offset for advancing/reversing split

        # Set up hotkey manager
        if IS_WINDOWS:
            self.hotkey_manager = HotkeyManager(self)

            if self.settings.hotkeys_enabled:
                try:
                    self.enable_hotkeys()
                except AttributeError:
                    QErrorMessage(parent=self).showMessage("Could not enable hotkeys.")
                    self.disable_hotkeys()
                    self.settings.hotkeys_enabled = False
                    self.hotkeys_toggle.setChecked(False)
        else:
            self.hotkey_manager = None

        self.start_loops()  # Start livesplit checking loops

    def toggle_on_top(self):
        """Toggle window always on top, update settings and window flag to match."""
        self.settings.on_top = not self.settings.on_top
        self.menu_on_top.setChecked(self.settings.on_top)
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, self.settings.on_top)
        self.show()

    def refresh_transparency(self):
        """
        Redo all of the transparency display configuration
        """
        qss_bg_color = rgba_to_qss(self.settings.background_color)
        qss_font_color = rgba_to_qss(self.settings.font_color)
        qss_style = (
            f"background-color: {qss_bg_color}; color: {qss_font_color}"
        )

        # Flags and attributes
        # Needs the FramelessWindowHint flag set for the translucency to work.
        self.setWindowFlag(
            QtCore.Qt.WindowType.FramelessWindowHint, 
            self.settings.transparency
        )
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, 
            self.settings.transparency
        )

        # Central widget always matches CSS style, statusbar only when transparent
        self.ui.centralWidget.setStyleSheet(qss_style)
        if self.settings.transparency:
            self.ui.statusbar.setStyleSheet(qss_style)
        else:
            self.ui.statusbar.setStyleSheet("")

    def toggle_transparency(self):
        """Toggle window transparency, update settings and window flag to match."""
        self.settings.transparency = not self.settings.transparency
        self.menu_transparency.setChecked(self.settings.transparency)
        self.refresh_transparency()
        self.show()

    def toggle_hotkey_enable(self):
        if IS_WINDOWS:
            try:
                if self.settings.hotkeys_enabled:
                    self.disable_hotkeys()
                    self.settings.hotkeys_enabled = False
                    self.hotkeys_toggle.setChecked(False)
                else:
                    self.enable_hotkeys()
                    self.settings.hotkeys_enabled = True
                    self.hotkeys_toggle.setChecked(True)
            except AttributeError:
                QErrorMessage(parent=self).showMessage("Could not enable hotkeys.")
                self.settings.hotkeys_enabled = False
                self.hotkeys_toggle.setChecked(False)

    def enable_hotkeys(self):
        if IS_WINDOWS:
            increase_key = self.settings.increase_offset_hotkey.scancodes
            decrease_key = self.settings.decrease_offset_hotkey.scancodes
            self.hotkey_manager.enable_hotkeys(increase_key, decrease_key)

    def disable_hotkeys(self):
        if IS_WINDOWS:
            self.hotkey_manager.disable_hotkeys()
            self.split_offset = 0  # Reset the offset as you can no longer change it
            if not self.ls.connected:
                self.update_notes(0)

    def increase_offset(self):
        self.split_offset += 1
        # Rerender if not connected (if connected this will happen automatically)
        if not self.ls.connected:
            self.update_notes(0)
            self.ui.statusbar.showMessage(
                f"Trying to connect to Livesplit. | Split Offset: {self.split_offset}"
            )
        else:
            self.ui.statusbar.showMessage(
                f"Connected to Livesplit. | Split Offset: {self.split_offset}"
            )

    def decrease_offset(self):
        self.split_offset -= 1
        # Rerender if not connected (if connected this will happen automatically)
        if not self.ls.connected:
            self.update_notes(0)
            self.ui.statusbar.showMessage(
                f"Trying to connect to Livesplit. | Split Offset: {self.split_offset}"
            )
        else:
            self.ui.statusbar.showMessage(
                f"Connected to Livesplit. | Split Offset: {self.split_offset}"
            )

    def start_loops(self):
        """Start the livesplit server connection thread."""
        self.ls.start_loops()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            window = self.windowHandle()
            window.startSystemMove()
        return super().mousePressEvent(event)

    def closeEvent(self, event):
        """On close save settings and close the livesplit connection."""
        self.settings.save()
        if IS_WINDOWS:
            self.hotkey_manager.disable_all()  # Kill any hotkeys
        self.ls.close()
        event.accept()

    def resizeEvent(self, event):
        """Store the new window height and width to keep it between launches."""
        self.settings.width = self.width()
        self.settings.height = self.height()
        event.accept()

    def setup_actions(self):
        """Setup the browser element with custom options"""
        # Replace the context menu with the app context menu
        # noinspection PyUnresolvedReferences
        self.ui.notes.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.notes.customContextMenuRequested.connect(self.show_menu)
        # Allow links to open in an external browser
        page = ExtLinkWebEnginePage(self, backgroundColor=QColorConstants.Transparent)
        self.ui.notes.setPage(page)

    def build_menu(self):
        """Create the custom context menu."""
        self.rc_menu = QMenu()
        open_notes = self.rc_menu.addAction("Open Notes")
        open_notes.triggered.connect(self.open_notes)

        open_settings = self.rc_menu.addAction("Settings")
        open_settings.triggered.connect(self.open_settings)

        self.menu_on_top = self.rc_menu.addAction("Always on top")
        self.menu_on_top.setCheckable(True)
        self.menu_on_top.setChecked(self.settings.on_top)
        self.menu_on_top.triggered.connect(self.toggle_on_top)

        self.menu_transparency = self.rc_menu.addAction("Enable Transparency")
        self.menu_transparency.setCheckable(True)
        self.menu_transparency.setChecked(self.settings.transparency)
        self.menu_transparency.triggered.connect(self.toggle_transparency)

        if IS_WINDOWS:
            self.hotkeys_toggle = self.rc_menu.addAction("Enable Hotkeys")
            self.hotkeys_toggle.setCheckable(True)
            self.hotkeys_toggle.setChecked(self.settings.hotkeys_enabled)
            self.hotkeys_toggle.triggered.connect(self.toggle_hotkey_enable)

        exit_action = self.rc_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def show_menu(self):
        """Display the context menu at the cursor position."""
        if not self.rc_menu:
            self.build_menu()
        self.rc_menu.popup(QCursor.pos())

    def load_template(self):
        """Load the HTML template for the split rendering."""
        self.template = self.j2_environment.get_template(
            str(self.settings.html_template_file)
        )

    def load_css(self):
        """Read the CSS file into memory."""
        self.css = self.settings.full_css_path.read_text()

    def open_notes(self):
        """Open the a file dialog and create a Notes instance from the file."""
        notefile, _ = QFileDialog.getOpenFileName(
            self,
            "Open Notes",
            self.settings.notes_folder,
            "Note Files (*.txt *.md *.html);;All Files (*.*)",
        )

        if notefile:
            self.notefile = notefile
            # Reset split index and load notes
            self.notes = Notes.from_file(
                notefile, separator=self.settings.split_separator
            )
            # Remember this notes folder next time notes are loaded.
            self.settings.notes_folder = str(Path(notefile).parent)
            # Reset the split offset
            self.split_offset = 0

            self.update_notes(idx=0, refresh=True)

    def render_blank(self):
        """Render the initial blank template."""
        html = self.template.render(
            font_size=self.settings.font_size,
            font_color=self.settings.font_color,
            bg_color="transparent",
            css=self.css,
            notes=["<h1>Right Click to Load Notes</h1>"],
        )
        self.ui.notes.setHtml(html)

    def update_notes(self, idx, refresh=False):
        """
        Update the notes to the index given.

        :param idx: The new index
        :param refresh: force a refresh even if the index is the same
        """

        # Initial index can be -1 when livesplit is stopped
        # Add the offset and then make sure we're still above 0
        idx = max(idx, 0) + self.split_offset
        idx = max(idx, 0)

        if self.notes and (idx != self.split_index or refresh):
            start = idx - self.settings.previous_splits
            end = idx + self.settings.next_splits + 1

            html = self.template.render(
                font_size=self.settings.font_size,
                font_color=self.settings.font_color,
                bg_color="transparent",
                css=self.css,
                notes=self.notes.render_splits(start, end),
            )

            self.ui.notes.setHtml(html, baseUrl=self.notefile)
            self.split_index = idx

    def open_settings(self):
        """Open the settings dialog, refresh everything if the settings have changed."""
        # Block hotkeys while in the settings menu
        if IS_WINDOWS and self.hotkey_manager.enabled:
            self.disable_hotkeys()

        settings_dialog = SettingsDialog(
            parent=self, settings=self.settings, hotkey_manager=self.hotkey_manager
        )
        settings_dialog.setWindowIcon(self.icon)
        result = settings_dialog.exec()
        if result == 1:
            # Kill and restart connection if server ip or port change
            if (
                self.client.connection.server != self.settings.hostname
                or self.client.connection.port != self.settings.port
            ):
                self.ls.close()
                self.client = get_client(self.settings.hostname, self.settings.port)
                self.ls = LivesplitLink(self.client, self)
                self.ls.start_loops()

            # Redraw transparency settings (colours may have changed)
            self.refresh_transparency()

            # Reread notes with separator
            if self.notefile:
                self.notes = Notes.from_file(
                    self.notefile, separator=self.settings.split_separator
                )
                # Reset the offset
                self.split_offset = 0
                self.update_notes(self.split_index, refresh=True)
            else:
                self.render_blank()

        # Re-enable hotkeys if enabled
        if IS_WINDOWS and self.settings.hotkeys_enabled:
            self.enable_hotkeys()


class LivesplitLink(QtCore.QObject):
    """
    Handle the thread running the livesplit connection and linking to the main window.
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
        self.update_status(
            f"Trying to connect to Livesplit. | "
            f"Split Offset: {self.main_window.split_offset}"
        )
        self.connected = self.client.connect()
        if self.connected:
            self.update_status(
                f"Connected to Livesplit. | "
                f"Split Offset: {self.main_window.split_offset}"
            )

    def loop_update_split(self):
        while not self.break_loop:
            # If not connected attempt to connect
            if self.connected:
                try:
                    split_index = self.client.get_split_index()
                except (ConnectionError, TimeoutError):
                    self.connected = False
                    self.client.close()
                else:
                    # Send the signal to the main window to update.
                    # noinspection PyUnresolvedReferences
                    self.note_signal.emit(split_index)
            else:
                self.ls_connect()
            time.sleep(0.1)
