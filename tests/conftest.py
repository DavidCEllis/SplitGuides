import sys
from pathlib import Path

import pytest

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


@pytest.fixture(scope="function")
def clear_settings():
    delete_settings_file()
    yield
    delete_settings_file()
