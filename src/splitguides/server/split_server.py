import random
import secrets
import string
import time
from pathlib import Path

from flask import Flask, render_template, Response
from PySide6.QtWidgets import QApplication, QFileDialog

from ..settings import Settings
from ..livesplit_client import get_client
from ..note_parser import Notes

KEEP_ALIVE = 10

settings = Settings.load()

template_folder = str(Path(__file__).parent / "templates")
static_folder = str(Path(__file__).parent / "static")

app = Flask(
    "splitguides",
    template_folder=settings.server_template_folder,
    static_folder=settings.server_static_folder,
)

notefile = None
notes = None

app.secret_key = "".join(
    secrets.choice(string.printable) for _ in range(random.randint(30, 40))
)


# noinspection PyUnresolvedReferences
@app.route("/")
def notes_page():
    """
    Render the basic page as index.
    :return:
    """
    global notefile
    return render_template(settings.server_html_template_file, notefile=notefile.stem)


@app.route("/splits")
def split():
    """
    Server-sent events handler
    :return: server-sent events
    """

    def event_stream():
        """
        Handle the stream of note updates, when the note index changes - push the update
        otherwise just keep alive every 10s.
        """
        current_note_index = None
        last_update = 0
        client = get_client(settings.hostname, settings.port)
        connected = client.connect()
        # Note if the previous state was not connected
        disconnected = True
        # Define empty data, used to display the last notes even if disconnected
        data = ""

        while True:
            if connected:
                now = time.time()
                try:
                    new_index = max(client.get_split_index(), 0)
                except (ConnectionError, TimeoutError):
                    connected = client.connect()
                    yield (
                        f"data: <h2>Trying to connect to livesplit.</h2>"
                        f"<h3>Make sure Livesplit server is running.</h3>{data}\n\n"
                    )
                else:
                    if current_note_index != new_index or disconnected:
                        disconnected = False

                        last_update = now
                        current_note_index = new_index
                        split_text = notes.render_splits(
                            new_index - settings.server_previous_splits,
                            new_index + settings.server_next_splits + 1,
                        )
                        if len(split_text) > 0:
                            # Remove newlines from the notes as they break the send
                            data = split_text[0].replace("\n", "")
                            yield f"data: {data}\n\n"
                        else:
                            yield f"data: End of Notes.\n\n"
                    elif now - last_update > KEEP_ALIVE:
                        last_update = now
                        yield ":No update, keep connection\n\n"
            else:
                disconnected = True
                connected = client.connect()
                yield (
                    f"data: <h2>Trying to connect to livesplit.</h2>"
                    f"<h3>Make sure Livesplit server is running.</h3>{data}\n\n"
                )
            time.sleep(0.5)

    return Response(event_stream(), mimetype="text/event-stream")


def get_notes():
    global notes, notefile
    temp_app = QApplication()

    filepath, _ = QFileDialog.getOpenFileName(
        None,
        "Open Notes",
        settings.notes_folder,
        "Note Files (*.txt *.md);;All Files (*.*)",
    )

    temp_app.quit()

    notefile = Path(filepath)
    notes = Notes.from_file(notefile, settings.split_separator)

    settings.notes_folder = str(notefile.parent)
    settings.save()
