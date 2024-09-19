# /// script
# requires-python = "~=3.12"
# dependencies = [
#     "pyside6~=6.7",
#     "jinja2~=3.1",
#     "bleach[css]==6.0",
#     "flask~=3.0",
#     "markdown~=3.6",
#     "keyboard~=0.13.5",
#     "ducktools-classbuilder>=0.7.2",
#     "waitress~=3.0",
#     "ducktools-env>=0.1.2",
# ]
#
# [tool.ducktools.env.app]
# name = "splitguides"
# owner = "davidcellis"
# version = "0.9.1"
#
# [tool.ducktools.env.include]
# data = ["../src/splitguides", "../resources"]
#
# ///

import sys
import runpy

# Tool to extract splitguides
from ducktools.env.bundled_data import get_data_folder


def main():
    with get_data_folder() as bundled_data:
        sys.path.insert(0, bundled_data)
        runpy.run_module("splitguides.server", run_name="__main__")


if __name__ == "__main__":
    main()
