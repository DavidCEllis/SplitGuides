# A lot of staring at pyside2-uic source so I can just build the
# ui files without leaving python

from pathlib import Path

from pyside2uic.driver import Driver
from pyside2uic.port_v3.invoke import invoke


class Options:
    def __init__(self, options):
        self._options = options

    def __getattr__(self, key):
        # For values that aren't set, provide None like optparse
        try:
            return self._options[key]
        except KeyError:
            return None


def build_ui():

    root = Path('.')
    ui_files = root.glob('*.ui')

    for infile in ui_files:
        outfile = infile.parents[1] / 'build' / infile.with_suffix('.py').name
        options_dict = {
            'output': str(outfile),
            'execute': False,
        }

        # Usually the options are parsed by optparse which makes an object
        options = Options(options_dict)
        arguments = str(infile)

        # Generate the .py file
        invoke(Driver(options, arguments))

        print(f'Read: {infile}\nBuilt: {outfile}\n')
