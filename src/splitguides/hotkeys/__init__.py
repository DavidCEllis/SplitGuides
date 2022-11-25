from prefab_classes import prefab_compiler

with prefab_compiler():
    from .keyboard_fixer import Hotkey, read_hotkey, hotkey_or_none
