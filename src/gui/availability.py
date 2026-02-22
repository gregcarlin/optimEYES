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
        old_data = self.project.availability, self.project.coverage
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
        availability, coverage = self.table.get_data()
        self.project.availability = availability
        self.project.coverage = coverage
        self.edit_parent.refresh_project()
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
        self.setColumnCount(len(project.availability) + 1)
        self.setHorizontalHeaderLabels(
            [resident.name for resident in project.availability] + ["Coverage note"]
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

        self.coverages: list[QtWidgets.QLineEdit] = []
        for day_index in range(num_days):
            coverage_edit = QtWidgets.QLineEdit(str(project.coverage[day_index]))
            coverage_edit.setFrame(False)
            coverage_edit.setCursorPosition(0)
            self.setCellWidget(day_index, len(project.availability), coverage_edit)
            self.coverages.append(coverage_edit)

        # Set all columns to the width of the longest resident's name
        self.resizeColumnsToContents()
        column_width = max(
            self.columnWidth(i) for i in range(len(project.availability))
        )
        for i in range(len(project.availability)):
            self.setColumnWidth(i, column_width)
        self.setColumnWidth(len(project.availability), 200)

    @override
    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(700, 600)

    def get_data(self) -> tuple[list[Resident], list[str]]:
        residents: list[Resident] = []

        for resident in self.project.availability:
            availability = [
                1 if box.checkState() != QtCore.Qt.CheckState.Unchecked else 0
                for box in self.checkboxes[resident.name]
            ]
            va = [
                1 if box.checkState() == QtCore.Qt.CheckState.PartiallyChecked else 0
                for box in self.checkboxes[resident.name]
            ]
            new_resident = Resident(resident.name, resident.pgy, availability, va)
            residents.append(new_resident)

        coverage = [widget.text() for widget in self.coverages]

        return residents, coverage
