from typing import override

from PySide6 import QtWidgets, QtGui

from structs.field import (
    TextInputField,
    IntermediateSentinel,
)

class TextFieldValidator(QtGui.QValidator):
    def __init__(self, field: TextInputField) -> None:
        super().__init__()

        self.field = field

    @override
    def validate(self, input: str, pos: int) -> QtGui.QValidator.State:
        match self.field.parse(input):
            case None:
                return QtGui.QValidator.State.Invalid
            case IntermediateSentinel.VAL:
                return QtGui.QValidator.State.Intermediate
            case _:
                return QtGui.QValidator.State.Acceptable


class TextFieldEdit(QtWidgets.QLineEdit):
    def __init__(
        self, field: TextInputField, save_button: QtWidgets.QPushButton
    ) -> None:
        super().__init__()

        self.save_button = save_button

        self.setValidator(TextFieldValidator(field))
        self.setText(str(field.value))

        self.textChanged.connect(self.check_state)

    def check_state(self, text: str) -> None:
        result = self.validator().validate(text, 0)
        if result == QtGui.QValidator.State.Acceptable:
            self.save_button.setEnabled(True)
            color = QtGui.QColor(255, 255, 255)
        else:
            self.save_button.setEnabled(False)
            color = QtGui.QColor(255, 100, 100)
        p = self.palette()
        p.setColor(QtGui.QPalette.ColorRole.Base, color)
        self.setPalette(p)


class DropDownEdit(QtWidgets.QComboBox):
    def __init__(self, items: list[str], selected: int) -> None:
        super().__init__()

        self.addItems(items)
        self.setCurrentIndex(selected)
