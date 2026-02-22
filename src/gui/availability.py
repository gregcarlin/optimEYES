from datetime import timedelta
from typing import override

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project
from structs.resident import Resident
from gui.common import BinaryMessage, ProjectManagerWidget


class AvailabilityWidget(QtWidgets.QWidget):
    def __init__(self, project: Project, parent: ProjectManagerWidget) -> None:
        super().__init__()

        self.project = project
        self.edit_parent = parent

        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            "Set availability for residents here. A partial check (dash) indicates that they're available, but at the VA on a day where we should try to limit them being oncall (if the relevant VA coverage constraints and/or objectives are used)."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        self.table = AvailabilityTableWidget(project)
        layout.addWidget(self.table)

        btn_layout = QtWidgets.QHBoxLayout()
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_clicked)
        btn_layout.addWidget(cancel_button)
        save_button = QtWidgets.QPushButton("Save")
        save_button.setDefault(True)
        save_button.clicked.connect(self.save_clicked)
        btn_layout.addWidget(save_button)
        layout.addLayout(btn_layout)

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        old_data = self.project.availability
        new_data = self.table.get_data()
        if old_data == new_data:
            # Data is unchanged, close
            self.edit_parent.setEnabled(True)
            event.accept()
        else:
            message = BinaryMessage("Discard unsaved changes?", self)
            result = message.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Discard:
                self.edit_parent.setEnabled(True)
                event.accept()
            else:
                event.ignore()

    def save_clicked(self) -> None:
        self.project.availability = self.table.get_data()
        self.edit_parent.update_project(self.project)
        self.close()

    def cancel_clicked(self) -> None:
        self.close()


class AvailabilityTableWidget(QtWidgets.QTableWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()

        self.project = project

        num_days = (
            0
            if project.availability == []
            else len(project.availability[0].availability)
        )

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setRowCount(0 if project.availability == [] else num_days)
        self.setColumnCount(len(project.availability))
        self.setHorizontalHeaderLabels(
            [resident.name for resident in project.availability]
        )
        self.setVerticalHeaderLabels(
            []
            if project.availability == []
            else [
                f"{project.start_date + timedelta(days=i):%a %m-%d}"
                for i in range(num_days)
            ]
        )

        self.checkboxes: dict[str, list[QtWidgets.QCheckBox]] = {}
        for resident_index, resident in enumerate(project.availability):
            self.checkboxes[resident.name] = []
            for day_index, (available, va) in enumerate(
                zip(resident.availability, resident.va)
            ):
                check = QtWidgets.QCheckBox()
                check.setTristate(True)
                if available == 0:
                    check_state = QtCore.Qt.CheckState.Unchecked
                elif va != 0:
                    check_state = QtCore.Qt.CheckState.PartiallyChecked
                else:
                    check_state = QtCore.Qt.CheckState.Checked
                check.setCheckState(check_state)
                self.checkboxes[resident.name].append(check)

                # Magic needed to center check box
                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(widget)
                layout.addWidget(check)
                layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)

                self.setCellWidget(day_index, resident_index, widget)

        # Set all columns to the width of the longest resident's name
        self.resizeColumnsToContents()
        column_width = max(
            self.columnWidth(i) for i in range(len(project.availability))
        )
        for i in range(len(project.availability)):
            self.setColumnWidth(i, column_width)

    @override
    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(500, 600)

    def get_data(self) -> list[Resident]:
        result: list[Resident] = []

        for resident in self.project.availability:
            availability = [
                1 if box.checkState() != QtCore.Qt.CheckState.Unchecked else 0
                for box in self.checkboxes[resident.name]
            ]
            va = [
                1 if box.checkState() == QtCore.Qt.CheckState.PartiallyChecked else 0
                for box in self.checkboxes[resident.name]
            ]
            # TODO add note column for coverage
            new_resident = Resident(
                resident.name, resident.pgy, availability, va, resident.coverage
            )
            result.append(new_resident)

        return result
