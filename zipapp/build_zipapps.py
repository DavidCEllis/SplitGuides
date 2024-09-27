import sys
from subprocess import run
from pathlib import Path

import splitguides
from splitguides.build_ui import build_ui

desktop_script = str(Path(__file__).parent / "splitguides_desktop.py")
server_script = str(Path(__file__).parent / "splitguides_server.py")

lockfile_name = f"splitguides_v{splitguides.__version__}.lock"
lockfile_path = Path(__file__).parent / lockfile_name

if not lockfile_path.exists():
    print("LOCKFILE NOT GENERATED FOR THIS VERSION OF SPLITGUIDES - EXITING")
    sys.exit()

# The built UI files *must* be included - should already exist
build_ui(replace=False)

print("Building desktop zipapp")
run(
    [
        sys.executable,
        "-m",
        "ducktools.env",
        "bundle",
        "--with-lock",
        str(lockfile_path),
        str(desktop_script),
    ],
    check=True,
)

print("Building server zipapp")
run(
    [
        sys.executable,
        "-m",
        "ducktools.env",
        "bundle",
        "--with-lock",
        str(lockfile_path),
        str(server_script),
    ],
    check=True,
)
