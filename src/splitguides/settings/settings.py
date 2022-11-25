# COMPILE_PREFABS
import os
import socket
import sys
import json

from pathlib import Path

from prefab_classes import prefab, attribute
from prefab_classes.serializers import to_json

from ..hotkeys import hotkey_or_none

if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    base_path = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    base_path = Path(__file__).parents[1]

settings_file = Path(base_path / "settings.json")
default_template_folder = Path(base_path / "templates")
default_static_folder = Path(base_path / "static")
user_path = str(Path(os.path.expanduser("~")) / "Documents")

try:
    local_hostname = socket.gethostname()
except Exception:
    local_hostname = "127.0.0.1"
    print(
        "Could not get local network hostname, using 127.0.0.1. "
        "The server will only be accessible from this machine."
    )


@prefab(compile_prefab=True)
class Settings:
    """
    Global persistent settings handler
    """
    # What file to use
    output_file = attribute(default=settings_file, converter=Path)

    # Networking Settings
    hostname = attribute(default="localhost")
    port = attribute(default=16834)
    # Parser Settings
    split_separator = attribute(default="")
    # User Preferences
    previous_splits = attribute(default=0)
    next_splits = attribute(default=2)
    font_size = attribute(default=20)
    font_color = attribute(default="#000000")
    background_color = attribute(default="#f1f8ff")
    # Templating
    html_template_folder = attribute(default=default_template_folder, converter=Path)
    html_template_file = attribute(default="desktop.html")
    css_folder = attribute(default=default_static_folder, converter=Path)
    css_file = attribute(default="desktop.css")
    # Window Settings
    on_top = attribute(default=False)
    width = attribute(default=800)
    height = attribute(default=800)
    notes_folder = attribute(default=user_path)
    # Hotkey Settings
    hotkeys_enabled = attribute(default=False)

    increase_offset_hotkey = attribute(default=None, converter=hotkey_or_none)
    decrease_offset_hotkey = attribute(default=None, converter=hotkey_or_none)

    # Server Settings
    server_previous_splits = attribute(default=0)
    server_next_splits = attribute(default=0)
    server_hostname = attribute(default=local_hostname)
    server_port = attribute(default=14250)

    server_template_folder = attribute(default=default_template_folder, converter=Path)
    server_html_template_file = attribute(default="server.html")
    server_static_folder = attribute(default=default_static_folder, converter=Path)
    server_css_file = attribute(default="server.css")

    def save(self):
        """
        Save settings as JSON
        """
        def path_to_json(o):
            if isinstance(o, Path):
                return str(o)
            else:
                raise TypeError(
                    f"Object of type {o.__class__} is not JSON Serializable"
                )

        json_str = to_json(self, excludes=["output_file"], default=path_to_json)
        self.output_file.write_text(json_str)

    @classmethod
    def load(cls, input_filename=settings_file):
        """
        Load settings from a file, if the file does not exist
        just use defaults

        :param input_filename: Saved settings file.
        :return:
        """
        input_path = Path(input_filename)
        if input_path.exists():
            new_settings = json.loads(input_path.read_text())

            # noinspection PyArgumentList
            loaded_settings = cls(output_file=input_filename, **new_settings)

            # Check that the templates exist, reset otherwise
            # This will happen if the executable folder is moved
            # Absolute path ends up getting used because otherwise launching
            # from an external folder doesn't work
            if not Path(loaded_settings.full_template_path).exists():
                loaded_settings.html_template_folder = default_template_folder
                loaded_settings.html_template_file = "desktop.html"
            if not Path(loaded_settings.full_css_path).exists():
                loaded_settings.css_folder = default_static_folder
                loaded_settings.css_file = "desktop.css"
            if not Path(loaded_settings.server_template_folder).exists():
                loaded_settings.server_template_folder = default_template_folder
                loaded_settings.server_html_template_file = "server.html"
            if not Path(loaded_settings.server_static_folder).exists():
                loaded_settings.server_static_folder = default_static_folder
                loaded_settings.server_css_file = "server.css"

            return loaded_settings
        else:
            return Settings(output_file=input_filename)

    @property
    def full_template_path(self):
        return self.html_template_folder / self.html_template_file

    @property
    def full_css_path(self):
        return self.css_folder / self.css_file
