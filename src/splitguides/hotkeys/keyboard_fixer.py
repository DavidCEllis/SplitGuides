# COMPILE_PREFABS
"""
The keyboard library does not handle numpad hotkeys correctly.

This is a rewrite of the relevant functions to handle this.
"""

import queue as _queue

from prefab_classes import prefab, attribute
import keyboard


KEY_DOWN = "down"
KEY_UP = "up"


@prefab
class Hotkey:
    scancodes = attribute(default=None)
    name = attribute(default=None)


def hotkey_or_none(keydict):
    return Hotkey(**keydict) if keydict else None


def read_hotkey(suppress=True):
    """
    Modified read_hotkey function to correctly support numpad keys.

    The original function returns just the names, this returns a Hotkey object.
    The scancodes can then be stored while the name can be displayed.
    """

    queue = _queue.Queue()

    # Replace lambda with
    def hook_func(event):
        queue.put(event)
        return event.event_type == KEY_DOWN

    hooked = keyboard.hook(hook_func, suppress=suppress)
    while True:
        keychange = queue.get()
        if keychange.event_type == KEY_UP:
            keyboard.unhook(hooked)
            with keyboard._pressed_events_lock:
                key_events = list(keyboard._pressed_events.values())
                key_events.append(keychange)
                key_codes = [e.scan_code for e in key_events]
                key_string = keyboard.get_hotkey_name([e.name for e in key_events])
            return Hotkey(key_codes, key_string)
