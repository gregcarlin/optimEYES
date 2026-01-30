from abc import ABC, abstractmethod
from functools import partial
from typing import override

from PySide6 import QtCore, QtWidgets

from structs.project import Project
from gui.common import AbstractQWidgetMeta


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
