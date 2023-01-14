from prefab_classes.compiled import prefab_compiler

with prefab_compiler():
    from .settings import Settings
    from .settings import (
        settings_file, default_template_folder, default_static_folder
    )
