try:
    from .build.main_window import Ui_MainWindow
    from .build.settings import Ui_Settings
except ImportError as e:
    raise FileNotFoundError(
        "Dialog files could not be found, Ui files need to be rebuilt."
    )
