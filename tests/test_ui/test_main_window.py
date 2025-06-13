from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from splitguides.ui.main_window import MainWindow
from splitguides.note_parser import Notes


# Default settings for each test
pytestmark = pytest.mark.usefixtures("clear_settings")


@pytest.fixture(scope="function")
def fake_link():
    with patch("splitguides.ui.main_window.LivesplitLink") as fake_link:
        yield fake_link


def test_init_link(qtbot, fake_link):
    fake_link_instance = MagicMock()
    fake_link.return_value = fake_link_instance

    main_window = MainWindow()
    qtbot.add_widget(main_window)

    assert main_window.ui.statusbar.currentMessage() == "Not connected to server."

    fake_link.assert_called_with(main_window.client, main_window)
    fake_link_instance.start_loops.assert_called_once()


@pytest.mark.xfail(
    raises=AssertionError,
    reason="Possibly a Qt Bug - https://bugreports.qt.io/browse/QTBUG-52552",
)
def test_rc_menu_open(qtbot, fake_link):
    """Test the right click context menu works"""
    with patch.object(MainWindow, "show_menu") as mock_method:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        # Simulate a right click
        qtbot.mouseClick(
            main_window.ui.notes,
            QtCore.Qt.RightButton,
            pos=main_window.ui.notes.rect().center(),
        )

        mock_method.assert_called_once()


def test_toggle_on_top(qtbot, fake_link):
    """Check the 'on top' toggle menu switches on and off correctly"""
    with patch.object(MainWindow, "show") as fake_show:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        on_top = main_window.settings.on_top
        assert on_top is False  # Default Settinng

        # Toggle On
        main_window.toggle_on_top()
        # Check settings have changed
        assert main_window.settings.on_top is True

        # Check menu item checked matches setting
        assert main_window.menu_on_top.isChecked() is True

        # Check window flag has been set
        # noinspection PyUnresolvedReferences
        assert bool(main_window.windowFlags() & QtCore.Qt.WindowStaysOnTopHint) is True

        # Check window shown
        fake_show.assert_called_once()
        fake_show.reset_mock()

        # Toggle Back
        main_window.toggle_on_top()
        # Check settings have reverted
        assert main_window.settings.on_top is False

        # Check menu item checked matches setting
        assert main_window.menu_on_top.isChecked() is False

        # Check window flag has been set
        # noinspection PyUnresolvedReferences
        assert bool(main_window.windowFlags() & QtCore.Qt.WindowStaysOnTopHint) is False

        # Check window shown again
        fake_show.assert_called_once()


def test_resize_stored(qtbot, fake_link):
    """Check the new size is stored in settings when a window is resized."""
    main_window = MainWindow()
    qtbot.add_widget(main_window)

    assert main_window.settings.width == 800
    assert main_window.settings.height == 800

    oldsize = QtCore.QSize(800, 800)
    newsize = QtCore.QSize(1000, 1000)
    resize_event = QtGui.QResizeEvent(oldsize, newsize)

    # Resize doesn't send the event and sending the event doesn't resize :/
    main_window.resize(newsize)
    QtCore.QCoreApplication.sendEvent(main_window, resize_event)

    assert main_window.settings.width == 1000
    assert main_window.settings.height == 1000


def test_blank_notes_called(qtbot, fake_link):
    """Test the blank note message is present."""
    with patch.object(MainWindow, "render_blank") as blank_render:

        main_window = MainWindow()
        qtbot.add_widget(main_window)

        blank_render.assert_called_once()


def test_blank_notes_render(qtbot, fake_link):
    main_window = MainWindow()
    qtbot.add_widget(main_window)

    note_mock = MagicMock()
    main_window.ui.notes = note_mock

    main_window.render_blank()

    assert "<h1>Right Click to Load Notes</h1>" in note_mock.setHtml.call_args[0][0]


