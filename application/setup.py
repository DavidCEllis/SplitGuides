"""
Special setup.py file for building the app
"""

import sys
from pathlib import Path

from cx_Freeze import setup, Executable

base_path = Path(__file__).resolve().parents[1]
templates = str(base_path / "src" / "splitnotes2" / "templates")
static_folder = str(base_path / "src" / "splitnotes2" / "static")
icon_file = str(base_path / "resources" / "logo_alpha.ico")
icon_png = str(base_path / "resources" / "logo_alpha.png")

base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
    "build_exe": {
        "includes": ["atexit", "jinja2.ext", "html.parser"],
        "include_files": [templates, static_folder, icon_png],
    }
}

executables = [
    Executable("app.py", base=base, target_name="splitnotes2", icon=icon_file),
    Executable("app_server.py", target_name="splitnotes2_server", icon=icon_file),
]

setup(
    name="splitnotes2",
    version="0.6.0",
    description="Speedrun notes tool with HTML rendering",
    options=options,
    executables=executables,
)
