from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path

import pytest
from PySide2 import QtCore, QtGui, QtWidgets

from splitnotes2.ui.main_window import MainWindow
from splitnotes2.note_parser import Notes


# Default settings for each test
pytestmark = pytest.mark.usefixtures("clear_settings")


@pytest.fixture(scope="function")
def fake_link():
    with patch("splitnotes2.ui.main_window.LivesplitLink") as fake_link:
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
    reason="Possibly a Qt Bug - https://bugreports.qt.io/browse/QTBUG-52552"
)
def test_rc_menu_open(qtbot, fake_link):
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


def test_open_notes(qtbot, fake_link):
    with patch.object(
        QtWidgets.QFileDialog, "getOpenFileName"
    ) as mock_filedialog, patch.object(Notes, "from_file") as mock_notes, patch.object(
        MainWindow, "update_notes"
    ) as mock_update_notes:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        fake_notes = Notes(StringIO("Fake Notes\nAre Here\n\nSplit 2"))

        original_folder = main_window.settings.notes_folder
        fake_folder = Path("fake/folder")
        fake_file = str(fake_folder / "mock_notes.txt")

        mock_filedialog.return_value = (fake_file, "Note Files (*.txt *.md)")
        mock_notes.return_value = fake_notes

        main_window.open_notes()

        mock_filedialog.assert_called_once_with(
            main_window,
            "Open Notes",
            original_folder,
            "Note Files (*.txt *.md);;All Files (*.*)",
        )

        mock_notes.assert_called_once_with(fake_file, separator="")

        assert main_window.settings.notes_folder == str(fake_folder)

        mock_update_notes.assert_called_once_with(idx=0, refresh=True)
