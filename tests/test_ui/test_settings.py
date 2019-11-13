from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QTimer

from splitnotes2.ui.settings import Settings, SettingsDialog, settings_file

test_settings = Path(__file__).parent / "settings.json"


# Default settings for each test
pytestmark = pytest.mark.usefixtures("clear_settings")


class TestSettings:
    # Test the Settings class
    def test_settings_with_file(self):
        """Check settings are read and updated from a settings file"""
        assert not settings_file.exists()  # Check there is no settings file

        settings_file.write_text(test_settings.read_text())

        s = Settings()

        assert s.hostname == "fakehost"
        assert s.port == 12345
        assert s.split_separator == "/split"
        assert s.previous_splits == 1
        assert s.next_splits == 3
        assert s.font_size == 22
        assert s.font_color == "#000001"
        assert s.background_color == "#f1f8f1"
        assert s.full_template_path == Path("fake/html/folder/fakehtml.html")
        assert s.full_css_path == Path("fake/css/folder/fakecss.css")
        assert s.on_top
        assert s.width == 1000
        assert s.height == 1100
        assert s.notes_folder == "fake/documents/folder"

        settings_file.unlink()  # Delete our fake settings file

    def test_failed_getattr(self):
        s = Settings()

        with pytest.raises(AttributeError) as err:
            _ = s.fake_attribute

        assert str(err.value) == "Settings has no attribute 'fake_attribute'"


class TestSettingsUI:
    def test_settings_ui_basic(self, qtbot):
        settings = Settings()
        settings_dialog = SettingsDialog(parent=None, settings=settings)

        qtbot.add_widget(settings_dialog)

        qtbot.mouseDClick(settings_dialog.ui.hostname_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.hostname_edit, "TestHost")

        qtbot.mouseDClick(settings_dialog.ui.port_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.port_edit, "2112")

        qtbot.mouseDClick(settings_dialog.ui.previous_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.previous_edit, "1")

        qtbot.mouseDClick(settings_dialog.ui.advance_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.advance_edit, "3")

        qtbot.mouseDClick(settings_dialog.ui.separator_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.separator_edit, "/split")

        qtbot.mouseDClick(settings_dialog.ui.fontsize_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.fontsize_edit, "25")

        qtbot.mouseDClick(settings_dialog.ui.textcolor_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.textcolor_edit, "#BBBBBB")

        qtbot.mouseDClick(settings_dialog.ui.bgcolor_edit, Qt.LeftButton)
        qtbot.keyClicks(settings_dialog.ui.bgcolor_edit, "#AAAAAA")

        button = settings_dialog.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)

        QTimer.singleShot(0, button.clicked)
        settings_dialog.exec_()

        assert settings_dialog.result() == 1

        settings_dialog.store_settings()

        assert settings.hostname == "TestHost"
        assert settings.port == 2112
        assert settings.previous_splits == 1
        assert settings.next_splits == 3
        assert settings.split_separator == "/split"
        assert settings.font_size == 25
        assert settings.font_color == "#BBBBBB"
        assert settings.background_color == "#AAAAAA"
