import os
import sys
import json
from pathlib import Path

from PySide2.QtWidgets import QDialog, QColorDialog, QFileDialog
from PySide2.QtCore import QRegExp
from PySide2.QtGui import QIntValidator, QRegExpValidator, QColor

from .layouts import Ui_Settings


if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    base_path = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    base_path = Path(__file__).parent

settings_file = Path(base_path / "settings.json")
default_template_folder = Path(base_path / "html")
user_path = str(Path(os.path.expanduser("~")) / "Documents")


class Settings:
    """
    This handles the settings object and the defaults.
    """

    defaults = {
        # Networking settings
        "hostname": "localhost",
        "port": 16834,
        # Parser settings
        "split_separator": "",
        # User Preferences
        "previous_splits": 0,
        "next_splits": 2,
        "font_size": 20,
        "font_color": "#000000",
        "background_color": "#f1f8ff",
        # Templating
        "html_template_folder": default_template_folder,
        "html_template_file": "default.html",
        "css_folder": default_template_folder,
        "css_file": "default.css",
        # Remembering settings
        "on_top": False,
        "width": 800,
        "height": 800,
        "notes_folder": user_path,
    }

    def __init__(self):
        # Start with the defaults
        self.settings = {**self.defaults}

        # Load additional settings from thte settings file if it exists
        if settings_file.exists():
            new_settings = json.loads(settings_file.read_text())

            # Convert strings to Paths
            new_settings["html_template_folder"] = Path(
                new_settings["html_template_folder"]
            )
            new_settings["css_folder"] = Path(new_settings["css_folder"])

            self.settings.update(**new_settings)

    def __getattr__(self, item):
        """
        Display the contents of the settings dict as if they are the attributes of
        this settings object.
        """
        try:
            return self.settings[item]
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{item}'")

    def __setattr__(self, key, value):
        """
        When an attribute is updated, if it exists as a key in the settings dict,
        instead update that item.
        """
        # If the key is a settings value update it, otherwise update the instance dict.
        if key in self.defaults:
            self.settings[key] = value
        else:
            super().__setattr__(key, value)

    def save(self):
        output = json.dumps(self.settings, indent=2, default=str)
        settings_file.write_text(output)

    @property
    def full_template_path(self):
        return self.html_template_folder / self.html_template_file

    @property
    def full_css_path(self):
        return self.css_folder / self.css_file


class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent=parent)
        self.ui = Ui_Settings()
        self.ui.setupUi(self)

        self.settings = settings
        self.temp_html_path = self.settings.full_template_path
        self.temp_css_path = self.settings.full_css_path

        self.setup_validators()
        self.fill_settings()

        self.ui.textcolor_button.clicked.connect(self.font_color_dialog)
        self.ui.bgcolor_button.clicked.connect(self.bg_color_dialog)
        self.ui.htmltemplate_button.clicked.connect(self.html_template_dialog)
        self.ui.css_button.clicked.connect(self.css_dialog)

    def setup_validators(self):
        color_re = QRegExp(r"#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})")
        color_validator = QRegExpValidator(color_re, None)
        self.ui.port_edit.setValidator(QIntValidator(1024, 65535, None))
        # 255 splits seems like a lot
        self.ui.previous_edit.setValidator(QIntValidator(0, 255, None))
        self.ui.advance_edit.setValidator(QIntValidator(0, 255, None))
        # I don't know why you'd set a font size of 10k but sure why not
        self.ui.fontsize_edit.setValidator(QIntValidator(0, 10000, None))
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

    def store_settings(self):
        self.settings.hostname = self.ui.hostname_edit.text()
        self.settings.port = int(self.ui.port_edit.text())
        self.settings.previous_splits = int(self.ui.previous_edit.text())
        self.settings.next_splits = int(self.ui.advance_edit.text())
        self.settings.split_separator = self.ui.separator_edit.text()
        self.settings.font_size = int(self.ui.fontsize_edit.text())
        self.settings.font_color = self.ui.textcolor_edit.text()
        self.settings.background_color = self.ui.bgcolor_edit.text()

        # Paths get stored in temporary variables
        self.settings.html_template_folder = Path(self.temp_html_path).parent
        self.settings.html_template_file = Path(self.temp_html_path).name

        self.settings.css_folder = Path(self.temp_css_path).parent
        self.settings.css_file = Path(self.temp_css_path).name

    def font_color_dialog(self):
        """
        Pop up a color dialog for the text color.
        """
        color = QColorDialog.getColor(QColor(self.settings.font_color), parent=self)
        self.ui.textcolor_edit.setText(color.name())

    def bg_color_dialog(self):
        """
        Pop up a color dialog for the background color.
        """
        color = QColorDialog.getColor(
            QColor(self.settings.background_color), parent=self
        )
        self.ui.bgcolor_edit.setText(color.name())

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
            str(self.settings.html_template_folder),
            "css files (*.css);;All Files (*.*)",
        )

        if cssfile:
            self.temp_css_path = cssfile
            self.ui.css_edit.setText(Path(cssfile).name)
