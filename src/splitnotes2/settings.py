import os
import sys
import json

from pathlib import Path


if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    base_path = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    base_path = Path(__file__).parent

settings_file = Path(base_path / "settings.json")
default_template_folder = Path(base_path / "ui" / "templates")
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
