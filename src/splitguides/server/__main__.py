from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
import waitress

from splitguides.server import app, get_notes, settings
from splitguides.server import split_server

from splitguides.ui.server_settings_ui import ServerSettingsDialog


def launch():
    # Create a base application and main window for the dialogs to use as parent
    qt_app = QApplication()
    main_window = QMainWindow()

    settings_dialog = ServerSettingsDialog(
        parent=main_window,
        settings=settings,
    )

    result = settings_dialog.exec()
    if result == 0:  # Rejected, close without launching server
        print("Settings cancelled, closing application.")
        qt_app.quit()
        return

    success = get_notes(main_window)  # Sets internal 'notes' and 'notefile' variables
    if not success:
        print("No notes file selected, closing application.")
        qt_app.quit()
        return

    print(
        "This server version of SplitGuides allows you view notes via a browser window "
        "and should work across a local network.\n"
        "This is not intended to be used over the internet or on public networks."
    )

    # Access via split_server as this value gets replaced only after get_notes
    assert isinstance(split_server.notefile, Path)  # True due to success of get_notes
    notefolder = Path(split_server.notefile).parent

    print(f"Serving contents of '{notefolder}' for relative links")

    print(
        f"Connect a browser to "
        f"http://{settings.server_hostname}:{settings.server_port}/ "
        f"in order to view the notes."
    )

    print("Press ctrl+c to close the server.")

    try:
        waitress.serve(
            app,
            host=settings.server_hostname,
            port=settings.server_port
        )
    except KeyboardInterrupt:
        print("Interrupt received, closing application.")
    finally:
        qt_app.quit()


if __name__ == "__main__":
    launch()
