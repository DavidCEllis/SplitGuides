from PySide6.QtWidgets import QApplication, QMainWindow
import flask.cli as cli

from splitguides.server import app, get_notes, settings
from splitguides.ui.server_settings_ui import ServerSettingsDialog


# Stop flask from giving users an unhelpful warning.
cli.show_server_banner = lambda *x: None


def launch():
    base_app = QApplication()
    main_window = QMainWindow()

    settings_dialog = ServerSettingsDialog(
        parent=main_window,
        settings=settings,
    )

    result = settings_dialog.exec()

    if result == 0:  # Rejected, close without launching server
        print("Settings cancelled, closing application.")
        return

    get_notes()  # Sets internal 'notes' and 'notefile' variables

    base_app.quit()

    print(
        "This server version of SplitGuides allows you view notes via a browser window "
        "and should work across a local network.\n"
        "It is not intended to be used over the internet and as such is not based on a "
        "production server."
    )

    print(
        f"Connect a browser to http://{settings.server_hostname}:{settings.server_port}/ "
        f"in order to view the notes."
    )

    print(f"This hostname and port can be changed in {settings.output_file} if needed.")

    app.run(threaded=True, host=settings.server_hostname, port=settings.server_port)


if __name__ == "__main__":
    launch()
