from prefab_classes.compiled import prefab_compiler

with prefab_compiler():
    from .keyboard_fixer import Hotkey, read_hotkey, hotkey_or_none
