try:
    from .build.main_window import Ui_MainWindow
    from .build.settings import Ui_Settings
    from .build.server_settings import Ui_ServerSettings
except ImportError:
    raise FileNotFoundError(
        "Dialog files could not be found, Ui files need to be rebuilt."
    )
