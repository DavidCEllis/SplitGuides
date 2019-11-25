import random
import secrets
import string
import time
from pathlib import Path

from flask import Flask, render_template, Response
from PySide2.QtWidgets import QFileDialog

from ..settings import Settings
from ..livesplit_client import get_client
from ..note_parser import Notes

KEEP_ALIVE = 10
last_update = 0

template_folder = str(Path(__file__).parent / "templates")
static_folder = str(Path(__file__).parent / "static")

app = Flask("splitnotes2", template_folder=template_folder, static_folder=static_folder)

notes = None
current_note_index = None

settings = Settings()
client = get_client(settings.hostname, settings.port)

app.secret_key = "".join(
    secrets.choice(string.printable) for _ in range(random.randint(30, 40))
)


def make_connection():
    global client

    if client is None:
        client = get_client(settings.hostname, settings.port)

    return client


# noinspection PyUnresolvedReferences
@app.route("/")
def notes_page():
    return render_template("index.html")


@app.route("/splits")
def split():
    def event_stream():
        global current_note_index, last_update
        while True:
            now = time.time()
            new_index = client.get_split_index()
            if current_note_index != new_index:
                current_note_index = new_index
                split_text = notes.render_splits(new_index, new_index + 1)
                last_update = now
                yield f"data: {split_text}\n\n"
            elif now - last_update > KEEP_ALIVE:
                last_update = now
                yield ":No update, keep connection"
            time.sleep(0.5)

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    global notes
    notefile, _ = QFileDialog.getOpenFileName(
        None,
        "Open Notes",
        settings.notes_folder,
        "Note Files (*.txt *.md);;All Files (*.*)",
    )
    settings.notes_folder = str(Path(notefile).parent)
    settings.save()
    # noinspection PyRedeclaration
    notes = Notes(notefile)

    app.run(threaded=True)
