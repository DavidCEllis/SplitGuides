import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

from PySide6.QtWidgets import QDialog, QColorDialog, QFileDialog
from PySide6.QtCore import QRegularExpression, Slot
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QRegularExpressionValidator,
    QColor,
)

from ..settings import DesktopSettings
from .color import rgba_to_qcolor, qcolor_to_rgba
from .hotkey_manager import HotkeyManager
from .layouts import Ui_Settings
from ..hotkeys import Hotkey


class SettingsDialog(QDialog):
    def __init__(
        self, parent, settings: DesktopSettings, hotkey_manager: HotkeyManager
    ):
        super().__init__(parent=parent)
        self.ui = Ui_Settings()
        self.ui.setupUi(self)

        self.hotkey_manager = hotkey_manager
        self.nextsplitkey = None
        self.previoussplitkey = None

        self.settings = settings
        self.temp_html_path = self.settings.full_template_path
        self.temp_css_path = self.settings.full_css_path

        self.setup_validators()
        self.fill_settings()

        self.ui.textcolor_button.clicked.connect(self.font_color_dialog)
        self.ui.bgcolor_button.clicked.connect(self.bg_color_dialog)
        self.ui.htmltemplate_button.clicked.connect(self.html_template_dialog)
        self.ui.css_button.clicked.connect(self.css_dialog)

        if sys.platform == "win32":
            self.ui.nextsplitkey_button.clicked.connect(self.get_increase_hotkey)
            self.ui.previoussplitkey_button.clicked.connect(self.get_decrease_hotkey)
        else:
            self.ui.nextsplitkey_button.setDisabled(True)
            self.ui.previoussplitkey_button.setDisabled(True)

        self.pool = ThreadPoolExecutor(max_workers=1)

    def setup_validators(self):
        color_re = QRegularExpression(r"#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})")
        color_validator = QRegularExpressionValidator(color_re, None)
        self.ui.port_edit.setValidator(QIntValidator(1024, 65535, None))
        # 255 splits seems like a lot
        self.ui.previous_edit.setValidator(QIntValidator(0, 255, None))
        self.ui.advance_edit.setValidator(QIntValidator(0, 255, None))
        # I don't know why you'd set a font size of 10k but sure why not
        self.ui.fontsize_edit.setValidator(QDoubleValidator(0.0, 10000.0, 2, None))
        self.ui.textcolor_edit.setValidator(color_validator)
        self.ui.bgcolor_edit.setValidator(color_validator)

    def fill_settings(self):
        self.ui.hostname_edit.setText(self.settings.hostname)
        self.ui.port_edit.setText(str(self.settings.port))
        self.ui.previous_edit.setText(str(self.settings.previous_splits))
        self.ui.advance_edit.setText(str(self.settings.next_splits))
        self.ui.separator_edit.setText(self.settings.split_separator)
        self.ui.fontsize_edit.setText(str(self.settings.font_size))
        self.ui.textcolor_edit.setText(self.settings.font_color)
        self.ui.bgcolor_edit.setText(self.settings.background_color)
        self.ui.htmltemplate_edit.setText(str(self.settings.html_template_file))
        self.ui.css_edit.setText(str(self.settings.css_file))

        if self.settings.increase_offset_hotkey:
            self.ui.nextsplitkey_edit.setText(self.settings.increase_offset_hotkey.name)
        if self.settings.decrease_offset_hotkey:
            self.ui.previoussplitkey_edit.setText(
                self.settings.decrease_offset_hotkey.name
            )
        self.nextsplitkey = self.settings.increase_offset_hotkey
        self.previoussplitkey = self.settings.decrease_offset_hotkey

    def store_settings(self):
        self.settings.hostname = self.ui.hostname_edit.text()
        self.settings.port = int(self.ui.port_edit.text())
        self.settings.previous_splits = int(self.ui.previous_edit.text())
        self.settings.next_splits = int(self.ui.advance_edit.text())
        self.settings.split_separator = self.ui.separator_edit.text()
        self.settings.font_size = float(self.ui.fontsize_edit.text())
        self.settings.font_color = self.ui.textcolor_edit.text()
        self.settings.background_color = self.ui.bgcolor_edit.text()

        self.settings.increase_offset_hotkey = self.nextsplitkey
        self.settings.decrease_offset_hotkey = self.previoussplitkey

        # Paths get stored in temporary variables
        self.settings.html_template_folder = Path(self.temp_html_path).parent
        self.settings.html_template_file = Path(self.temp_html_path).name

        self.settings.css_folder = Path(self.temp_css_path).parent
        self.settings.css_file = Path(self.temp_css_path).name

    def font_color_dialog(self):
        """
        Pop up a color dialog for the text color.
        """
        color = QColorDialog.getColor(
            rgba_to_qcolor(self.ui.textcolor_edit.text()),
            parent=self,
            title="Text Color",
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.ui.textcolor_edit.setText(qcolor_to_rgba(color))

    def bg_color_dialog(self):
        """
        Pop up a color dialog for the background color.
        """
        color = QColorDialog.getColor(
            rgba_to_qcolor(self.ui.bgcolor_edit.text()),
            parent=self,
            title="Background Color",
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.ui.bgcolor_edit.setText(qcolor_to_rgba(color))

    def html_template_dialog(self):
        htmlfile, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            str(self.settings.html_template_folder),
            "html templates (*.html);;All Files (*.*)",
        )

        if htmlfile:
            self.temp_html_path = htmlfile
            self.ui.htmltemplate_edit.setText(Path(htmlfile).name)

    def css_dialog(self):
        cssfile, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            str(self.settings.css_folder),
            "css files (*.css);;All Files (*.*)",
        )

        if cssfile:
            self.temp_css_path = cssfile
            self.ui.css_edit.setText(Path(cssfile).name)

    def get_increase_hotkey(self):
        """Get a hotkey to use to increase the split offset"""
        # First set the buttons dialog and disable the interface
        self.ui.nextsplitkey_button.setText("Listening...")
        self.setEnabled(False)
        fn = lambda: self.hotkey_manager.select_input(self.return_increase_hotkey)
        self.pool.submit(fn)

    @Slot(str)
    def return_increase_hotkey(self, hotkey=None):
        """
        Get the returned hotkey or cancel if no hotkey is returned
        :param hotkey:
        """
        if hotkey:
            hotkey = Hotkey(**json.loads(hotkey))
            self.ui.nextsplitkey_edit.setText(hotkey.name)
            self.nextsplitkey = hotkey
        else:
            self.ui.nextsplitkey_edit.setText("")
            self.nextsplitkey = None

        self.ui.nextsplitkey_button.setText("Select")

        # Unbind next split key if both are equal
        if hotkey and self.ui.previoussplitkey_edit.text() == hotkey.name:
            self.ui.previoussplitkey_edit.setText("")
            self.previoussplitkey = None

        # Disconnect the hotkey signal from this function
        self.hotkey_manager.hotkey_signal.disconnect(self.return_increase_hotkey)

        self.setEnabled(True)

    def get_decrease_hotkey(self):
        """Get a hotkey to use to decrease the split offset"""
        self.ui.previoussplitkey_button.setText("Listening...")
        self.setEnabled(False)
        fn = lambda: self.hotkey_manager.select_input(self.return_decrease_hotkey)
        self.pool.submit(fn)

    @Slot(str)
    def return_decrease_hotkey(self, hotkey=None):
        """
        Get the returned hotkey or cancel if no hotkey is returned
        :param hotkey:
        """
        if hotkey:
            hotkey = Hotkey(**json.loads(hotkey))
            self.ui.previoussplitkey_edit.setText(hotkey.name)
            self.previoussplitkey = hotkey
        else:
            self.ui.previoussplitkey_edit.setText("")
            self.previoussplitkey = None
        self.ui.previoussplitkey_button.setText("Select")

        # Unbind next split key if both are equal
        if hotkey and self.ui.nextsplitkey_edit.text() == hotkey.name:
            self.ui.nextsplitkey_edit.setText("")
            self.nextsplitkey = None

        # Disconnect the hotkey signal from this function
        self.hotkey_manager.hotkey_signal.disconnect(self.return_decrease_hotkey)

        self.setEnabled(True)

    def accept(self):
        """If the dialog is accepted save the settings"""
        # Normal cleanup
        super().accept()
        # Store the settings in the settings object
        self.store_settings()
