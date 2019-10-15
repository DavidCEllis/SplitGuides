# A lot of staring at pyside2-uic source so I can just build the
# ui files without leaving python

from pathlib import Path

from pyside2uic.driver import Driver
from pyside2uic.port_v3.invoke import invoke


class Options:
    def __init__(self, options):
        self._options = options

    def __getattr__(self, key):
        return self._options[key]


def build_ui():

    root = Path(__file__).parent
    ui_files = root.glob('*.ui')

    Path(root / 'build').mkdir(exist_ok=True)
    Path(root / 'build' / '__init__.py').touch(exist_ok=True)

    print("Building user interface files.")

    for infile in ui_files:

        outfile = root / 'build' / infile.with_suffix('.py').name
        options_dict = {
            'output': str(outfile),
            'execute': False,
            'preview': False,
            'debug': False,
            'indent': 4,
            'from_imports': False
        }

        # Usually the options are parsed by optparse which makes an object
        options = Options(options_dict)
        arguments = str(infile)

        # Generate the .py file
        invoke(Driver(options, arguments))

        print(f'Read: {infile}\nBuilt: {outfile}\n')


if __name__ == '__main__':
    build_ui()
