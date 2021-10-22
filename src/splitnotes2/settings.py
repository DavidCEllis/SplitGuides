import os
import socket
import sys
import json

from pathlib import Path

import attr

if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    base_path = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    base_path = Path(__file__).parent

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


@attr.s
class Settings:
    """
    Global persistent settings handler
    """

    # What file to use
    output_file = attr.ib(default=settings_file, converter=Path)

    # Networking Settings
    hostname = attr.ib(default="localhost")
    port = attr.ib(default=16834)
    # Parser Settings
    split_separator = attr.ib(default="")
    # User Preferences
    previous_splits = attr.ib(default=0)
    next_splits = attr.ib(default=2)
    font_size = attr.ib(default=20)
    font_color = attr.ib(default="#000000")
    background_color = attr.ib(default="#f1f8ff")
    # Templating
    html_template_folder = attr.ib(default=default_template_folder, converter=Path)
    html_template_file = attr.ib(default="desktop.html")
    css_folder = attr.ib(default=default_static_folder, converter=Path)
    css_file = attr.ib(default="desktop.css")
    # Window Settings
    on_top = attr.ib(default=False)
    width = attr.ib(default=800)
    height = attr.ib(default=800)
    notes_folder = attr.ib(default=user_path)
    # Server Settings
    server_previous_splits = attr.ib(default=0)
    server_next_splits = attr.ib(default=0)
    server_hostname = attr.ib(default=local_hostname)
    server_port = attr.ib(default=14250)

    server_template_folder = attr.ib(default=default_template_folder, converter=Path)
    server_html_template_file = attr.ib(default="server.html")
    server_static_folder = attr.ib(default=default_static_folder)
    server_css_file = attr.ib(default="server.css")

    def save(self):
        """
        Save settings as JSON
        """
        as_dict = attr.asdict(self)
        del as_dict["output_file"]  # Don't save the name of the output file
        self.output_file.write_text(json.dumps(as_dict, indent=2, default=str))

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
            return cls(output_file=input_filename)

    @property
    def full_template_path(self):
        return self.html_template_folder / self.html_template_file

    @property
    def full_css_path(self):
        return self.css_folder / self.css_file
