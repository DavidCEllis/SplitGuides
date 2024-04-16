import os
import socket
import sys
import json

from abc import ABCMeta
from pathlib import Path
from typing import ClassVar

from ducktools.classbuilder.prefab import prefab, attribute, as_dict, is_prefab_instance

from .hotkeys import hotkey_or_none, Hotkey

if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    base_path = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    base_path = Path(__file__).parent

desktop_settings_file = Path(base_path / "settings.json")
server_settings_file = Path(base_path / "server_settings.json")

default_template_folder = Path(base_path / "templates")
default_static_folder = Path(base_path / "static")
user_path = str(Path(os.path.expanduser("~")) / "Documents")

try:
    local_hostname = socket.gethostname()
except OSError:
    local_hostname = "127.0.0.1"
    print(
        "Could not get local network hostname, using 127.0.0.1. "
        "The server will only be accessible from this machine."
    )


@prefab
class BaseSettings(metaclass=ABCMeta):
    # Settings files to use - Default to desktop versions
    SETTINGS_FILE: ClassVar[None | Path] = desktop_settings_file

    default_template_filename: ClassVar[str] = "desktop.html"
    default_css_filename: ClassVar[str] = "desktop.css"

    # Settings save file
    output_file: None | Path = attribute(default=None, in_dict=False)

    # Networking Settings
    hostname: str = "localhost"
    port: int = 16834

    # Parser Settings
    split_separator: str = ""

    # Display Settings
    previous_splits: int = 0
    next_splits: int = 2
    font_size: int | float = 20.0
    font_color: str = "#000000"
    background_color: str = "#f1f8ff"

    html_template_folder: Path = default_template_folder
    css_folder: Path = default_static_folder
    html_template_file: None | str = None
    css_file: None | str = None

    notes_folder: Path = user_path

    # Hotkey Settings
    hotkeys_enabled: bool = False
    increase_offset_hotkey: None | Hotkey = None
    decrease_offset_hotkey: None | Hotkey = None

    def __prefab_post_init__(
        self,
        output_file,
        html_template_folder,
        css_folder,
        increase_offset_hotkey,
        decrease_offset_hotkey,
    ):
        self.output_file = Path(output_file)
        self.html_template_folder = Path(html_template_folder)
        self.css_folder = Path(css_folder)

        self.increase_offset_hotkey = hotkey_or_none(increase_offset_hotkey)
        self.decrease_offset_hotkey = hotkey_or_none(decrease_offset_hotkey)

    def save(self):
        """
        Save settings as JSON
        """

        def json_default(o):
            if is_prefab_instance(o):
                return as_dict(o)
            elif isinstance(o, Path):
                return str(o)
            else:
                raise TypeError(
                    f"Object of type {o.__class__} is not JSON Serializable"
                )

        json_str = json.dumps(
            self,
            default=json_default,
            indent=2,
        )
        self.output_file.write_text(json_str)

    # noinspection PyArgumentList
    @classmethod
    def load(cls, input_filename: None | str | Path = None):
        """
        Load settings from a file, if the file does not exist
        just use defaults

        :param input_filename: Saved settings file.
        :return:
        """
        if input_filename is None:
            input_filename = cls.SETTINGS_FILE

        input_path = Path(input_filename)
        if input_path.exists():
            new_settings = json.loads(input_path.read_text())

            # noinspection PyArgumentList
            loaded_settings = cls(output_file=input_filename, **new_settings)

            # Check that the templates exist, reset otherwise
            # This will happen if the executable folder is moved
            # Absolute path ends up getting used because otherwise launching
            # from an external folder doesn't work
            loaded_settings.fix_template_paths()

            return loaded_settings
        else:
            return cls(output_file=input_filename)

    def fix_template_paths(self):
        if not self.full_template_path.exists():
            self.html_template_folder = default_template_folder
            self.html_template_file = self.default_template_filename
        if not self.full_css_path.exists():
            self.css_folder = default_static_folder
            self.css_file = self.default_css_filename

    @property
    def full_template_path(self):
        return self.html_template_folder / self.html_template_file

    @property
    def full_css_path(self):
        return self.css_folder / self.css_file


@prefab
class DesktopSettings(BaseSettings):
    """
    Global persistent settings handler
    """

    # Class variables
    SETTINGS_FILE: ClassVar[Path] = desktop_settings_file
    default_template_filename: ClassVar[str] = "desktop.html"
    default_css_filename: ClassVar[str] = "desktop.css"

    # What file to use
    output_file: Path = attribute(default=desktop_settings_file, in_dict=False)

    # Override Defaults
    html_template_file: str = "desktop.html"
    css_file: str = "desktop.css"

    # Window Settings
    on_top: bool = False
    width: int = 800
    height: int = 800


@prefab
class ServerSettings(BaseSettings):
    # Class variables
    SETTINGS_FILE: ClassVar[Path] = server_settings_file
    default_template_filename: ClassVar[str] = "server.html"
    default_css_filename: ClassVar[str] = "server.css"

    output_file: Path = attribute(default=server_settings_file, in_dict=False)

    # Override defaults
    html_template_file: str = "server.html"
    css_file: str = "server.css"

    server_hostname: str = local_hostname
    server_port: int = 8000
