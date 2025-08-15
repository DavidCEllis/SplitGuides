import os
import socket
import sys
import json

from abc import ABCMeta
from pathlib import Path
from typing import ClassVar

from ducktools.classbuilder.prefab import prefab, attribute, as_dict, is_prefab_instance, get_attributes

from .hotkeys import hotkey_or_none, Hotkey
from .exceptions import UnsupportedPlatformError

PROJECT_NAME = "splitguides"

match sys.platform:
    # Don't change existing win32/linux config locations
    # but let platformdirs handle this for previously unsupported platforms
    case "win32":
        if _local_app_folder := os.environ.get("LOCALAPPDATA"):
            if not os.path.isdir(_local_app_folder):
                raise FileNotFoundError(
                    f"Could not find local app data folder {_local_app_folder}"
                )
        else:
            raise EnvironmentError("Environment variable %LOCALAPPDATA% not found")
        SETTINGS_FOLDER = Path(_local_app_folder) / PROJECT_NAME
    case "linux":
        SETTINGS_FOLDER = Path(os.path.expanduser(os.path.join("~", f".{PROJECT_NAME}")))
    case other:
        import platformdirs
        SETTINGS_FOLDER = Path(platformdirs.user_config_dir(PROJECT_NAME))

SETTINGS_FOLDER.mkdir(exist_ok=True)

if getattr(sys, "frozen", False):  # pragma: nocover
    # Application is .exe, use visible files
    APPLICATION_FOLDER = Path(sys.executable).parent
else:
    # Running as .py - use standard folder structure
    APPLICATION_FOLDER = Path(__file__).parent

DESKTOP_SETTINGS_FILE = SETTINGS_FOLDER / "settings.json"
SERVER_SETTINGS_FILE = SETTINGS_FOLDER / "server_settings.json"

DEFAULT_TEMPLATE_FOLDER = Path(APPLICATION_FOLDER / "templates")
DEFAULT_STATIC_FOLDER = Path(APPLICATION_FOLDER / "static")

USER_PATH = str(Path(os.path.expanduser("~")) / "Documents")

try:
    LOCAL_HOSTNAME = socket.gethostname()
except OSError:
    LOCAL_HOSTNAME = "127.0.0.1"
    print(
        "Could not get local network hostname, using 127.0.0.1. "
        "The server will only be accessible from this machine."
    )


@prefab
class BaseSettings(metaclass=ABCMeta):
    # Settings files to use - Default to desktop versions
    SETTINGS_FILE: ClassVar[Path] = DESKTOP_SETTINGS_FILE

    default_template_filename: ClassVar[str] = "desktop.html"
    default_css_filename: ClassVar[str] = "desktop.css"

    # Settings save file
    output_file: Path = attribute(serialize=False)

    # Networking Settings
    timer: str = "LiveSplit"
    hostname: str = "localhost"
    port: int = 16834

    # Parser Settings
    split_separator: str = ""

    # Display Settings
    previous_splits: int = 0
    next_splits: int = 2
    font_size: int | float = 20.0
    # Color format: Hex Rgba, NOT argb
    font_color: str = "#000000ff"
    background_color: str = "#f1f8ffff"

    html_template_folder: Path = DEFAULT_TEMPLATE_FOLDER
    css_folder: Path = DEFAULT_STATIC_FOLDER

    # Default to desktop versions
    html_template_file: str = "desktop.html"
    css_file: str = "desktop.css"

    notes_folder: str = USER_PATH

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

            valid_attribs = {k for k, v in get_attributes(cls).items() if v.init}

            # Filter settings from new_settings so there are no invalid keys
            filtered_settings = {
                k: v for k, v in new_settings.items()
                if k in valid_attribs
            }

            loaded_settings = cls(output_file=input_path, **filtered_settings)

            # Check that the templates exist, reset otherwise
            # This will happen if the executable folder is moved
            # Absolute path ends up getting used because otherwise launching
            # from an external folder doesn't work
            loaded_settings.fix_template_paths()

            return loaded_settings
        else:
            return cls(output_file=input_path)

    def fix_template_paths(self):
        if not self.full_template_path.exists():
            self.html_template_folder = DEFAULT_TEMPLATE_FOLDER
            self.html_template_file = self.default_template_filename
        if not self.full_css_path.exists():
            self.css_folder = DEFAULT_STATIC_FOLDER
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
    SETTINGS_FILE: ClassVar[Path] = DESKTOP_SETTINGS_FILE
    default_template_filename: ClassVar[str] = "desktop.html"
    default_css_filename: ClassVar[str] = "desktop.css"

    # What file to use
    output_file: Path = attribute(default=DESKTOP_SETTINGS_FILE, serialize=False)

    # Override Defaults
    html_template_file: str = "desktop.html"
    css_file: str = "desktop.css"

    # Window Settings
    on_top: bool = False
    transparency: bool = False
    width: int = 800
    height: int = 800


@prefab
class ServerSettings(BaseSettings):
    # Class variables
    SETTINGS_FILE: ClassVar[Path] = SERVER_SETTINGS_FILE
    default_template_filename: ClassVar[str] = "server.html"
    default_css_filename: ClassVar[str] = "server.css"

    output_file: Path = attribute(default=SERVER_SETTINGS_FILE, serialize=False)

    # Override defaults
    html_template_file: str = "server.html"
    css_file: str = "server.css"

    server_hostname: str = LOCAL_HOSTNAME
    server_port: int = 8000
