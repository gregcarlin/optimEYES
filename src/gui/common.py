from abc import ABC

from PySide6 import QtWidgets

class AbstractQWidgetMeta(type(ABC), type(QtWidgets.QWidget)):
    pass

class AlertMessage(QtWidgets.QMessageBox):
    def __init__(self, text: str, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setText(text)


class BinaryMessage(QtWidgets.QMessageBox):
    def __init__(self, question: str, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setInformativeText(question)
        self.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Cancel
            | QtWidgets.QMessageBox.StandardButton.Discard
        )
        self.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)


def show_alert(message: str, parent: QtWidgets.QWidget) -> None:
    alert = AlertMessage(message, parent)
    alert.show()

def center_on_screen(widget: QtWidgets.QWidget) -> None:
    # Widget must already be visible
    screen_geometry = widget.screen().availableGeometry()
    x = int((screen_geometry.width() - widget.width()) / 2)
    y = int((screen_geometry.height() - widget.height()) / 2)
    widget.move(x, y)

