from abc import ABC, abstractmethod
from functools import partial
from typing import override, Any

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project
from structs.field import (
    Field,
    OptionField,
    TextInputField,
    WeekdayListField,
    FileField,
    DictIntIntField,
)
from gui.common import AbstractQWidgetMeta, BinaryMessage, clear_layout
from gui.field import TextFieldEdit, DropDownEdit, WeekdayListEdit, FileEdit, DictIntIntEdit


class TableWidget(QtWidgets.QTableWidget, ABC, metaclass=AbstractQWidgetMeta):
    def __init__(self, project: Project, rows: int, buttons: int) -> None:
        super().__init__()

        self.project = project

        self.setRowCount(rows)
        self.setColumnCount(buttons + 1)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        for i in range(buttons):
            self.setColumnWidth(i + 1, 50)

        self.edit_widget = None

    @override
    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(400, 600)

    def setRow(self, index: int, label: str, editable: bool) -> None:
        text = QtWidgets.QLabel(label)
        text.setMargin(5)
        text.setWordWrap(True)
        self.setCellWidget(index, 0, text)
        if editable:
            edit_button = QtWidgets.QPushButton("Edit")
            edit_button.setFixedHeight(40)
            edit_button.clicked.connect(partial(self.edit_clicked, index=index))
            self.setCellWidget(index, 1, edit_button)
        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.setFixedHeight(40)
        delete_button.clicked.connect(partial(self.delete_clicked, index=index))
        self.setCellWidget(index, 2, delete_button)

    @abstractmethod
    def edit_clicked(self, index: int) -> None:
        pass

    @abstractmethod
    def delete_clicked(self, index: int) -> None:
        pass


class SectionHeaderWidget(QtWidgets.QWidget, ABC, metaclass=AbstractQWidgetMeta):
    def __init__(self, label: str) -> None:
        super().__init__()

        label_widget = QtWidgets.QLabel(
            label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )
        label_widget.setContentsMargins(0, 4, 0, 0)
        new_button = QtWidgets.QPushButton("+")
        new_button.setFixedWidth(20)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(label_widget)
        layout.addWidget(new_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        new_button.clicked.connect(self.add_new_clicked)

    @QtCore.Slot()
    @abstractmethod
    def add_new_clicked(self):
        pass


Editor = DropDownEdit | TextFieldEdit | WeekdayListEdit | FileEdit | DictIntIntEdit


class AddOrEditWidget(QtWidgets.QWidget, ABC, metaclass=AbstractQWidgetMeta):
    def __init__(self, root: QtWidgets.QWidget, prefix_fields: int = 0) -> None:
        super().__init__()

        self.root = root
        self.prefix_fields = prefix_fields

        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self._layout = QtWidgets.QGridLayout(self)

        self.field_widgets: list[Editor] = []

    def populate_fields(self) -> None:
        clear_layout(self._layout, start_index=self.prefix_fields)
        self.field_widgets: list[Editor] = []
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_clicked)

        fields = self.get_current_fields()
        for i, field in enumerate(fields):
            label = QtWidgets.QLabel(field.name)
            self._layout.addWidget(label, self.prefix_fields + i, 0)
            match field:
                case OptionField():
                    edit = DropDownEdit(
                        field.allowed_value_labels(),
                        field.allowed_values.index(field.value),
                    )
                case TextInputField():
                    edit = TextFieldEdit(field, self.save_button)
                case WeekdayListField():
                    edit = WeekdayListEdit(field, self.save_button)
                case FileField():
                    edit = FileEdit(field.value)
                case DictIntIntField():
                    edit = DictIntIntEdit(field.value, field.key_label, field.value_label)
                case _:
                    raise ValueError(f"Unknown field type: {field}")
            self._layout.addWidget(edit, self.prefix_fields + i, 1)
            self.field_widgets.append(edit)

        self._layout.addWidget(
            self.save_button, self.prefix_fields + len(fields), 0, 1, 2
        )

    @staticmethod
    def _rebuild_field(
        field: Field, widget: Editor
    ) -> OptionField | TextInputField | WeekdayListField | FileField | DictIntIntField:
        if isinstance(field, OptionField):
            assert isinstance(widget, DropDownEdit)
            return field.parse(widget.currentIndex())
        elif isinstance(field, TextInputField):
            assert isinstance(widget, TextFieldEdit)
            new_field = field.parse(widget.text())
            assert isinstance(new_field, TextInputField)
            return new_field
        elif isinstance(field, WeekdayListField):
            assert isinstance(widget, WeekdayListEdit)
            return field.parse([box.isChecked() for box in widget.checkboxes])
        elif isinstance(field, FileField):
            assert isinstance(widget, FileEdit)
            return FileField(widget.path, field.name)
        elif isinstance(field, DictIntIntField):
            assert isinstance(widget, DictIntIntEdit)
            return field.parse(widget.get_data())
        else:
            raise ValueError(f"Unsupported field type: {type(field)}")

    def _rebuild_fields(self) -> tuple[Any, ...]:
        old_fields = self.get_current_fields()
        return tuple(
            AddOrEditWidget._rebuild_field(old_field, widget)
            for old_field, widget in zip(old_fields, self.field_widgets)
        )

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        old_fields = self.get_current_fields()
        try:
            new_fields = self._rebuild_fields()
        except AssertionError:
            # Fields are dirty, and invalid
            new_fields = None
        if new_fields == old_fields:
            # Fields are unchanged, close
            self.root.setEnabled(True)
            event.accept()
        else:
            message = BinaryMessage("Discard unsaved changes?", self)
            result = message.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Discard:
                self.root.setEnabled(True)
                event.accept()
            else:
                event.ignore()

    @abstractmethod
    def get_current_fields(self) -> tuple[Field, ...]:
        pass

    @abstractmethod
    def save_clicked(self) -> None:
        pass


class AddNewWidget(AddOrEditWidget, ABC, metaclass=AbstractQWidgetMeta):
    def __init__(self, root: QtWidgets.QWidget, items: list[str]) -> None:
        super().__init__(root, prefix_fields=1)

        self.index = 0
        self.selector = QtWidgets.QComboBox()
        self.selector.addItems(items)
        self._layout.addWidget(self.selector, 0, 0, 1, 2)
        self.selector.currentIndexChanged.connect(self.on_change)

        self.populate_fields()

    def on_change(self, index: int) -> None:
        self.index = index
        self.populate_fields()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # Skip check for unsaved fields, just allow user to close
        self.root.setEnabled(True)
        event.accept()
