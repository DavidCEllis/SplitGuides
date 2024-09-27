"""
Special setup.py file for building the app

`python setup.py build` in this folder to create the application.
"""

import sys
from pathlib import Path

from cx_Freeze import setup, Executable

import splitguides

base_path = Path(__file__).resolve().parents[1]

desktop_app = str(base_path / "src" / "splitguides" / "__main__.py")
server_app = str(base_path / "src" / "splitguides" / "server" / "__main__.py")

templates = str(base_path / "src" / "splitguides" / "templates")
static_folder = str(base_path / "src" / "splitguides" / "static")
icon_file = str(base_path / "resources" / "logo_alpha.ico")
icon_png = str(base_path / "resources" / "logo_alpha.png")


base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
    "build_exe": {
        "includes": [
            "atexit",
            "jinja2.ext",
            "html.parser",
            "markdown",
            "markdown.extensions",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
            "markdown.extensions.tables",
        ],
        "include_files": [templates, static_folder, icon_png],
    }
}

executables = [
    Executable(script=desktop_app, base=base, target_name="splitguides", icon=icon_file),
    Executable(script=server_app, target_name="splitguides_server", icon=icon_file),
]

setup(
    name="splitguides",
    version=splitguides.__version__,
    description="Speedrun notes tool with HTML rendering",
    options=options,
    executables=executables,
)
