import pytest

from splitguides.settings import DESKTOP_SETTINGS_FILE


@pytest.fixture(scope="function")
def clear_settings():
    # Make a memory copy of the settings file and restore it on completion
    # Should move to not using the actual user settings file location but that will take
    # some digging.

    data = DESKTOP_SETTINGS_FILE.read_text()
    DESKTOP_SETTINGS_FILE.unlink(missing_ok=True)

    try:
        yield
    finally:
        DESKTOP_SETTINGS_FILE.unlink(missing_ok=True)
        DESKTOP_SETTINGS_FILE.write_text(data)
