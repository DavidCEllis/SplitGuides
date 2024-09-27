import sys
from subprocess import run
from pathlib import Path

from ducktools.env.environment_specs import EnvironmentSpec

import splitguides

desktop_script = Path(__file__).parent / "splitguides_desktop.py"
server_script = Path(__file__).parent / "splitguides_server.py"

lockfile_name = f"splitguides_v{splitguides.__version__}.lock"
lockfile_path = Path(__file__).parent / lockfile_name

desktop_spec = EnvironmentSpec.from_script(str(desktop_script))
server_spec = EnvironmentSpec.from_script(str(server_script))

if desktop_spec.details != server_spec.details:
    print("Desktop spec does not match server spec! Exiting.")
    sys.exit()


print("Building lockfile")
run(
    [
        sys.executable,
        "-m",
        "ducktools.env",
        "generate_lock",
        str(desktop_script),
        "--output",
        str(lockfile_path),
    ],
    check=True,
)
