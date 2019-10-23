import sys
from pathlib import Path

src_folder = Path("./src").resolve()
sys.path.insert(0, str(src_folder))


def delete_settings_file():
    """
    Delete any existing settings file to ensure test consistency
    """
    settings_files = src_folder.glob("**/settings.json")
    for f in settings_files:
        try:
            f.unlink()
        except FileNotFoundError:
            pass


delete_settings_file()
