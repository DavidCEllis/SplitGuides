import sys
from pathlib import Path

import pytest

from splitguides.settings import DESKTOP_SETTINGS_FILE

src_folder = Path("./src").resolve()
sys.path.insert(0, str(src_folder))


@pytest.fixture(scope="function")
def clear_settings():
    DESKTOP_SETTINGS_FILE.unlink(missing_ok=True)
    yield
    DESKTOP_SETTINGS_FILE.unlink(missing_ok=True)
