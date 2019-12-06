from splitnotes2.server import app, get_notes, settings
import flask.cli as cli

# Stop flask from giving users an unhelpful warning.
cli.show_server_banner = lambda *x: None


def launch():
    get_notes()  # Sets internal 'notes' and 'notefile' variables

    print(
        "This server version of Splitnotes2 allows you view splitnotes via a browser window "
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
