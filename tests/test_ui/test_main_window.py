from unittest.mock import patch, MagicMock

import pytest
from PySide2 import QtCore

from splitnotes2.ui.main_window import MainWindow


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
    with patch.object(MainWindow, "show") as fake_show:
        main_window = MainWindow()
        qtbot.add_widget(main_window)

        on_top = main_window.settings.on_top
        assert on_top is False  # Default Settinng

        # Toggle On
        main_window.toggle_on_top()
        # Check settings have changed
        assert main_window.settings.on_top is not on_top

        # Check menu item checked matches setting
        assert main_window.menu_on_top.isChecked() is main_window.settings.on_top

        # Check window flag has been set
        # noinspection PyUnresolvedReferences
        assert (
            bool(main_window.windowFlags() & QtCore.Qt.WindowStaysOnTopHint)
            is main_window.settings.on_top
        )

        # Check window shown
        fake_show.assert_called_once()
        fake_show.reset_mock()

        # Toggle Back
        main_window.toggle_on_top()
        # Check settings have reverted
        assert main_window.settings.on_top is on_top

        # Check menu item checked matches setting
        assert main_window.menu_on_top.isChecked() is main_window.settings.on_top

        # Check window flag has been set
        # noinspection PyUnresolvedReferences
        assert (
            bool(main_window.windowFlags() & QtCore.Qt.WindowStaysOnTopHint)
            is main_window.settings.on_top
        )

        # Check window shown again
        fake_show.assert_called_once()
