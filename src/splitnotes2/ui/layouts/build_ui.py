# In v5.14 they removed pyside2uic so this invokes uic directly
from subprocess import run
from pathlib import Path

import PySide2

pyside_folder = Path(PySide2.__file__).parent


def uic(infile, outfile):
    """
    Run the QT User Interface Compiler to convert a .ui file to a .py file

    :param infile: Input path
    :param outfile: Output path
    :return: the CompletedProcess object from running the uic .exe
    """
    exe = pyside_folder / "uic.exe"
    cmd = [exe, "-g", "python", "--o", str(outfile), str(infile)]
    return run(cmd, capture_output=True)


def build_ui():
    """
    Compile any .ui files in this folder to the build folder as .py files
    """
    # Scan this folder for .ui files
    root = Path(__file__).parent
    ui_files = root.glob("*.ui")

    # Make the build and __init__ files if they do not exist
    Path(root / "build").mkdir(exist_ok=True)
    Path(root / "build" / "__init__.py").touch(exist_ok=True)

    print("Building user interface files.")

    for infile in ui_files:
        outfile = root / "build" / infile.with_suffix(".py").name
        result = uic(infile, outfile)

        if result.returncode == 0:
            print(f"Read: {infile}\nBuilt: {outfile}\n")
        else:
            print(f"Failed to convert: code{result.returncode}\n{result.stderr}")


if __name__ == "__main__":
    build_ui()
