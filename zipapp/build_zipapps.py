import sys
from subprocess import run
from pathlib import Path


desktop_script = str(Path(__file__).parent / "splitguides_desktop.py")
server_script = str(Path(__file__).parent / "splitguides_server.py")

print("Building desktop zipapp")
run(
    [sys.executable, "-m", "ducktools.env", "bundle", str(desktop_script)],
    check=True,
)

print("Building server zipapp")
run(
    [sys.executable, "-m", "ducktools.env", "bundle", str(desktop_script)],
    check=True,
)
