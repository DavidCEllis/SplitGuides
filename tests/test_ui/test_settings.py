from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PySide2 import QtWidgets, QtGui
from PySide2.QtCore import Qt, QTimer

from splitnotes2.settings import Settings, settings_file
from splitnotes2.ui.settings_ui import SettingsDialog

test_settings = Path(__file__).parent / "settings.json"


# Default settings for each test
pytestmark = pytest.mark.usefixtures("clear_settings")


@pytest.fixture
def settings_ui(qtbot):
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

    return settings, settings_dialog


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
    def test_settings_ui_basic(self, qtbot, settings_ui):
        settings, settings_dialog = settings_ui

        button = settings_dialog.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)

        QTimer.singleShot(0, button.clicked)
        result = settings_dialog.exec_()

        assert result == 1

        assert settings.hostname == "TestHost"
        assert settings.port == 2112
        assert settings.previous_splits == 1
        assert settings.next_splits == 3
        assert settings.split_separator == "/split"
        assert settings.font_size == 25
        assert settings.font_color == "#BBBBBB"
        assert settings.background_color == "#AAAAAA"

    def test_settings_ui_cancel(self, qtbot, settings_ui):
        settings, settings_dialog = settings_ui
        button = settings_dialog.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)

        QTimer.singleShot(0, button.clicked)
        result = settings_dialog.exec_()

        assert result == 0

        assert settings.hostname == Settings.defaults["hostname"]
        assert settings.port == Settings.defaults["port"]
        assert settings.previous_splits == Settings.defaults["previous_splits"]
        assert settings.next_splits == Settings.defaults["next_splits"]
        assert settings.split_separator == Settings.defaults["split_separator"]
        assert settings.font_size == Settings.defaults["font_size"]
        assert settings.font_color == Settings.defaults["font_color"]
        assert settings.background_color == Settings.defaults["background_color"]

    def test_settings_ui_colorpicker_font(self, qtbot):
        """
        Test font color picker
        """
        settings = Settings()
        settings_dialog = SettingsDialog(parent=None, settings=settings)

        qtbot.add_widget(settings_dialog)

        with patch.object(QtWidgets.QColorDialog, "getColor") as mock:
            fake_color = MagicMock()
            fake_color.isValid.return_value = True
            fake_color.name.return_value = "#012345"

            mock.return_value = fake_color

            qtbot.mouseClick(settings_dialog.ui.textcolor_button, Qt.LeftButton)

            mock.assert_called_with(
                QtGui.QColor(settings.font_color), parent=settings_dialog
            )

        assert settings_dialog.ui.textcolor_edit.text() == "#012345"

    def test_settings_ui_colorpicker_bg(self, qtbot):
        """
        Test BG color picker
        """
        settings = Settings()
        settings_dialog = SettingsDialog(parent=None, settings=settings)

        qtbot.add_widget(settings_dialog)
        with patch.object(QtWidgets.QColorDialog, "getColor") as mock:
            fake_color = MagicMock()
            fake_color.isValid.return_value = True
            fake_color.name.return_value = "#456789"

            mock.return_value = fake_color

            qtbot.mouseClick(settings_dialog.ui.bgcolor_button, Qt.LeftButton)

            mock.assert_called_with(
                QtGui.QColor(settings.background_color), parent=settings_dialog
            )

        assert settings_dialog.ui.bgcolor_edit.text() == "#456789"
