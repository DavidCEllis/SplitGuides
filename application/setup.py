"""
Special setup.py file for building the app
"""

import sys
from pathlib import Path

from cx_Freeze import setup, Executable

python3_dll = str(Path(sys.executable).parent / "python3.dll")
templates = str(
    Path(__file__).resolve().parents[1] / "src" / "splitnotes2" / "ui" / "templates"
)
icon_file = str(Path(__file__).resolve().parents[1] / "resources" / "logo_alpha.ico")
icon_png = str(Path(__file__).resolve().parents[1] / "resources" / "logo_alpha.png")

base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
    "build_exe": {
        "includes": "atexit",
        "include_files": [python3_dll, templates, icon_png],
    }
}

executables = [
    Executable("app.py", base=base, targetName="splitnotes2", icon=icon_file),
    Executable("app_server.py", targetName="splitnotes2_server", icon=icon_file),
]

setup(
    name="splitnotes2",
    version="0.4.0",
    description="Speedrun splitnotes tool with HTML rendering",
    options=options,
    executables=executables,
)
