from datetime import timedelta
from typing import override

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project


class AvailabilityWidget(QtWidgets.QWidget):
    def __init__(self, project: Project, parent: QtWidgets.QWidget) -> None:
        super().__init__()

        self.edit_parent = parent

        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            "Set availability for residents here. A partial check (dash) indicates that they're available, but at the VA on a day where we should try to limit them being oncall (if the relevant VA coverage constraints and/or objectives are used)."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        table = AvailabilityTableWidget(project)
        layout.addWidget(table)

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.edit_parent.setEnabled(True)


class AvailabilityTableWidget(QtWidgets.QTableWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()

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
        for resident_index, resident in enumerate(project.availability):
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
