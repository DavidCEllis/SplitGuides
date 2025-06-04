# This file exists to make sure the UI files are built
import sys
from pathlib import Path
from subprocess import run

from setuptools import setup

if __name__ == "__main__":
    path_to_build = str(Path(__file__).parent / "src" / "splitguides" / "build_ui.py")
    cmd = [sys.executable, path_to_build]

    result = run(cmd, check=True)

    setup()
