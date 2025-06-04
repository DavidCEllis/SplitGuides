import sys
import os

from pathlib import Path

from PySide6 import QtCore
from PySide6.QtWidgets import QDialog, QColorDialog, QFileDialog
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QRegularExpressionValidator,
    QColor,
)

from ..settings import ServerSettings
from .color import colorFromHexRgba, colorToHexRgba
from .layouts import Ui_ServerSettings


# Get correct paths
if getattr(sys, "frozen", False):  # pragma: nocover
    base_path = Path(sys.executable).parent
    icon_file = str(base_path / "logo_alpha.png")
elif os.environ.get("DUCKTOOLS_ENV_LAUNCH_TYPE"):
    # Ducktools-env zipapp
    base_path = Path(__file__).parent
    icon_file = str(base_path.parents[1] / "resources" / "logo_alpha.png")
else:
    base_path = Path(__file__).parent
    icon_file = str(base_path.parents[2] / "resources" / "logo_alpha.png")


class ServerSettingsDialog(QDialog):
    def __init__(
        self,
        parent,
        settings: ServerSettings,
    ):
        super().__init__(parent=parent)

        self.ui = Ui_ServerSettings()
        self.ui.setupUi(self)

        self.settings = settings

        # noinspection PyUnresolvedReferences
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        # self.hotkey_manager = hotkey_manager
        self.nextsplitkey = None
        self.previoussplitkey = None

        self.temp_html_path = self.settings.full_template_path
        self.temp_css_path = self.settings.full_css_path

        self.setup_validators()
        self.fill_settings()

        self.ui.textcolor_button.clicked.connect(self.font_color_dialog)
        self.ui.bgcolor_button.clicked.connect(self.bg_color_dialog)
        self.ui.htmltemplate_button.clicked.connect(self.html_template_dialog)
        self.ui.css_button.clicked.connect(self.css_dialog)

        # Next and previous split keys are currently non-functioning
        # self.ui.nextsplitkey_button.clicked.connect(self.get_increase_hotkey)
        # self.ui.previoussplitkey_button.clicked.connect(self.get_decrease_hotkey)
        # self.pool = ThreadPoolExecutor(max_workers=1)
        self.ui.nextsplitkey_button.setDisabled(True)
        self.ui.previoussplitkey_button.setDisabled(True)
        self.ui.nextsplitkey_label.hide()
        self.ui.nextsplitkey_edit.hide()
        self.ui.nextsplitkey_button.hide()
        self.ui.previoussplitkey_label.hide()
        self.ui.previoussplitkey_edit.hide()
        self.ui.previoussplitkey_button.hide()
        self.ui.divider_4.hide()
        self.adjustSize()

        self.ui.confirm_cancel_box.accepted.connect(self.accept)
        self.ui.confirm_cancel_box.rejected.connect(self.reject)

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

        self.ui.noteserverhost_edit.setText(self.settings.server_hostname)
        self.ui.noteserverport_edit.setText(str(self.settings.server_port))

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

        self.settings.server_hostname = self.ui.noteserverhost_edit.text()
        self.settings.server_port = int(self.ui.noteserverport_edit.text())

    def font_color_dialog(self):
        """
        Pop up a color dialog for the text color.
        """
        color = QColorDialog.getColor(
            colorFromHexRgba(self.settings.font_color),
            parent=self,
            title="Text Color",
            options=QColorDialog.ColorDialogOptions() | QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.ui.textcolor_edit.setText(colorToHexRgba(color))

    def bg_color_dialog(self):
        """
        Pop up a color dialog for the background color.
        """
        color = QColorDialog.getColor(
            colorFromHexRgba(self.settings.background_color),
            parent=self,
            title="Background Color",
            options=QColorDialog.ColorDialogOptions() | QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.ui.bgcolor_edit.setText(colorToHexRgba(color))

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

    def accept(self):
        """If the dialog is accepted save the settings"""
        # Normal cleanup
        super().accept()
        # Store the settings in the settings object
        self.store_settings()
