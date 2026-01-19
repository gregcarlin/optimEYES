import sys
from PySide6 import QtCore, QtWidgets, QtGui
from cli import main as cli_main


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello world", alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText("loading num...")
        solution = cli_main()[0]
        v = solution.solution.get_objective_value()
        self.text.setText(f"the num is: {v}")


def main() -> int:
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
