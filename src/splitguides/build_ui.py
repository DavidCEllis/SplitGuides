"""
Build the .ui files into .py script files.
"""
import os
import sys

# In v5.14 they removed pyside2uic so this invokes uic directly
from subprocess import run
from pathlib import Path

import PySide6


def uic(infile, outfile):
    """
    Run the QT User Interface Compiler to convert a .ui file to a .py file

    :param infile: Input path
    :param outfile: Output path
    :return: the CompletedProcess object from running the uic .exe
    """
    # This logic is largely from PySide6.scripts.pyside_tool
    # The problem with calling the pyside6-uic script directly is discovery
    # while inside the isolated venv
    pyside_dir = Path(PySide6.__file__).resolve().parent

    if sys.platform != "win32":
        exe = pyside_dir / "Qt" / "libexec" / "uic"
    else:
        exe = pyside_dir / "uic.exe"

    cmd = [os.fspath(exe), "-g", "python", "--o", str(outfile), str(infile)]

    return run(cmd, capture_output=True)


def build_ui(replace=True):
    """
    Compile any .ui files in this folder to the build folder as .py files

    :param replace: replace existing UI files
    """
    # Scan this folder for .ui files
    root = Path(__file__).parent / "ui" / "layouts"
    ui_files = list(root.glob("*.ui"))

    # Make the build and __init__ files if they do not exist
    Path(root / "build").mkdir(exist_ok=True)
    Path(root / "build" / "__init__.py").touch(exist_ok=True)

    print("Building user interface files.")

    for infile in ui_files:
        outfile = root / "build" / infile.with_suffix(".py").name

        if replace or not outfile.exists:
            result = uic(infile, outfile)

            if result.returncode == 0:
                print(f"Read: {infile}\nBuilt: {outfile}\n")
            else:
                raise RuntimeError(
                    "Failed to convert .uic layout file to .py: "
                    f"code{result.returncode}\n{result.stderr}"
                )
        else:
            print(f"Output file {outfile} already exists")


if __name__ == "__main__":
    build_ui(replace=True)
