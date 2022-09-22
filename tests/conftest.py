import sys
from pathlib import Path

import pytest

from splitguides.settings import settings_file

src_folder = Path("./src").resolve()
sys.path.insert(0, str(src_folder))


@pytest.fixture(scope="function")
def clear_settings():
    settings_file.unlink(missing_ok=True)
    yield
    settings_file.unlink(missing_ok=True)
