"""
Special setup.py file for building the app

`python setup.py build` in this folder to create the application.
"""

import itertools
import sys
import shutil
import subprocess
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
readme = str(base_path / "readme.md")
license_file = str(base_path / "COPYING")


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
        "include_files": [templates, static_folder, icon_png, readme, license_file],
    }
}

executables = [
    Executable(script=desktop_app, base=base, target_name="splitguides", icon=icon_file),
    Executable(script=server_app, target_name="splitguides_server", icon=icon_file),
]

if __name__ == "__main__":
    build_path = Path.cwd() / "build"
    if build_path.exists:
        print("Cleaning up build path")
        for f in itertools.chain(
            build_path.glob("exe.*"),
            build_path.glob("SplitGuides_v*"),
        ):
            if f.is_dir():
                print(f"Removing: {f}")
                shutil.rmtree(f)

        for f in build_path.glob("*.zip"):
            print(f"Removing: {f}")
            f.unlink()

    setup(
        name="splitguides",
        version=splitguides.__version__,
        description="Speedrun notes tool with HTML rendering",
        options=options,
        executables=executables,
    )

    app_path = list(build_path.glob("exe.*"))[0]
    output_folder = app_path.with_name(f"SplitGuides_v{splitguides.__version__}")
    app_path.rename(output_folder)

    zip_path = f"{output_folder}.zip"

    print(f"Building zip archive at {zip_path}")
    subprocess.run([
        sys.executable,
        "-m",
        "zipfile",
        "-c",
        str(zip_path),
        str(output_folder),
    ])
