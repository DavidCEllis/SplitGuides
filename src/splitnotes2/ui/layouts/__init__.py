try:
    from .build.main_window import Ui_MainWindow
    from .build.settings import Ui_Settings
except ImportError:
    from .build_ui import build_ui
    build_ui()

    try:
        from .build.main_window import Ui_MainWindow
        from .build.settings import Ui_Settings
    except ImportError:
        raise FileNotFoundError(
            "Dialog files could not be found, Ui files need to be rebuilt."
        )
