"""
Handle the keyboard inputs and the thread waiting

I'm trying to isolate all keyboard module related code here because
I really don't like the design
(some confusing lambdas + all the actual code is in one 1k+ line __init__.py file)
but it's currently better than the alternative of writing a keyboard hook
library myself for this one small task.
"""
import time
import json
from collections.abc import Callable

import keyboard
from PySide6 import QtCore

from ducktools.classbuilder.prefab import as_dict

from ..hotkeys import read_hotkey


class HotkeyManager(QtCore.QObject):
    hotkey_signal = QtCore.Signal(str)
    increase_signal = QtCore.Signal()
    decrease_signal = QtCore.Signal()

    enabled: bool
    increase_key: Callable[[], None] | None
    decrease_key: Callable[[], None] | None

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.enabled = False

        # Connect to the increase_offset and decrease_offset functions
        self.increase_signal.connect(self.parent.increase_offset)
        self.decrease_signal.connect(self.parent.decrease_offset)

        # The keys for unbinding
        self.increase_key = None
        self.decrease_key = None

    def enable_hotkeys(self, increase_key, decrease_key):
        if increase_key:
            self.increase_key = keyboard.add_hotkey(
                tuple(increase_key), self.increase_signal.emit
            )
        if decrease_key:
            self.decrease_key = keyboard.add_hotkey(
                tuple(decrease_key), self.decrease_signal.emit
            )
        self.enabled = True

    def disable_hotkeys(self):
        if self.increase_key:
            keyboard.remove_hotkey(self.increase_key)
        if self.decrease_key:
            keyboard.remove_hotkey(self.decrease_key)
        self.enabled = False

    @staticmethod
    def disable_all():
        """Backup method to just disable everything, used at close"""
        keyboard.unhook_all()

    def select_input(self, return_object):
        """
        Choose a hotkey to be used.
        :param return_object: the function to call back with the hotkey value
        """
        self.hotkey_signal.connect(return_object)

        # Sleep 100ms to allow inputs used to trigger
        # The detection to clear first
        time.sleep(0.1)
        hotkey = read_hotkey(False)

        # Esc, Backspace or Delete can be used to clear the input
        if hotkey.name in ["esc", "backspace", "delete"]:
            hotkey = None  # Blank will be converted to None

        self.hotkey_signal.emit(json.dumps(as_dict(hotkey)))  # Needs to be a string
