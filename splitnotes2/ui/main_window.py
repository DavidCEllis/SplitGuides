from PySide2 import QtCore, QtWidgets
from PySide2.QtUiTools import QUiLoader

QFile = QtCore.QFile

main_ui_file = QFile("main_window.ui")


class MainWindow:
    def __init__(self):
        super().__init__()
        main_ui_file.open(QFile.ReadOnly)
        try:
            loader = QUiLoader()
            self.ui = loader.load(main_ui_file)
        finally:
            main_ui_file.close()

    def show(self):
        self.ui.show()

