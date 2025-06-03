"""
Build the .ui files into .py script files.
"""
import os
import sys

# In v5.14 they removed pyside2uic so this invokes uic directly
from subprocess import run
from pathlib import Path

import PySide6

pyside_folder = Path(PySide6.__file__).parent


def uic(infile, outfile):
    """
    Run the QT User Interface Compiler to convert a .ui file to a .py file

    :param infile: Input path
    :param outfile: Output path
    :return: the CompletedProcess object from running the uic .exe
    """
    exe = os.fspath(Path(sys.executable).parent / "pyside6-uic")
    cmd = [exe, "--o", str(outfile), str(infile)]
    return run(cmd, capture_output=True)


def build_ui(replace=True):
    """
    Compile any .ui files in this folder to the build folder as .py files

    :param replace: replace existing UI files
    """
    # Scan this folder for .ui files
    root = Path(__file__).parent / "ui" / "layouts"
    ui_files = root.glob("*.ui")

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
                print(f"Failed to convert: code{result.returncode}\n{result.stderr}")
        else:
            print(f"Output file {outfile} already exists")


if __name__ == "__main__":
    build_ui(replace=True)
