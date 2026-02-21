from typing import override

from PySide6 import QtWidgets, QtGui

from dateutil import Weekday
from structs.field import (
    TextInputField,
    IntermediateSentinel,
    WeekdayListField,
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


class WeekdayListEdit(QtWidgets.QWidget):
    def __init__(
        self, field: WeekdayListField, save_button: QtWidgets.QPushButton
    ) -> None:
        super().__init__()

        self.save_button = save_button

        layout = QtWidgets.QHBoxLayout(self)
        self.checkboxes = []
        for weekday in Weekday:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(weekday in field.value)
            checkbox.checkStateChanged.connect(self.check_state)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)
            label = QtWidgets.QLabel(weekday.name.capitalize())
            layout.addWidget(label)

    def check_state(self) -> None:
        self.save_button.setEnabled(any(box.isChecked() for box in self.checkboxes))


class FileEditDialog(QtWidgets.QFileDialog):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        self.selectFile(path)


class FileEdit(QtWidgets.QWidget):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.path = path

        layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(path)
        layout.addWidget(self.label)
        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_clicked)
        layout.addWidget(edit_btn)

    def edit_clicked(self) -> None:
        dialog = FileEditDialog(self.path)
        result = dialog.exec()
        if not result:
            return

        self.path = dialog.selectedFiles()[0]
        self.label.setText(self.path)