# fmt: off
def test_open_notes(qtbot, fake_link):
    """Test notes are opened correctly when a file is given"""
    # Black likes to make multiple with statements unreadable
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName") as mock_filedialog, \
            patch.object(Notes, "from_file") as mock_notes, \
            patch.object(MainWindow, "update_notes") as mock_update_notes:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        fake_notes = Notes(StringIO("Fake Notes\nAre Here\n\nSplit 2"))

        original_folder = main_window.settings.notes_folder
        fake_folder = Path("fake/folder")
        fake_file = str(fake_folder / "mock_notes.txt")

        mock_filedialog.return_value = (fake_file, "Note Files (*.txt *.md *.html)")
        mock_notes.return_value = fake_notes

        main_window.open_notes()

        mock_filedialog.assert_called_once_with(
            main_window,
            "Open Notes",
            original_folder,
            "Note Files (*.txt *.md *.html);;All Files (*.*)",
        )

        mock_notes.assert_called_once_with(fake_file, separator="")

        assert main_window.settings.notes_folder == str(fake_folder)

        mock_update_notes.assert_called_once_with(idx=0, refresh=True)
# fmt: on


# fmt: off
def test_no_notes(qtbot, fake_link):
    """Test that notes are not read if no file is given"""
    with patch.object(
        QtWidgets.QFileDialog, "getOpenFileName"
    ) as mock_filedialog, patch.object(Notes, "from_file") as mock_notes:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        mock_filedialog.return_value = (None, "Note Files (*.txt *.md)")

        main_window.open_notes()

        mock_notes.assert_not_called()


# fmt: on


@pytest.mark.parametrize("idx", [-10, 0, 10, 20])
def test_update_notes(qtbot, fake_link, idx):
    """Test the update method renders as expected"""
    main_window = MainWindow()
    qtbot.add_widget(main_window)

    main_window.settings.previous_splits = 0
    main_window.settings.next_splits = 2

    fake_notes = MagicMock(main_window.notes)
    fake_template = MagicMock(main_window.template)
    fake_note_ui = MagicMock(main_window.ui.notes)

    main_window.notes = fake_notes
    main_window.template = fake_template
    main_window.ui.notes = fake_note_ui
    main_window.notefile = "Notes_URL"

    fake_notes.render_splits.return_value = "Fake Splits"
    fake_template.render.return_value = "Fake HTML"

    main_window.update_notes(idx, refresh=True)

    used_idx = max(idx, 0)

    fake_notes.render_splits.assert_called_once_with(used_idx - 0, used_idx + 3)
    fake_template.render.assert_called_once_with(
        font_size=main_window.settings.font_size,
        font_color=main_window.settings.font_color,
        bg_color="transparent",
        css=main_window.css,
        notes="Fake Splits",
    )
    fake_note_ui.setHtml.assert_called_once_with("Fake HTML", baseUrl="Notes_URL")

    assert main_window.split_index == used_idx


# fmt: off
def test_open_settings(qtbot, fake_link):
    fake_link_inst = MagicMock()
    fake_link.return_value = fake_link_inst

    with patch("splitguides.ui.main_window.SettingsDialog") as fake_settings_dialog_cls, \
            patch.object(Notes, "from_file") as mock_notes:
        # Mock setup
        fake_settings_dialog = MagicMock()
        fake_settings_dialog_cls.return_value = fake_settings_dialog

        fake_settings_dialog.exec.return_value = 1

        main_window = MainWindow()
        qtbot.add_widget(main_window)

        fake_link.assert_called_once_with(main_window.client, main_window)

        # Change hostname to trigger reconnect
        main_window.settings.hostname = "newhost"

        # Change separator to /split
        main_window.settings.split_separator = "/split"
        main_window.notefile = "fake_file"
        main_window.split_index = 2

        assert main_window.client.connection.server != main_window.settings.hostname

        main_window.open_settings()

        fake_settings_dialog.setWindowIcon.assert_called_once_with(main_window.icon)
        fake_settings_dialog.exec.assert_called_once()

        fake_link_inst.close.assert_called_once()
        fake_link.assert_called_with(main_window.client, main_window)
        assert fake_link_inst.start_loops.call_count == 2

        mock_notes.assert_called_once_with("fake_file", separator="/split")

# fmt: on
