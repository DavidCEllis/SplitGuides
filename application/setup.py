"""
Special setup.py file for building the app
"""

import sys
from pathlib import Path

from cx_Freeze import setup, Executable

python3_dll = str(Path(sys.executable).parent / 'python3.dll')
templates = str(Path(__file__).resolve().parents[1] / 'src' / 'splitnotes2' / 'ui' / 'html')

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit',
        'include_files': [
            python3_dll,
            templates,
        ]
    }
}

executables = [
    Executable('app.py', base=base, targetName='splitnotes2')
]

setup(name='splitnotes2',
      version='0.0.1',
      description='Speedrun splitnotes tool with HTML rendering',
      options=options,
      executables=executables
      )
