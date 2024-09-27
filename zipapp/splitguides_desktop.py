# Splitguides - A tool to display speedrun notes that automatically advance with livesplit
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# /// script
# requires-python = "~=3.12.0"
# dependencies = [
#     "pyside6~=6.7",
#     "jinja2~=3.1",
#     "bleach[css]==6.0",
#     "flask~=3.0",
#     "markdown~=3.6",
#     "keyboard~=0.13.5",
#     "ducktools-classbuilder>=0.7.2",
#     "waitress~=3.0",
#     "ducktools-env>=0.1.3",
# ]
#
# [tool.ducktools.env.app]
# name = "splitguides"
# owner = "davidcellis"
# version = "0.9.1"
#
# [tool.ducktools.env.include]
# data = ["../src/splitguides", "../resources"]
# license = "../COPYING"
# ///

import sys
import runpy

# Tool to extract splitguides
from ducktools.env.bundled_data import get_data_folder


def main():
    with get_data_folder() as bundled_data:
        sys.path.insert(0, bundled_data)
        runpy.run_module("splitguides", run_name="__main__")


if __name__ == "__main__":
    main()
