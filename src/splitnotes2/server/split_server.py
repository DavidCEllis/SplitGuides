import random
import secrets
import socket
import string
import time
from pathlib import Path

from flask import Flask, render_template, Response
from PySide2.QtWidgets import QApplication, QFileDialog

from splitnotes2.settings import Settings
from splitnotes2.livesplit_client import get_client
from splitnotes2.note_parser import Notes

KEEP_ALIVE = 10

template_folder = str(Path(__file__).parent / "templates")
static_folder = str(Path(__file__).parent / "static")

app = Flask("splitnotes2", template_folder=template_folder, static_folder=static_folder)

notefile = None
notes = None

settings = Settings.load()

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
    return render_template("index.html", notefile=notefile.stem)


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

        while True:
            if connected:
                now = time.time()
                try:
                    new_index = max(client.get_split_index(), 0)
                except (ConnectionError, TimeoutError):
                    connected = client.connect()
                    yield "data: <h1>Trying to connect to livesplit.</h1>\n\n"
                else:
                    if current_note_index != new_index:
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
                connected = client.connect()
                yield "data: <h1>Trying to connect to livesplit.</h1>\n\n"
            time.sleep(0.5)

    return Response(event_stream(), mimetype="text/event-stream")


def get_filename():
    temp_app = QApplication()

    filepath, _ = QFileDialog.getOpenFileName(
        None,
        "Open Notes",
        settings.notes_folder,
        "Note Files (*.txt *.md);;All Files (*.*)",
    )

    temp_app.quit()

    filepath = Path(filepath)
    return filepath


def launch():
    global notes, notefile
    notefile = get_filename()
    settings.notes_folder = str(Path(notefile).parent)
    settings.save()
    notes = Notes.from_file(notefile)

    hostname = socket.gethostname()
    port = 14250

    print(f"Connect a browser to http://{hostname}:{port}/")

    app.run(threaded=True, host=hostname, port=port)


if __name__ == "__main__":
    launch()
