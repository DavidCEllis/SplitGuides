from splitnotes2.server import app, get_notes, settings


def launch():
    get_notes()  # Sets internal 'notes' and 'notefile' variables

    print(
        f"Connect a browser to http://{settings.server_hostname}:{settings.server_port}/"
    )

    app.run(threaded=True, host=settings.server_hostname, port=settings.server_port)


if __name__ == "__main__":
    launch()
